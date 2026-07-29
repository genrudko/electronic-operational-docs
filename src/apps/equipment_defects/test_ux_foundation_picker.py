from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EquipmentDefectCustomPickerContractTests(SimpleTestCase):
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

    def test_form_templates_load_custom_picker_after_repair_three(self) -> None:
        for filename in ("registration_form.html", "action_form.html"):
            with self.subTest(template=filename):
                template = (self.template_root / filename).read_text(encoding="utf-8")
                repair_three_css = "equipment_defects/ux_foundation_repair3.css"
                picker_css = "equipment_defects/ux_foundation_repair3_picker.css"
                repair_three_js = "equipment_defects/ux_foundation_repair3.js"
                picker_js = "equipment_defects/ux_foundation_repair3_picker.js"
                for marker in (
                    repair_three_css,
                    picker_css,
                    repair_three_js,
                    picker_js,
                    "?v=uxf001r31",
                ):
                    self.assertIn(marker, template)
                self.assertLess(template.index(repair_three_css), template.index(picker_css))
                self.assertLess(template.index(repair_three_js), template.index(picker_js))

    def test_picker_keeps_manual_input_and_adds_calendar_and_time_wheels(self) -> None:
        script = (self.static_root / "ux_foundation_repair3_picker.js").read_text(
            encoding="utf-8"
        )
        required = (
            ".defect-manual-date",
            ".defect-manual-time",
            "Открыть календарь",
            "Открыть выбор времени",
            "Выберите дату",
            "Выберите время",
            "defect-calendar-grid",
            "defect-time-wheel",
            "Часы",
            "Минуты",
            "Europe/Moscow",
            "data-defect-time-trust",
            'input.dispatchEvent(new Event("input", { bubbles: true }))',
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_picker_is_a_light_mobile_bottom_sheet(self) -> None:
        stylesheet = (
            self.static_root / "ux_foundation_repair3_picker.css"
        ).read_text(encoding="utf-8")
        required = (
            ".defect-picker-trigger",
            ".defect-picker-backdrop",
            ".defect-picker-panel",
            ".defect-calendar-day.is-selected",
            ".defect-time-option.is-selected",
            "@media (max-width: 620px)",
            "place-items: end stretch",
            "border-radius: 16px 16px 0 0",
            "env(safe-area-inset-bottom)",
        )
        for marker in required:
            with self.subTest(marker=marker):
                self.assertIn(marker, stylesheet)
