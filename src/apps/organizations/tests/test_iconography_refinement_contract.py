from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class IconographyRefinementContractTests(SimpleTestCase):
    def setUp(self) -> None:
        self.source_root = Path(settings.BASE_DIR) / "src"
        self.project_root = Path(settings.BASE_DIR)
        self.sprite = (
            self.source_root / "static/system/icons.svg"
        ).read_text(encoding="utf-8")

    def symbol(self, symbol_id: str) -> str:
        marker = f'<symbol id="{symbol_id}"'
        self.assertIn(marker, self.sprite)
        return self.sprite.split(marker, maxsplit=1)[1].split(
            "</symbol>", maxsplit=1
        )[0]

    def test_sprite_keeps_complete_canonical_catalogue(self) -> None:
        self.assertEqual(self.sprite.count("<symbol "), 66)
        self.assertIn("GOST R 56303-2014-derived", self.sprite)

    def test_rejected_metaphors_are_removed(self) -> None:
        work_permit = self.symbol("icon-module-work-permits")
        leadership = self.symbol("icon-org-leadership")
        rza = self.symbol("icon-org-rza")
        grounding = self.symbol("icon-grounding")

        self.assertIn('<circle cx="16" cy="16" r="4"', work_permit)
        self.assertNotIn("M2 18a2 2", work_permit)
        self.assertIn('<circle cx="12" cy="6" r="3"', leadership)
        self.assertNotIn("L15.39", leadership)
        self.assertIn('<rect x="4" y="3" width="16"', rza)
        self.assertNotIn("M22 12h-2.48", rza)
        self.assertIn("M12 3v9M4 12h16M7 16h10M10 20h4", grounding)

    def test_organization_and_division_are_visually_distinct(self) -> None:
        organization = self.symbol("icon-organization")
        division = self.symbol("icon-org-division")
        self.assertNotEqual(organization, division)
        self.assertIn("M4 21V7l8-4", organization)
        self.assertIn('<rect x="9" y="3" width="6" height="5"', division)

    def test_process_icons_have_explicit_domain_semantics(self) -> None:
        shift = self.symbol("icon-shift-handover")
        self.assertIn('<circle cx="5" cy="6" r="2.5"', shift)
        self.assertIn('<circle cx="19" cy="6" r="2.5"', shift)
        self.assertIn("M8 12h8", shift)
        self.assertIn("M10 9.5 7.5 12 10 14.5", shift)
        self.assertIn("M14 9.5l2.5 2.5-2.5 2.5", shift)

    def test_equipment_icons_use_gost_derived_shapes(self) -> None:
        breaker = self.symbol("icon-equipment-breaker")
        ground_switch = self.symbol("icon-equipment-ground-switch")
        portable_ground = self.symbol("icon-equipment-portable-ground")

        self.assertIn("M12 2v6M12 16v6", breaker)
        self.assertIn('<rect x="8" y="8" width="8" height="8"', breaker)
        self.assertNotIn("M12 2v20", breaker)
        self.assertNotIn('width="6" height="10"', breaker)

        self.assertIn("M12 2v5M9 8h6", ground_switch)
        self.assertIn("M12 15 9.5 10.5", ground_switch)
        self.assertIn('<circle cx="12" cy="15" r="1"', ground_switch)
        self.assertIn("M12 16v1M7 17h10M9 20h6M11 23h2", ground_switch)
        self.assertNotIn("M12 7l5 4", ground_switch)

        self.assertEqual(portable_ground.count("<rect "), 3)
        self.assertIn("M5 6c0 5 4 5 7 8", portable_ground)
        self.assertIn("M19 6c0 5-4 5-7 8", portable_ground)
        self.assertIn("M7 16h10M9 19h6M11 22h2", portable_ground)

    def test_gost_boundary_is_documented_without_false_compliance_claim(self) -> None:
        contract_path = (
            self.project_root
            / "docs/ux/EQUIPMENT_PICTOGRAM_GOST_BASIS_V1.md"
        )
        if not contract_path.exists():
            self.skipTest(
                "repository-only UX contract is not packaged in runtime images"
            )
        contract = contract_path.read_text(encoding="utf-8")
        self.assertIn("ГОСТ Р 56303-2014", contract)
        self.assertIn("Изменением № 1", contract)
        self.assertIn("не заменяют инженерное УГО", contract)
        self.assertIn("квадрат", contract)
        self.assertIn("отключённый заземляющий разъединитель", contract)
