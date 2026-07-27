from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class EquipmentDefectRepairFourUITests(SimpleTestCase):
    def test_desktop_registry_is_fitted_without_horizontal_table_floor(self) -> None:
        script_path = (
            Path(settings.BASE_DIR)
            / "src"
            / "static"
            / "equipment_defects"
            / "defects.js"
        )
        script = script_path.read_text(encoding="utf-8")

        self.assertIn("function initDesktopRegistryFit()", script)
        self.assertIn('register.style.width = "100%";', script)
        self.assertIn('register.style.minWidth = "0";', script)
        self.assertIn('cell.style.overflowWrap = "anywhere";', script)
        self.assertIn("initDesktopRegistryFit();", script)

    def test_stale_field_error_is_removed_after_operator_starts_correction(self) -> None:
        script_path = (
            Path(settings.BASE_DIR)
            / "src"
            / "static"
            / "equipment_defects"
            / "defects.js"
        )
        script = script_path.read_text(encoding="utf-8")

        self.assertIn("function initInlineErrorClearing()", script)
        self.assertIn("errors.forEach((error) => error.remove());", script)
        self.assertIn(
            'control.addEventListener("input", clear, { once: true });',
            script,
        )
        self.assertIn(
            'control.addEventListener("change", clear, { once: true });',
            script,
        )
        self.assertIn("initInlineErrorClearing();", script)
