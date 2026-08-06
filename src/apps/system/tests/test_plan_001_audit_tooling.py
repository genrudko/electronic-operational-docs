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
    render_report,
    scan_for_secret_leaks,
    verify_manifest,
)
from apps.system.plan_001_audit.source_evidence import (
    ABSENT,
    CHAT0_INTEGRATION_DECISION,
    DOMAIN_OWNERSHIP,
    NOT_APPLICABLE,
    PRESENT,
    UNKNOWN,
    build_evidence_matrix,
    classify_runtime_data,
    domain_hits,
)
from tests.credential_fixtures import ephemeral_credential


def _commands() -> dict[str, dict[str, object]]:
    return {
        "django_tests": {
            "timed_out": False,
            "returncode": 0,
            "executed_test_count": 502,
            "output": "Ran 502 tests in 1.0s\nOK",
        }
    }


def _python_rows() -> dict[str, list[dict[str, object]]]:
    return {
        "views": [
            {"path": "src/apps/operational_documents/views.py"},
            {"path": "src/apps/operational_log/views.py"},
        ],
        "forms": [
            {"path": "src/apps/operational_documents/forms.py"},
            {"path": "src/apps/operational_log/forms.py"},
        ],
        "services": [
            {"path": "src/apps/operational_documents/services.py"},
            {"path": "src/apps/operational_log/services.py"},
        ],
        "management_commands": [
            {
                "path": (
                    "src/apps/operational_log/management/commands/"
                    "seed_demo_operational_log.py"
                )
            }
        ],
        "tests": [
            {
                "path": (
                    "src/apps/operational_documents/tests/"
                    "test_operational_document_core.py"
                ),
                "test_method_count": 11,
            },
            {
                "path": "src/apps/operational_log/tests/test_views.py",
                "test_method_count": 12,
            },
        ],
        "other_python": [
            {"path": ".github/workflows/auto-001b-controller-ci.yml"},
            {"path": "scripts/automation/auto_001b_request.py"},
        ],
    }


def _assets() -> dict[str, list[dict[str, object]]]:
    return {
        "templates": [
            {
                "path": (
                    "src/apps/operational_documents/templates/"
                    "operational_documents/registry.html"
                )
            },
            {
                "path": (
                    "src/apps/operational_log/templates/"
                    "operational_log/detail.html"
                )
            },
        ],
        "javascript": [],
        "stylesheets": [],
        "fixtures": [],
        "presentation_candidates": [],
    }


def _models() -> list[dict[str, object]]:
    return [
        {
            "label": "operational_documents.operationaldocumentrecord",
            "app_label": "operational_documents",
            "row_count": 2,
        },
        {
            "label": "operational_log.operationallogentry",
            "app_label": "operational_log",
            "row_count": 5,
        },
    ]


def _routes() -> list[dict[str, object]]:
    return [
        {
            "route": "operations/documents/",
            "namespace": "operational_documents",
            "qualified_name": "operational_documents:registry",
            "callback": "apps.operational_documents.views.registry",
        },
        {
            "route": "operations/journal/",
            "namespace": "operational_log",
            "qualified_name": "operational_log:registry",
            "callback": "apps.operational_log.views.registry",
        },
    ]


def _runtime_forms() -> list[dict[str, object]]:
    return [
        {
            "code": "journal-equipment-defects",
            "name": "Журнал дефектов оборудования",
            "catalog_present": True,
            "installed_type_count": 0,
            "published_revision_count": 0,
            "published_type_count": 0,
            "record_count": 0,
        },
        {
            "code": "journal-outage-requests",
            "name": "Журнал заявок",
            "catalog_present": True,
            "installed_type_count": 0,
            "published_revision_count": 0,
            "published_type_count": 0,
            "record_count": 0,
        },
        {
            "code": "journal-orders",
            "name": "Журнал распоряжений",
            "catalog_present": True,
            "installed_type_count": 0,
            "published_revision_count": 0,
            "published_type_count": 0,
            "record_count": 0,
        },
        {
            "code": "journal-equipment-commissioning",
            "name": "Журнал ввода оборудования",
            "catalog_present": True,
            "installed_type_count": 0,
            "published_revision_count": 0,
            "published_type_count": 0,
            "record_count": 0,
        },
        {
            "code": "journal-rza-telemechanics",
            "name": "Журнал РЗА",
            "catalog_present": True,
            "installed_type_count": 0,
            "published_revision_count": 0,
            "published_type_count": 0,
            "record_count": 0,
        },
    ]


def _matrix() -> list[dict[str, object]]:
    references = {
        "journal-equipment-defects": [
            {
                "path": (
                    "src/apps/operational_documents/tests/"
                    "test_operational_document_core.py"
                ),
                "line": 10,
                "excerpt": 'code="journal-equipment-defects"',
                "is_test": True,
            }
        ]
    }
    return build_evidence_matrix(
        model_rows=_models(),
        migration_rows={"disk": [], "pending": []},
        route_rows=_routes(),
        python_rows=_python_rows(),
        assets=_assets(),
        commands=_commands(),
        smoke=[],
        hits={area: [] for area in DOMAIN_OWNERSHIP},
        source_bound_runtime=_runtime_forms(),
        source_bound_references=references,
    )


class Plan001AuditToolingTests(SimpleTestCase):
    def test_full_suite_command_uses_accepted_apps_label(self) -> None:
        self.assertEqual(
            FULL_TEST_COMMAND[-3:],
            ("apps", "--verbosity", "2"),
        )
        self.assertEqual(executed_tests("Ran 502 tests in 2.3s"), 502)
        self.assertIsNone(executed_tests("no Django test summary"))

    def test_sanitisation_redacts_values_keys_and_uri_credentials(self) -> None:
        secret = ephemeral_credential("PlanAuditSanitize")
        scheme = "postgresql"
        dsn = f"{scheme}://user:{secret}@db/eod"
        rendered = sanitize_text(
            "\n".join((f"POSTGRES_PASSWORD={secret}", dsn)),
            (secret,),
        )
        self.assertNotIn(secret, rendered)
        self.assertIn("POSTGRES_PASSWORD=<redacted>", rendered)
        expected_dsn = f"{scheme}://user:<redacted>@db/eod"
        self.assertIn(expected_dsn, rendered)
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
        secret = ephemeral_credential("PlanAuditLeak")
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            report = root / "REPORT.md"
            report.write_text("safe\n", encoding="utf-8")
            scan_for_secret_leaks(root, (secret,))
            report.write_text(secret, encoding="utf-8")
            with self.assertRaisesRegex(
                RuntimeError,
                "secret-like marker leaked",
            ):
                scan_for_secret_leaks(root, (secret,))

    def test_explicit_ownership_maps_core_and_operational_log(self) -> None:
        rows = {row["area"]: row for row in _matrix()}
        structured = rows["structured_journal_core"]
        operational = rows["operational_journal"]
        for component in ("models", "services", "routes", "tests"):
            self.assertEqual(
                structured["component_states"][component]["status"],
                PRESENT,
            )
            self.assertEqual(
                operational["component_states"][component]["status"],
                PRESENT,
            )
        self.assertIn(
            "operational_documents.operationaldocumentrecord",
            structured["models"],
        )
        self.assertIn(
            "operational_log.operationallogentry",
            operational["models"],
        )

    def test_auto001_paths_do_not_create_false_journal_readiness(self) -> None:
        rows = {row["area"]: row for row in _matrix()}
        for area in (
            "application_journal",
            "disposition_journal",
            "work_permit",
            "switching_documents",
        ):
            row = rows[area]
            self.assertNotEqual(
                row["component_states"]["services"]["status"],
                PRESENT,
            )
            self.assertNotEqual(
                row["component_states"]["routes"]["status"],
                PRESENT,
            )
        self.assertEqual(
            rows["work_permit"]["component_states"]["models"]["status"],
            ABSENT,
        )
        self.assertEqual(
            rows["switching_documents"]["component_states"]["tests"]["status"],
            ABSENT,
        )

    def test_catalog_presence_does_not_replace_published_type(self) -> None:
        defect = {
            row["area"]: row for row in _matrix()
        }["defect_journal"]
        self.assertEqual(defect["source_catalog_state"], PRESENT)
        self.assertEqual(defect["published_type_state"], ABSENT)
        self.assertEqual(defect["records_state"], ABSENT)
        self.assertEqual(
            defect["component_states"]["models"]["status"],
            NOT_APPLICABLE,
        )
        self.assertEqual(
            defect["component_states"]["tests"]["status"],
            PRESENT,
        )

    def test_absent_unknown_and_not_applicable_are_distinct(self) -> None:
        statuses = {
            payload["status"]
            for row in _matrix()
            for payload in row["component_states"].values()
        }
        self.assertIn(ABSENT, statuses)
        self.assertIn(UNKNOWN, statuses)
        self.assertIn(NOT_APPLICABLE, statuses)

    def test_runtime_data_keeps_staging_and_unknown_separate(self) -> None:
        model_rows = [
            {
                "label": "imports.powersystemassetoccurrence",
                "app_label": "imports",
                "row_count": 2500,
            },
            {
                "label": "equipment.equipmentasset",
                "app_label": "equipment",
                "row_count": 9,
            },
            {
                "label": "equipment.equipmentauditevent",
                "app_label": "equipment",
                "row_count": 19,
            },
        ]
        result = classify_runtime_data(
            model_rows,
            {
                "presentation_candidates": [
                    {
                        "path": (
                            "src/apps/equipment/management/commands/"
                            "seed_demo_equipment.py"
                        )
                    }
                ]
            },
            _runtime_forms(),
        )
        categories = result["categories"]
        self.assertEqual(categories["staging/import"]["row_count"], 2500)
        self.assertEqual(categories["unknown"]["row_count"], 9)
        self.assertEqual(categories["system/internal"]["row_count"], 19)
        self.assertEqual(categories["presentation/demo"]["status"], UNKNOWN)
        self.assertNotEqual(
            categories["staging/import"]["status"],
            categories["canonical"]["status"],
        )

    def test_discovery_hits_exclude_auto001_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            workflow = root / ".github/workflows/auto.yml"
            workflow.parent.mkdir(parents=True)
            workflow.write_text(
                "application order switch work permit\n",
                encoding="utf-8",
            )
            source = root / "src/apps/operational_log/example.py"
            source.parent.mkdir(parents=True)
            source.write_text("operational_log\n", encoding="utf-8")
            hits = domain_hits(root)
        self.assertFalse(
            any(
                item["path"].startswith(".github/")
                for rows in hits.values()
                for item in rows
            )
        )
        self.assertTrue(hits["operational_journal"])

    def test_report_marks_chat0_decision_as_manual(self) -> None:
        data = {
            "project": {
                "pr_number": 7,
                "head_sha": "b" * 40,
                "trusted_main_head": "c" * 40,
                "accepted_application_baseline": "d" * 40,
                "generated_at": "2026-07-26T00:00:00+00:00",
                "python_version": "3.13",
                "django_version": "5.2",
            },
            "database": {"current_database": "eod_development"},
            "commands": _commands(),
            "apps": [],
            "models": [],
            "migrations": {"pending": []},
            "routes": [],
            "python": {"views": [], "forms": [], "services": []},
            "fixtures": {"total_objects": 0},
            "integration_decision": CHAT0_INTEGRATION_DECISION,
            "runtime_data_classification": {
                "categories": {
                    name: {
                        "status": UNKNOWN,
                        "row_count": None,
                        "note": "test",
                    }
                    for name in (
                        "canonical",
                        "staging/import",
                        "presentation/demo",
                        "system/internal",
                        "unknown",
                    )
                }
            },
            "evidence_matrix": _matrix(),
            "source_bound_forms": _runtime_forms(),
            "documentation": {
                "missing_mandatory_files": [],
                "stale_auto001_claim_files": [],
                "plan001_acceptance_files": [],
            },
        }
        report = render_report(data)
        self.assertIn("Ручное решение интеграционного Чата 0", report)
        self.assertIn("не machine verdict", report)
        self.assertIn("DEFECT JOURNAL", report)
        self.assertIn("merge authorization: ABSENT", report)
