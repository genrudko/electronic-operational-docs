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
        self.assertIn("@media screen and (min-width: 48rem) and (max-width: 61.25rem)", responsive)
        self.assertIn("@media screen and (max-width: 47.99rem)", responsive)
        self.assertIn("@media screen and (max-width: 47.99rem)", surfaces)
        self.assertIn("Compact keeps mouse-oriented control density", responsive)
        self.assertIn("Phone is touch-first", surfaces)
        phone = responsive[responsive.rindex("@media screen and (max-width: 47.99rem)") :]
        self.assertIn(
            "body.ux-platform.opj-clean-journal-page .journal-workspace-actions .da-button",
            phone,
        )
        self.assertIn("button.da-icon-button.draft-row-action", phone)
        self.assertIn("button.draft-editor-ribbon-button", phone)
        self.assertIn("min-width: 0 !important", responsive)

    def test_personnel_releases_content_width_before_shell_compacts(self) -> None:
        css = read("src/static/organizations/personnel_directory.css")

        compact = css[css.index("@media (max-width:70rem)") :]
        self.assertIn(".personnel-directory-workspace { grid-template-columns:1fr", compact)
        self.assertIn(".personnel-directory-sidebar { position:static; }", compact)
        self.assertIn("@media (max-width:61.25rem)", compact)
        self.assertIn(".personnel-recent-grid { grid-template-columns:1fr; }", compact)
        self.assertNotIn("@media (max-width:59.375rem)", css)

    def test_compact_state_keeps_dense_opj_and_rights_surfaces_distinct_from_phone(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")

        compact_start = responsive.index(
            "@media screen and (min-width: 48rem) and (max-width: 61.25rem)"
        )
        phone_start = responsive.index(
            "@media screen and (max-width: 47.99rem)",
            compact_start,
        )
        compact = responsive[compact_start:phone_start]
        phone = responsive[phone_start:]

        self.assertIn(
            "grid-template-columns: clamp(6.5rem, 18%, 8rem) minmax(0, 1fr)",
            compact,
        )
        self.assertIn(
            ".draft-ledger-visas:not(:has([data-opj-marker])) { display: none; }",
            compact,
        )
        self.assertIn(
            ".approved-journal-visas:not(:has([data-opj-marker])) { display: none; }",
            compact,
        )
        self.assertIn(
            ".authority-matrix-panel .authority-matrix-scroll {",
            compact,
        )
        self.assertIn("display: block;", compact)
        self.assertIn(".authority-mobile-matrix { display: none; }", compact)
        self.assertIn(".authority-holders-table {", compact)
        self.assertIn("display: table;", compact)
        self.assertIn("position: sticky;", compact)
        self.assertIn(".authority-matrix-panel .authority-matrix-scroll { display: none; }", phone)
        self.assertIn(".authority-mobile-matrix {", phone)
        self.assertIn("display: grid;", phone)

    def test_authority_progressive_enhancement_splits_compact_preamble_from_phone_projection(self) -> None:
        script = read("src/static/organizations/personnel_authority_followup.js")
        controller = read("src/static/organizations/personnel_authority_matrix.js")

        self.assertIn('matchMedia("(max-width: 61.25rem)")', script)
        self.assertIn('matchMedia("(max-width: 47.99rem)")', script)
        self.assertIn("const enhancePreamble", script)
        self.assertIn("const buildMobileMatrix", script)
        self.assertIn("if (mobileMatrixBuilt || !mobileMedia.matches) return", script)
        self.assertIn("ensureAuthorityPresentation", script)
        self.assertIn("compactMedia.addEventListener", script)
        self.assertIn("mobileMedia.addEventListener", script)

        self.assertIn("const resetGlobalFilterContext", controller)
        self.assertIn('if (search) search.value = ""', controller)
        self.assertIn('selectedDivision = ""', controller)
        self.assertIn("collapsed.clear()", controller)
        self.assertIn("resetGlobalFilterContext();", controller)

    def test_repair_v14_1_compact_dense_surface_owners_are_explicit(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        compact_start = responsive.index(
            "@media screen and (min-width: 48rem) and (max-width: 61.25rem)"
        )
        phone_start = responsive.index(
            "@media screen and (max-width: 47.99rem)", compact_start
        )
        compact = responsive[compact_start:phone_start]

        self.assertIn(
            'html body.ux-platform .authority-panel[data-authority-panel="holders"] '
            '.authority-table-wrap > .authority-table.authority-holders-table {',
            compact,
        )
        self.assertIn(
            ".authority-matrix > thead th::before { content: none; display: none; }",
            compact,
        )
        self.assertIn(
            ".authority-holders-table > thead th::before { content: none; display: none; }",
            compact,
        )
        self.assertIn(
            "grid-template-columns: minmax(0, 1fr) auto;",
            compact,
        )
        self.assertIn(
            ".opj-toolbar-search {\n        grid-column: 1 / -1;",
            compact,
        )
        self.assertIn(
            ".draft-ledger-visas::before,\n    "
            "body.ux-platform.opj-clean-journal-page .approved-journal-visas::before",
            compact,
        )
        self.assertIn('content: "Визы";', compact)
        self.assertIn(
            ".opj-entry-date-placeholder { display: none; }",
            compact,
        )

    def test_repair_v14_2_compact_opj_viewport_geometry_and_redundant_date_contract(
        self,
    ) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        surfaces = read("src/static/system/ux_mobile_surfaces.css")

        compact_start = responsive.index(
            "@media screen and (min-width: 48rem) and (max-width: 61.25rem)"
        )
        phone_start = responsive.index(
            "@media screen and (max-width: 47.99rem)", compact_start
        )
        compact = responsive[compact_start:phone_start]
        phone = responsive[phone_start:]

        self.assertIn(
            "html body.ux-platform.opj-workspace-page .opj-workspace-header {",
            compact,
        )
        self.assertIn(
            "html body.ux-platform.opj-workspace-page .opj-clean-summary {",
            compact,
        )
        self.assertIn(
            "html body.ux-platform.opj-workspace-page "
            ".opj-toolbar[data-ribbon-mode=\"compact\"] .opj-editor-toolbar {",
            compact,
        )
        compact_toolbar = (
            "html body.ux-platform.opj-workspace-page "
            ".opj-toolbar[data-ribbon-mode=\"compact\"] .opj-editor-toolbar"
        )
        self.assertIn("display: none;", compact[compact.index(compact_toolbar) :])
        self.assertIn(
            "html body.ux-platform.opj-clean-journal-page "
            ".opj-clean-shift-group:has(.opj-clean-shift-date) "
            ".opj-entry-date-placeholder {",
            compact,
        )
        compact_date = (
            "html body.ux-platform.opj-clean-journal-page "
            ".opj-clean-shift-group:has(.opj-clean-shift-date) "
            ".opj-entry-date-placeholder"
        )
        self.assertIn("display: none;", compact[compact.index(compact_date) :])
        self.assertIn(
            "html body.ux-platform.opj-clean-journal-page "
            ".opj-clean-shift-group:has(.opj-clean-shift-date) "
            ".opj-entry-date-placeholder {",
            phone,
        )
        stale_editor_rule = (
            "html body.ux-platform.opj-workspace-page "
            ".opj-toolbar[data-ribbon-mode=\"compact\"] .opj-editor-toolbar,\n"
            "    html body.ux-platform.opj-workspace-page "
            ".opj-toolbar[data-ribbon-mode=\"expanded\"] .opj-editor-toolbar {\n"
            "        display: grid;"
        )
        self.assertNotIn(stale_editor_rule, surfaces)

        opj_acceptance = read("src/static/operational_log/opj_lifecycle_acceptance_repair.css")
        normative_markers = read("src/templates/operational_log/_normative_markers.html")

        self.assertNotIn(".approved-journal-date-time > span", opj_acceptance)
        self.assertNotIn(".approved-journal-date-time > span", normative_markers)
        self.assertIn(
            ".opj-clean-journal-page .approved-journal-date-time > strong,\n"
            ".opj-clean-journal-page .approved-journal-date-time > small {",
            opj_acceptance,
        )
        self.assertIn(
            ".opj-clean-journal-page .approved-journal-date-time > strong,\n"
            "            .opj-clean-journal-page .approved-journal-date-time > small {",
            normative_markers,
        )

    def test_human_text_uses_word_boundaries_and_only_technical_codes_use_anywhere(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        surfaces = read("src/static/system/ux_mobile_surfaces.css")
        defect_registry = read("src/static/equipment_defects/ux_foundation_repair2_registry.css")
        opj_registered = read("src/static/operational_log/opj_registered_actions.css")
        opj_workspace = read("src/static/operational_log/opj_workspace_controls.css")

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
        rich_paragraph = opj_registered[opj_registered.index(".opj-rich-paragraph") :]
        self.assertIn("overflow-wrap: break-word", rich_paragraph)
        self.assertIn("word-break: normal", rich_paragraph)
        rich_editor = opj_workspace[opj_workspace.index(".opj-workspace textarea[data-editor-fallback]") :]
        self.assertIn("overflow-wrap: break-word", rich_editor)
        self.assertIn("word-break: normal", rich_editor)

    def test_compact_opj_keeps_spread_sequential_without_stacking_each_record(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")
        surfaces = read("src/static/system/ux_mobile_surfaces.css")

        self.assertIn('.opj-toolbar[data-ribbon-mode="compact"] .opj-tool-group:nth-child(1)', surfaces)
        self.assertIn('.opj-toolbar[data-ribbon-mode="compact"] .opj-tool-group:nth-child(2)', surfaces)
        self.assertIn('.opj-view-switch [data-view-mode="spread"] { display: inline-flex; }', responsive)
        self.assertIn('content: "Первая страница разворота";', responsive)
        self.assertIn('content: "Вторая страница разворота";', responsive)
        compact = responsive[
            responsive.index("/* Repair v14: COMPACT OPJ is a ledger") :
            responsive.index("/* Repair v14: COMPACT Rights")
        ]
        self.assertNotIn('.draft-ledger-time::before { content: "Время"; }', compact)
        self.assertIn("grid-template-columns: clamp(6.5rem, 18%, 8rem) minmax(0, 1fr)", compact)

    def test_no_repair_specific_stylesheet_or_horizontal_page_pan_contract(self) -> None:
        responsive = read("src/static/system/ux_platform_responsive.css")

        self.assertIn("overflow-x: clip", responsive)
        self.assertIn(".ux-intrinsic-wide", responsive)
        self.assertIn("overscroll-behavior-inline: contain", responsive)
        self.assertNotIn("repair_v14.css", responsive.lower())
        self.assertFalse((ROOT / "src/static/system/repair_v14.css").exists())

    def test_browser_gate_resizes_mandatory_surfaces_down_and_back_up(self) -> None:
        browser_path = ROOT / "tests/browser_theme/run.py"
        if not browser_path.is_file():
            self.skipTest("repository-level browser harness is not packaged in runtime images")
        browser = browser_path.read_text(encoding="utf-8")

        for width in (
            1440, 1280, 1180, 1100, 1024, 976, 950, 900, 880, 832,
            768, 656, 600, 440, 412, 390,
        ):
            self.assertIn(f"    {width},", browser)
        for route in (
            '"personnel"',
            '"authorities"',
            '"imports"',
            '"workplace_docs"',
            '"defect_registry"',
            '"opj_registry"',
            '"registered_opj"',
            '"draft_workspace"',
        ):
            self.assertIn(route, browser)
        self.assertIn("TRANSITION_WIDTHS + tuple(reversed(TRANSITION_WIDTHS[:-1]))", browser)
        self.assertIn("responsive transition document overflow", browser)
        self.assertIn("responsive transition human-word shredding", browser)
        self.assertIn("authorityNativeMatrixExists", browser)
        self.assertIn("authorityMobileMatrixExists", browser)
        self.assertIn("authorityMatrixOverflow", browser)
        self.assertIn("opjDraftColumns", browser)
        self.assertIn("opjFirstRowTop", browser)
        self.assertIn("opjCleanDuplicateDateVisible", browser)
        self.assertIn("capture_responsive_transitions(page, shots, report, runtime_errors)", browser)
