from django.test import SimpleTestCase

from apps.imports.master_data_contract import (
    DC_DISTRIBUTION_FAMILY_CODE,
    MasterDataTarget,
    ReviewDisposition,
    normalize_aliases,
    validate_profile_row,
)


class MasterDataContractTests(SimpleTestCase):
    def test_organization_structure_is_separate_from_personnel(self):
        result = validate_profile_row(
            MasterDataTarget.ORGANIZATION_STRUCTURE,
            {
                "organization_code": "ORG",
                "organization_name": "Организация",
                "division_code": "OPS",
                "division_name": "Оперативная служба",
                "workplace_code": "SHIFT",
                "workplace_name": "Сменный персонал",
                "site_code": "WPP",
                "site_name": "Демонстрационная ВЭС",
            },
        )
        self.assertEqual(result.disposition, ReviewDisposition.READY)
        self.assertNotIn("personnel_number", result.normalized)

    def test_incomplete_structure_pair_is_blocked(self):
        result = validate_profile_row(
            MasterDataTarget.ORGANIZATION_STRUCTURE,
            {
                "organization_code": "ORG",
                "organization_name": "Организация",
                "division_code": "OPS",
            },
        )
        self.assertEqual(result.disposition, ReviewDisposition.BLOCKED)
        self.assertIn(
            "DIVISION_PAIR_INCOMPLETE",
            {issue.code for issue in result.issues},
        )

    def test_shot_and_shpt_share_one_technical_family(self):
        shot = validate_profile_row(
            MasterDataTarget.EQUIPMENT,
            {
                "code": "SHOT-1",
                "technical_name": "Шкаф оперативного тока",
                "type": "Щит постоянного тока",
                "site": "ВЭС",
                "source_designation": "ШОТ",
                "source_occurrence_id": "row-1",
            },
        )
        shpt = validate_profile_row(
            MasterDataTarget.EQUIPMENT,
            {
                "code": "SHPT-1",
                "technical_name": "Щит постоянного тока",
                "type": "Щит постоянного тока",
                "site": "ПС",
                "source_designation": "ЩПТ",
                "source_occurrence_id": "row-2",
            },
        )
        self.assertEqual(shot.disposition, ReviewDisposition.READY)
        self.assertEqual(shpt.disposition, ReviewDisposition.READY)
        self.assertEqual(shot.normalized["family_code"], DC_DISTRIBUTION_FAMILY_CODE)
        self.assertEqual(shpt.normalized["family_code"], DC_DISTRIBUTION_FAMILY_CODE)
        self.assertEqual(shot.normalized["source_designation"], "ШОТ")
        self.assertEqual(shpt.normalized["source_designation"], "ЩПТ")

    def test_conflicting_explicit_family_is_blocked(self):
        result = validate_profile_row(
            MasterDataTarget.EQUIPMENT,
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
        self.assertEqual(result.disposition, ReviewDisposition.BLOCKED)
        self.assertIn(
            "EQUIPMENT_FAMILY_CONFLICT",
            {issue.code for issue in result.issues},
        )

    def test_missing_source_occurrence_requires_review_not_publication(self):
        result = validate_profile_row(
            MasterDataTarget.EQUIPMENT,
            {
                "code": "EQ-1",
                "technical_name": "Оборудование",
                "type": "Другое",
                "site": "ВЭС",
            },
        )
        self.assertEqual(result.disposition, ReviewDisposition.REVIEW)
        self.assertIn(
            "SOURCE_OCCURRENCE_MISSING",
            {issue.code for issue in result.issues},
        )

    def test_aliases_are_stable_and_case_insensitive_unique(self):
        self.assertEqual(
            normalize_aliases("КТП-1; ктп-1 | KTP-1\nКТП 1"),
            ("КТП-1", "KTP-1", "КТП 1"),
        )

    def test_information_only_management_is_blocked(self):
        result = validate_profile_row(
            MasterDataTarget.DISPATCHING,
            {
                "equipment_code": "EQ-1",
                "relation_kind": "MANAGEMENT",
                "subject": "Оперативный персонал",
                "level": "Станционный уровень",
                "information_only": "да",
            },
        )
        self.assertEqual(result.disposition, ReviewDisposition.BLOCKED)
        self.assertIn(
            "INFORMATION_ONLY_MANAGEMENT_FORBIDDEN",
            {issue.code for issue in result.issues},
        )

    def test_information_only_supervision_is_valid(self):
        result = validate_profile_row(
            MasterDataTarget.DISPATCHING,
            {
                "equipment_code": "EQ-1",
                "relation_kind": "SUPERVISION",
                "subject": "Оперативный персонал",
                "level": "Станционный уровень",
                "information_only": "да",
            },
        )
        self.assertEqual(result.disposition, ReviewDisposition.READY)
