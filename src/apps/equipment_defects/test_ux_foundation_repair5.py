from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EquipmentDefectUXFoundationRepairFiveTests(SimpleTestCase):
    def setUp(self) -> None:
        self.template_root = (
            Path(settings.BASE_DIR)
            / "src"
            / "templates"
            / "equipment_defects"
        )
        self.static_root = (
            Path(settings.BASE_DIR)
            / "src"
            / "static"
            / "equipment_defects"
        )

    def test_repair_five_asset_is_loaded_after_repair_four(self) -> None:
        for filename in (
            "registry.html",
            "detail.html",
            "registration_form.html",
            "action_form.html",
        ):
            with self.subTest(template=filename):
                template = (self.template_root / filename).read_text(encoding="utf-8")
                repair_four = "equipment_defects/ux_foundation_repair4.css"
                repair_five = "equipment_defects/ux_foundation_repair5.css"
                self.assertIn(repair_four, template)
                self.assertIn(repair_five, template)
                self.assertIn("?v=uxf001r5", template)
                self.assertLess(template.index(repair_four), template.index(repair_five))

    def test_registry_statuses_follow_reference_pill_contract(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair5.css").read_text(
            encoding="utf-8"
        )
        required = (
            ".defect-da-status::before",
            'content: ""',
            "background: currentColor",
            "border-radius: 999px",
            "text-transform: none",
            "white-space: nowrap",
            '--da-status-registered-soft: #e7f2fb',
            '--da-status-progress-soft: #fff0df',
            '--da-status-resolved-soft: #e5f4ea',
            '--da-status-closed-soft: #edf1f4',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)

    def test_lifecycle_has_separate_completed_current_and_future_semantics(self) -> None:
        stylesheet = (self.static_root / "ux_foundation_repair5.css").read_text(
            encoding="utf-8"
        )
        required = (
            "completed = neutral card + teal check",
            "current = semantic status colour",
            "future = quiet neutral placeholder",
            '--da-lifecycle-complete: #317c7a',
            'data-current-status="REGISTERED"',
            'data-current-status="IN_PROGRESS"',
            'data-current-status="RESOLVED"',
            'data-current-status="CLOSED"',
            'content: "✓"',
            "--da-status-closed: #465568",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)
