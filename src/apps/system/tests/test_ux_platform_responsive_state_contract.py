from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformResponsiveStateContractTests(SimpleTestCase):
    def test_platform_declares_one_compact_boundary_and_a_narrower_phone_state(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        surfaces = read("src/static/system/ux_mobile_surfaces.css")
        shell = read("src/static/system/ux_platform.css")

        self.assertIn("@media (max-width: 980px)", shell)
        self.assertIn("@media screen and (max-width: 61.25rem)", responsive)
        self.assertIn("@media screen and (max-width: 61.25rem)", surfaces)
        self.assertIn("@media screen and (max-width: 47.99rem)", responsive)
        self.assertIn("@media screen and (max-width: 47.99rem)", surfaces)
        self.assertIn("Compact keeps mouse-oriented control density", responsive)
        self.assertIn("Phone is touch-first", surfaces)

    def test_personnel_releases_content_width_before_shell_compacts(self) -> None:
        css = read("src/static/organizations/personnel_directory.css")

        compact = css[css.index("@media (max-width:70rem)") :]
        self.assertIn(".personnel-directory-workspace { grid-template-columns:1fr", compact)
        self.assertIn(".personnel-directory-sidebar { position:static; }", compact)
        self.assertIn("@media (max-width:61.25rem)", compact)
        self.assertIn(".personnel-recent-grid { grid-template-columns:1fr; }", compact)
        self.assertNotIn("@media (max-width:59.375rem)", css)

    def test_compact_state_adapts_dense_operational_surfaces(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        surfaces = read("src/static/system/ux_mobile_surfaces.css")
        authority = read("src/static/organizations/personnel_authority_matrix.css")

        compact = responsive[responsive.index("@media screen and (max-width: 61.25rem)") :]
        for selector in (
            ".journal-registry-table",
            ".personnel-employee-table",
            ".authority-table",
            ".authority-workspace",
            ".defect-da-work-table",
            ".opj-toolbar-primary",
        ):
            self.assertIn(selector, compact)

        for selector in (
            ".workplace-document-mobile-list",
            ".workplace-document-entry-mobile-list",
            ".import-attempt-mobile-list",
            ".authority-mobile-matrix",
        ):
            self.assertIn(selector, surfaces)

        self.assertIn("@media (max-width:61.25rem)", authority)
        self.assertIn(".authority-matrix-panel .authority-matrix-scroll { display:none; }", authority)
        self.assertIn(".authority-mobile-matrix", authority)

    def test_human_text_uses_word_boundaries_and_only_technical_codes_use_anywhere(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        surfaces = read("src/static/system/ux_mobile_surfaces.css")
        defect_registry = read("src/static/equipment_defects/ux_foundation_repair2_registry.css")

        self.assertIn("overflow-wrap: break-word", responsive)
        self.assertIn("word-break: normal", responsive)
        self.assertNotIn("overflow-wrap: anywhere", surfaces)
        self.assertEqual(responsive.count("overflow-wrap: anywhere"), 1)
        technical_rule = responsive[responsive.index(".authority-evaluation-technical code") :]
        self.assertIn("overflow-wrap: anywhere", technical_rule)
        self.assertIn(
            ".defect-da-work-row strong,.defect-da-work-row a"
            "{overflow-wrap:break-word;word-break:normal;}",
            defect_registry,
        )

    def test_compact_opj_is_disclosure_based_and_spread_is_sequential(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        surfaces = read("src/static/system/ux_mobile_surfaces.css")

        self.assertIn('.opj-toolbar[data-ribbon-mode="compact"] .opj-tool-group:nth-child(1)', surfaces)
        self.assertIn('.opj-toolbar[data-ribbon-mode="compact"] .opj-tool-group:nth-child(2)', surfaces)
        self.assertIn('.opj-view-switch [data-view-mode="spread"] { display: inline-flex; }', responsive)
        self.assertIn('grid-template-columns: 1fr;', responsive)
        self.assertIn('content: "Первая страница разворота";', responsive)
        self.assertIn('content: "Вторая страница разворота";', responsive)

    def test_no_repair_specific_stylesheet_or_horizontal_page_pan_contract(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")

        self.assertIn("overflow-x: clip", responsive)
        self.assertIn(".ux-intrinsic-wide", responsive)
        self.assertIn("overscroll-behavior-inline: contain", responsive)
        self.assertNotIn("repair_v13.css", responsive.lower())
        self.assertFalse((ROOT / "src/static/system/repair_v13.css").exists())

    def test_browser_gate_resizes_mandatory_surfaces_down_and_back_up(self) -> None:
        browser = read("tests/browser_theme/run.py")

        for width in (1440, 1280, 1180, 1100, 1024, 976, 950, 900, 832, 768, 600, 440, 412, 390):
            self.assertIn(f"    {width},", browser)
        for route in (
            '"personnel"',
            '"authorities"',
            '"imports"',
            '"workplace_docs"',
            '"defect_registry"',
            '"opj_registry"',
            '"draft_workspace"',
        ):
            self.assertIn(route, browser)
        self.assertIn("TRANSITION_WIDTHS + tuple(reversed(TRANSITION_WIDTHS[:-1]))", browser)
        self.assertIn("responsive transition document overflow", browser)
        self.assertIn("responsive transition human-word shredding", browser)
        self.assertIn("capture_responsive_transitions(page, shots, report, runtime_errors)", browser)
