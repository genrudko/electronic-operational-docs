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
        self.assertNotIn("m4 5 3 3", grounding)

    def test_organization_and_division_are_visually_distinct(self) -> None:
        organization = self.symbol("icon-organization")
        division = self.symbol("icon-org-division")

        self.assertNotEqual(organization, division)
        self.assertIn("M4 21V7l8-4", organization)
        self.assertIn('<rect x="9" y="3" width="6" height="5"', division)

    def test_process_icons_have_explicit_domain_semantics(self) -> None:
        schemes = self.symbol("icon-module-schemes")
        shift = self.symbol("icon-shift-handover")
        current_works = self.symbol("icon-current-works")
        emergency = self.symbol("icon-emergency-readiness")
        battery_inspection = self.symbol("icon-battery-inspection")

        self.assertIn('<rect x="10" y="9" width="4" height="4"', schemes)
        self.assertIn('<circle cx="5" cy="6" r="2.5"', shift)
        self.assertIn('<circle cx="19" cy="6" r="2.5"', shift)
        self.assertIn("M8 12h8", shift)
        self.assertIn("M10 9.5 7.5 12 10 14.5", shift)
        self.assertIn("M14 9.5l2.5 2.5-2.5 2.5", shift)
        self.assertNotIn("M8 11h8", shift)
        self.assertIn('<circle cx="18" cy="18" r="4"', current_works)
        self.assertIn("M6 15v-4a6 6", emergency)
        self.assertIn('<circle cx="18" cy="18" r="3"', battery_inspection)

    def test_equipment_icons_use_gost_derived_shapes(self) -> None:
        transformer = self.symbol("icon-equipment-transformer")
        busbar = self.symbol("icon-equipment-busbar")
        breaker = self.symbol("icon-equipment-breaker")
        disconnector = self.symbol("icon-equipment-disconnector")
        ground_switch = self.symbol("icon-equipment-ground-switch")
        portable_ground = self.symbol("icon-equipment-portable-ground")
        battery = self.symbol("icon-equipment-battery")

        self.assertIn('<circle cx="9" cy="12" r="5"', transformer)
        self.assertIn('<circle cx="15" cy="12" r="5"', transformer)
        self.assertIn('stroke-width="4"', busbar)

        self.assertIn("M12 2v20", breaker)
        self.assertIn('<rect x="9" y="7" width="6" height="10"', breaker)
        self.assertNotIn("M9.5 10h5", breaker)

        self.assertIn("M8 12l7-6", disconnector)

        self.assertIn('<circle cx="12" cy="7" r="1"', ground_switch)
        self.assertIn('<circle cx="18" cy="12" r="1"', ground_switch)
        self.assertIn("M12 7l5 4", ground_switch)
        self.assertIn("M13 16h10M15 19h6M17 22h2", ground_switch)

        self.assertEqual(portable_ground.count("<rect "), 3)
        self.assertIn("M5 6c0 5 4 5 7 8", portable_ground)
        self.assertIn("M19 6c0 5-4 5-7 8", portable_ground)
        self.assertIn("M7 16h10M9 19h6M11 22h2", portable_ground)
        self.assertNotIn("m3 2 3 3", portable_ground)

        self.assertIn("M7 9v6M4 12h6M14 10v4", battery)

    def test_gost_boundary_is_documented_without_false_compliance_claim(self) -> None:
        contract = (
            self.project_root
            / "docs/ux/EQUIPMENT_PICTOGRAM_GOST_BASIS_V1.md"
        ).read_text(encoding="utf-8")

        self.assertIn("ГОСТ Р 56303-2014", contract)
        self.assertIn("Изменением № 1", contract)
        self.assertIn("не заменяют инженерное УГО", contract)
        self.assertIn("не объявляется самостоятельным УГО", contract)
        self.assertIn("две фигуры сотрудников", contract)
        self.assertIn("три фазных зажима", contract)
