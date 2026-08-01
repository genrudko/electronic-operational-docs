from types import SimpleNamespace

from django.test import SimpleTestCase

from apps.imports import services
from apps.imports.master_data_runtime import (
    install_master_data_contracts,
    installation_state,
)
from apps.imports.models import ImportBatch, ImportRow


class MasterDataRuntimeIntegrationTests(SimpleTestCase):
    def test_installation_is_idempotent_and_extends_equipment_fields(self):
        before = installation_state()
        install_master_data_contracts()
        after = installation_state()

        self.assertTrue(before["installed"])
        self.assertEqual(before, after)
        self.assertIn("family_code", after["equipment_fields"])
        self.assertIn("source_designation", after["equipment_fields"])
        self.assertIn("parent_code", after["equipment_fields"])
        self.assertIn("aliases", after["equipment_fields"])
        self.assertIn("source_occurrence_id", after["equipment_fields"])
        self.assertEqual(
            after["equipment_fields"].count("source_occurrence_id"),
            1,
        )

    def test_equipment_validation_normalizes_family_designation_and_aliases(self):
        normalized, issues = services.validate_mapped_values(
            ImportBatch.TargetRegistry.EQUIPMENT,
            {
                "code": "shot-1",
                "technical_name": "Шкаф оперативного тока",
                "type": "Щит постоянного тока",
                "site": "ВЭС",
                "source_designation": "шот",
                "aliases": "ШОТ-1; шот-1 | DC cabinet",
                "source_occurrence_id": "row-1",
            },
        )

        self.assertEqual(normalized["code"], "SHOT-1")
        self.assertEqual(normalized["source_designation"], "ШОТ")
        self.assertEqual(normalized["family_code"], "dc_distribution_board")
        self.assertEqual(normalized["aliases"], "ШОТ-1; DC cabinet")
        self.assertEqual(issues, [])

    def test_missing_equipment_provenance_is_review_not_invalid(self):
        _normalized, issues = services.validate_mapped_values(
            ImportBatch.TargetRegistry.EQUIPMENT,
            {
                "code": "EQ-1",
                "technical_name": "Оборудование",
                "type": "Другое",
                "site": "ВЭС",
            },
        )
        row = SimpleNamespace(status=ImportRow.Status.NEW, issues=[])

        self.assertEqual(len(issues), 1)
        self.assertTrue(issues[0].startswith("[MASTER_DATA_REVIEW:"))
        self.assertEqual(
            services._review_status(row, issues, []),
            ImportRow.ReviewStatus.REVIEW,
        )

    def test_conflicting_shot_family_is_invalid(self):
        _normalized, issues = services.validate_mapped_values(
            ImportBatch.TargetRegistry.EQUIPMENT,
            {
                "code": "SHOT-1",
                "technical_name": "Шкаф оперативного тока",
                "type": "Шкаф",
                "site": "ВЭС",
                "source_designation": "ШОТ",
                "family_code": "other_family",
                "source_occurrence_id": "row-1",
            },
        )
        row = SimpleNamespace(status=ImportRow.Status.NEW, issues=[])

        self.assertTrue(
            any(issue.startswith("[MASTER_DATA_BLOCKED:") for issue in issues)
        )
        self.assertEqual(
            services._review_status(row, issues, []),
            ImportRow.ReviewStatus.INVALID,
        )

    def test_information_only_supervision_remains_valid(self):
        normalized, issues = services.validate_mapped_values(
            ImportBatch.TargetRegistry.DISPATCHING,
            {
                "equipment_code": "EQ-1",
                "relation_kind": "SUPERVISION",
                "subject": "Субъект",
                "level": "Уровень",
                "information_only": "Да",
            },
        )

        self.assertEqual(normalized["relation_kind"], "SUPERVISION")
        self.assertEqual(normalized["information_only"], "да")
        self.assertEqual(issues, [])

    def test_information_only_management_is_invalid(self):
        _normalized, issues = services.validate_mapped_values(
            ImportBatch.TargetRegistry.DISPATCHING,
            {
                "equipment_code": "EQ-1",
                "relation_kind": "MANAGEMENT",
                "subject": "Субъект",
                "level": "Уровень",
                "information_only": "Да",
            },
        )
        row = SimpleNamespace(status=ImportRow.Status.NEW, issues=[])

        self.assertTrue(
            any(
                "INFORMATION_ONLY_MANAGEMENT_FORBIDDEN" in issue
                for issue in issues
            )
        )
        self.assertEqual(
            services._review_status(row, issues, []),
            ImportRow.ReviewStatus.INVALID,
        )
