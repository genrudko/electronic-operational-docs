from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts import backup_restore_drill as drill


class BackupRestoreDrillNegativeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def test_missing_backup_fails_closed(self) -> None:
        with self.assertRaises(drill.DrillError):
            drill.require_nonempty_backup(self.root / "missing.dump")

    def test_empty_backup_fails_closed(self) -> None:
        path = self.root / "empty.dump"
        path.write_bytes(b"")
        with self.assertRaises(drill.DrillError):
            drill.require_nonempty_backup(path)

    def test_truncated_or_unreadable_backup_fails_pg_restore_list(self) -> None:
        path = self.root / "truncated.dump"
        path.write_bytes(b"not-a-postgresql-custom-dump")
        with mock.patch.object(drill, "_run", side_effect=drill.DrillError("pg_restore list failed")):
            with self.assertRaises(drill.DrillError):
                drill.assert_pg_restore_readable(path)

    def test_checksum_mismatch_fails_closed(self) -> None:
        path = self.root / "backup.dump"
        path.write_bytes(b"payload")
        with self.assertRaises(drill.DrillError):
            drill.verify_backup_checksum(path, "0" * 64)

    def test_wrong_target_identity_fails_closed(self) -> None:
        with self.assertRaises(drill.DrillError):
            drill.validate_target_identity(
                source_database="eod_dr_source",
                target_database="some_other_database",
                target_class=drill.DISPOSABLE_TARGET_CLASS,
                sentinel=drill.DISPOSABLE_SENTINEL,
            )

    def test_ambiguous_target_identity_fails_closed(self) -> None:
        with self.assertRaises(drill.DrillError):
            drill.validate_target_identity(
                source_database="eod_dr_source",
                target_database="",
                target_class=drill.DISPOSABLE_TARGET_CLASS,
                sentinel=drill.DISPOSABLE_SENTINEL,
            )

    def test_live_or_non_disposable_target_fails_closed(self) -> None:
        for target in ("eod", "eod_preview", "eod_development", "postgres"):
            with self.subTest(target=target), self.assertRaises(drill.DrillError):
                drill.validate_target_identity(
                    source_database="eod_dr_source",
                    target_database=target,
                    target_class=drill.DISPOSABLE_TARGET_CLASS,
                    sentinel=drill.DISPOSABLE_SENTINEL,
                )

    def test_pg_restore_failure_fails_closed(self) -> None:
        path = self.root / "backup.dump"
        path.write_bytes(b"non-empty")
        with mock.patch.object(drill, "_run", side_effect=drill.DrillError("pg_restore failed")):
            with self.assertRaises(drill.DrillError):
                drill.restore_backup(path, "eod_restore_drill_123")

    def test_representative_count_loss_fails_closed(self) -> None:
        before = {label: 1 for label in drill.REPRESENTATIVE_MODELS}
        after = dict(before)
        after[drill.REPRESENTATIVE_MODELS[-1]] = 0
        with self.assertRaises(drill.DrillError):
            drill.validate_representative_counts(before, after)

    def test_post_restore_system_check_failure_cannot_be_certified(self) -> None:
        payload = self._passing_certificate()
        payload["verification"]["system_check"] = "FAIL"
        with self.assertRaises(drill.DrillError):
            drill.validate_certificate_payload(payload)

    def test_secret_or_raw_dump_material_cannot_be_certified(self) -> None:
        for mutation in (
            lambda payload: payload.update({"raw_dump": "PGDMP..."}),
            lambda payload: payload["recovery_point"].update(
                {"note": "postgresql://user:password@host/db"}
            ),
        ):
            payload = self._passing_certificate()
            mutation(payload)
            with self.assertRaises(drill.DrillError):
                drill.validate_certificate_payload(payload)

    def test_certificate_checksum_is_recomputed(self) -> None:
        payload = self._passing_certificate()
        certificate = self.root / "restore-certificate.json"
        checksum = self.root / "restore-certificate.sha256"
        digest = drill.write_certificate(payload, certificate, checksum)
        self.assertEqual(drill.verify_certificate_files(certificate, checksum), digest)
        parsed = json.loads(certificate.read_text(encoding="utf-8"))
        parsed["overall"] = "FAIL"
        certificate.write_text(drill.canonical_json(parsed), encoding="utf-8")
        with self.assertRaises(drill.DrillError):
            drill.verify_certificate_files(certificate, checksum)

    def _passing_certificate(self) -> dict:
        counts = {label: 1 for label in drill.REPRESENTATIVE_MODELS}
        return {
            "schema": drill.CERTIFICATE_SCHEMA,
            "schema_version": drill.CERTIFICATE_VERSION,
            "work_item": drill.WORK_ITEM,
            "repository": {
                "name": "genrudko/electronic-operational-docs",
                "exact_head": "a" * 40,
            },
            "recovery_point": {
                "source_class": "ci-representative",
                "source_database_identity": "eod_dr_source",
                "representative_dataset": "DEMO-ORGANIZATION-PLUS-DR-EQUIPMENT-V1",
            },
            "backup": {
                "format": "postgresql-custom",
                "sha256": "b" * 64,
                "size_bytes": 4096,
                "pg_restore_list": "PASS",
                "checksum_verification": "PASS",
            },
            "postgresql": {
                "server": "18.4",
                "pg_dump": "pg_dump (PostgreSQL) 18.4",
                "pg_restore": "pg_restore (PostgreSQL) 18.4",
            },
            "restore_target": {
                "class": drill.DISPOSABLE_TARGET_CLASS,
                "database_identity": "eod_restore_drill_123",
                "identity_guard": "PASS",
                "clean_target": "PASS",
                "cleanup": "PASS",
            },
            "verification": {
                "restore": "PASS",
                "migrations": "PASS",
                "system_check": "PASS",
                "database_identity": "PASS",
                "readiness": "PASS",
                "counts": "PASS",
                "integrity": "PASS",
            },
            "pre_restore_counts": dict(counts),
            "post_restore_counts": dict(counts),
            "objectives": {
                "rpo_target_hours": drill.RPO_TARGET_HOURS,
                "rto_target_hours": drill.RTO_TARGET_HOURS,
                "production_rto_status": "TARGET_SLO_NOT_PROVEN_BY_CI",
            },
            "timing": {"restore_seconds": 1.0, "drill_seconds": 2.0},
            "overall": "PASS",
        }


if __name__ == "__main__":
    unittest.main()
