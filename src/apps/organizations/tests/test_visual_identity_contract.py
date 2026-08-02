from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class VisualIdentityContractTests(SimpleTestCase):
    def setUp(self) -> None:
        self.source_root = Path(settings.BASE_DIR) / "src"

    def test_direction_a_shell_loads_shared_identity_layers(self) -> None:
        template = (
            self.source_root / "templates/shared/direction_a/base.html"
        ).read_text(encoding="utf-8")

        self.assertIn("system/eod_typography.css", template)
        self.assertIn("system/eod_iconography.css", template)
        self.assertIn("eodidentity001", template)

    def test_typography_uses_real_onest_face_and_controlled_fallback(self) -> None:
        stylesheet = (
            self.source_root / "static/system/eod_typography.css"
        ).read_text(encoding="utf-8")

        self.assertIn("@font-face {", stylesheet)
        self.assertIn('font-family: "Onest"', stylesheet)
        self.assertIn(
            "f18c06a14512e43a6191849278d6f07fdaf347d6",
            stylesheet,
        )
        self.assertIn("--eod-font-ui", stylesheet)
        self.assertIn("font-variant-numeric: lining-nums tabular-nums", stylesheet)
        self.assertIn("--journal-font-family", stylesheet)

    def test_icon_sprite_contains_shared_and_domain_catalogue(self) -> None:
        sprite = (self.source_root / "static/system/icons.svg").read_text(
            encoding="utf-8"
        )
        required_symbol_ids = {
            "icon-home",
            "icon-journal",
            "icon-document",
            "icon-equipment",
            "icon-organization",
            "icon-role",
            "icon-dispatch-center",
            "icon-org-leadership",
            "icon-org-operations",
            "icon-org-maintenance",
            "icon-org-rza",
            "icon-org-technical",
            "icon-org-wind",
            "icon-org-substation",
            "icon-module-defects",
            "icon-module-work-permits",
            "icon-module-switching",
            "icon-module-schemes",
            "icon-import",
            "icon-filter",
            "icon-print",
        }

        for symbol_id in required_symbol_ids:
            with self.subTest(symbol_id=symbol_id):
                self.assertIn(f'id="{symbol_id}"', sprite)

    def test_dense_tree_icon_is_not_a_colored_decorative_tile(self) -> None:
        stylesheet = (
            self.source_root / "static/system/eod_iconography.css"
        ).read_text(encoding="utf-8")

        self.assertIn(".authority-tree-icon", stylesheet)
        self.assertIn("background: transparent !important", stylesheet)
        self.assertIn("--eod-icon-stroke: 2", stylesheet)
