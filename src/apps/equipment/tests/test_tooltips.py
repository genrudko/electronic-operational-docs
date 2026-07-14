from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class ContextHelpRepairTests(SimpleTestCase):
    def test_base_template_loads_context_help_script(self):
        source = (
            Path(settings.BASE_DIR) / "src/templates/base.html"
        ).read_text(encoding="utf-8")
        self.assertIn("system/app.js", source)
        self.assertIn("defer", source)

    def test_script_closes_other_tips_and_handles_escape(self):
        source = (
            Path(settings.BASE_DIR) / "src/static/system/app.js"
        ).read_text(encoding="utf-8")
        self.assertIn("closeOtherTips", source)
        self.assertIn('event.key === "Escape"', source)
        self.assertIn('document.addEventListener("pointerdown"', source)
        self.assertIn("positionTip", source)

    def test_css_uses_fixed_popover_and_mobile_bottom_sheet(self):
        source = (
            Path(settings.BASE_DIR) / "src/static/system/app.css"
        ).read_text(encoding="utf-8")
        self.assertIn("Patch 005.1", source)
        self.assertIn("position: fixed", source)
        self.assertIn('data-placement="bottom-sheet"', source)
