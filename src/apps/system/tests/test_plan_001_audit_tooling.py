from __future__ import annotations

import tempfile
from pathlib import Path

from django.test import SimpleTestCase

from apps.system.plan_001_audit.core import (
    FULL_TEST_COMMAND,
    executed_tests,
    sanitize,
    sanitize_text,
)
from apps.system.plan_001_audit.package import (
    build_manifest,
    scan_for_secret_leaks,
    verify_manifest,
)
from apps.system.plan_001_audit.source_evidence import build_evidence_matrix


class Plan001AuditToolingTests(SimpleTestCase):
    def test_full_suite_command_uses_accepted_apps_label(self) -> None:
        self.assertEqual(
            FULL_TEST_COMMAND[-3:],
            ("apps", "--verbosity", "2"),
        )
        self.assertEqual(executed_tests("Ran 501 tests in 2.3s"), 501)
        self.assertIsNone(executed_tests("no Django test summary"))

    def test_sanitisation_redacts_values_keys_and_uri_credentials(self) -> None:
        secret = "PLAN001_TEST_SECRET_123456"
        rendered = sanitize_text(
            f"POSTGRES_PASSWORD={secret}\npostgresql://user:{secret}@db/eod",
            (secret,),
        )
        self.assertNotIn(secret, rendered)
        self.assertIn("POSTGRES_PASSWORD=<redacted>", rendered)
        self.assertIn("postgresql://user:<redacted>@db/eod", rendered)
        payload = sanitize(
            {"safe": "value", "api_token": secret, "nested": [secret]},
            (secret,),
        )
        self.assertEqual(payload["api_token"], "<redacted>")
        self.assertEqual(payload["nested"], ["<redacted-secret>"])

    def test_manifest_verification_detects_tampering(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "REPORT.md"
            report.write_text("safe\n", encoding="utf-8")
            data = {
                "project": {
                    "generated_at": "2026-07-26T00:00:00+00:00",
                    "head_sha": "a" * 40,
                }
            }
            manifest = build_manifest(root, data)
            verify_manifest(root, manifest)
            report.write_text("evil\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "checksum mismatch"):
                verify_manifest(root, manifest)

    def test_secret_leak_scan_fails_closed(self) -> None:
        secret = "PLAN001_TEST_SECRET_123456"
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "REPORT.md"
            report.write_text("safe\n", encoding="utf-8")
            scan_for_secret_leaks(root, (secret,))
            report.write_text(secret, encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "secret-like marker leaked"):
                scan_for_secret_leaks(root, (secret,))

    def test_matrix_keeps_subject_acceptance_unproven(self) -> None:
        commands = {
            "django_tests": {
                "timed_out": False,
                "returncode": 0,
                "executed_test_count": 501,
            }
        }
        rows = build_evidence_matrix(
            model_rows=[],
            migration_rows={"disk": [], "pending": []},
            route_rows=[],
            python_rows={
                "views": [],
                "forms": [],
                "services": [],
                "management_commands": [],
                "tests": [],
                "other_python": [],
            },
            assets={
                "templates": [],
                "javascript": [],
                "stylesheets": [],
                "fixtures": [],
                "presentation_candidates": [],
            },
            commands=commands,
            smoke=[],
            hits={
                area: []
                for area in (
                    "structured_journal_core",
                    "operational_journal",
                    "defect_journal",
                    "application_journal",
                    "disposition_journal",
                    "equipment_commissioning",
                    "relay_automation",
                    "work_permit",
                    "keys_journal",
                    "switching_documents",
                    "equipment_registry",
                    "personnel_rights",
                )
            },
        )
        self.assertTrue(rows)
        self.assertTrue(
            all(
                row["subject_acceptance"]
                == "not established by automatic audit"
                for row in rows
            )
        )
        self.assertTrue(all(row["remaining_deficit"] for row in rows))
