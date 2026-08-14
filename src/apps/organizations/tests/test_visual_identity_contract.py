from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class VisualIdentityContractTests(SimpleTestCase):
    def setUp(self) -> None:
        self.source_root = Path(settings.BASE_DIR) / "src"

    def test_direction_a_shell_loads_shared_identity_layers(self) -> None:
        template = (self.source_root / "templates/base.html").read_text(
            encoding="utf-8"
        )
        wrapper = (
            self.source_root / "templates/shared/direction_a/base.html"
        ).read_text(encoding="utf-8")
        sidebar = (
            self.source_root / "templates/shared/direction_a/_sidebar.html"
        ).read_text(encoding="utf-8")

        self.assertIn("system/eod_typography.css", template)
        self.assertIn("system/eod_iconography.css", template)
        self.assertIn("eodidentity002", template)
        self.assertIn('{% extends "base.html" %}', wrapper)
        self.assertIn("system/brand-mark.svg", sidebar)
        self.assertIn("eodbrand002", sidebar)
        self.assertNotIn("system/favicon.svg", sidebar)
        self.assertIn("system/favicon.svg", template)
        self.assertIn("Электронная оперативная документация", sidebar)
        self.assertNotIn('class="da-brand-mark"', sidebar)

    def test_typography_uses_onest_everywhere_and_consolas_for_technical_text(self) -> None:
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
        self.assertIn("--eod-font-mono: Consolas", stylesheet)
        self.assertIn("font-synthesis: style", stylesheet)
        self.assertIn("font-style: oblique", stylesheet)
        self.assertIn(".opj-ledger", stylesheet)
        self.assertIn("font-family: var(--eod-font-ui)", stylesheet)
        self.assertIn("font-variant-numeric: lining-nums tabular-nums", stylesheet)

    def test_brand_assets_are_deterministic_and_size_specific(self) -> None:
        mark = (self.source_root / "static/system/brand-mark.svg").read_text(
            encoding="utf-8"
        )
        favicon = (self.source_root / "static/system/favicon.svg").read_text(
            encoding="utf-8"
        )

        for asset in (mark, favicon):
            self.assertIn('viewBox="0 0 64 64"', asset)
            self.assertIn('fill="#1267A5"', asset)
            self.assertIn('stroke="#FFFFFF"', asset)
            self.assertNotIn("<image", asset)
            self.assertNotIn("<text", asset)

        self.assertIn("<circle", mark)
        self.assertIn("M23 28v16", mark)
        self.assertNotIn("<circle", favicon)
        self.assertIn("M22 31h18M22 42h14", favicon)
        self.assertNotEqual(mark, favicon)

    def test_icon_sprite_contains_shared_and_full_domain_catalogue(self) -> None:
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
            "icon-org-center",
            "icon-position",
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
            "icon-shift-handover",
            "icon-grounding",
            "icon-operational-order",
            "icon-current-works",
            "icon-inspection",
            "icon-commissioning",
            "icon-breaker-interruptions",
            "icon-battery-inspection",
            "icon-emergency-readiness",
            "icon-cross-document",
            "icon-reporting",
            "icon-equipment-line",
            "icon-equipment-cable",
            "icon-equipment-transformer",
            "icon-equipment-busbar",
            "icon-equipment-breaker",
            "icon-equipment-disconnector",
            "icon-equipment-ground-switch",
            "icon-equipment-portable-ground",
            "icon-equipment-rza",
            "icon-equipment-telemechanics",
            "icon-equipment-dc-supply",
            "icon-equipment-battery",
            "icon-import",
            "icon-filter",
            "icon-print",
        }

        for symbol_id in required_symbol_ids:
            with self.subTest(symbol_id=symbol_id):
                self.assertIn(f'id="{symbol_id}"', sprite)

        operations = sprite.split(
            '<symbol id="icon-org-operations"', maxsplit=1
        )[1].split("</symbol>", maxsplit=1)[0]
        dispatch = sprite.split(
            '<symbol id="icon-dispatch-center"', maxsplit=1
        )[1].split("</symbol>", maxsplit=1)[0]
        self.assertNotEqual(operations, dispatch)

    def test_icon_and_text_alignment_is_explicit(self) -> None:
        stylesheet = (
            self.source_root / "static/system/eod_iconography.css"
        ).read_text(encoding="utf-8")

        self.assertIn(".authority-tree-icon", stylesheet)
        self.assertIn("background: transparent !important", stylesheet)
        self.assertIn("--eod-icon-stroke: 2", stylesheet)
        self.assertIn("vertical-align: middle", stylesheet)
        self.assertIn("place-items: center", stylesheet)
        self.assertIn(".da-brand-logo", stylesheet)
        self.assertIn("object-fit: contain", stylesheet)

    def test_authority_matrix_owner_polish_owns_full_cell_marker_geometry(self) -> None:
        stylesheet = (
            self.source_root / "static/organizations/personnel_authority_matrix.css"
        ).read_text(encoding="utf-8")
        template = (
            self.source_root / "templates/organizations/authority_registry.html"
        ).read_text(encoding="utf-8")

        self.assertIn(
            ".authority-matrix-person td.authority-right-cell {",
            stylesheet,
        )
        self.assertIn("padding:0; text-align:center", stylesheet)
        self.assertIn(
            ".authority-matrix-person td.authority-right-cell.is-granted",
            stylesheet,
        )
        self.assertIn("background:var(--theme-success-soft)", stylesheet)
        self.assertIn(
            ".authority-matrix-person td.authority-right-cell.is-conditional",
            stylesheet,
        )
        self.assertIn("background:var(--theme-warning-soft)", stylesheet)
        self.assertIn(".authority-right-cell .authority-cell-marker", stylesheet)
        self.assertIn("font-size:var(--theme-font-size-sm)", stylesheet)
        self.assertIn("place-items:center", stylesheet)
        self.assertIn("authority-cell-marker--missing", template)
        self.assertNotIn("padding:0 !important", stylesheet)
        self.assertNotIn(
            ".authority-right-cell.is-granted a { background:var(--theme-success-soft)",
            stylesheet,
        )
        self.assertNotIn(
            ".authority-right-cell.is-conditional a { background:var(--theme-warning-soft)",
            stylesheet,
        )

    def test_authority_matrix_qualification_has_compact_semantic_zones(self) -> None:
        stylesheet = (
            self.source_root / "static/organizations/personnel_authority_matrix.css"
        ).read_text(encoding="utf-8")
        template = (
            self.source_root / "templates/organizations/authority_registry.html"
        ).read_text(encoding="utf-8")

        for marker in (
            "authority-qualification-layout",
            "authority-qualification-category",
            "authority-qualification-content",
            "authority-qualification-additional",
            "authority-qualification-primary",
            "authority-qualification-scope",
        ):
            self.assertIn(marker, template)
            self.assertIn(marker, stylesheet)
        self.assertIn("{% for special in row.special_qualifications %}", template)
        self.assertIn(
            "grid-template-columns:minmax(4.25rem,auto) minmax(0,1fr)",
            stylesheet,
        )
        self.assertIn(
            "overflow-wrap:break-word; word-break:normal",
            stylesheet,
        )
