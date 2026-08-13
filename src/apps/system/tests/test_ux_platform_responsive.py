from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformResponsiveSourceContractTests(SimpleTestCase):
    def test_responsive_owner_loads_after_feature_extra_head(self) -> None:
        base = read("src/templates/base.html")

        extra_head = base.index("{% block extra_head %}")
        responsive = base.index("system/ux_platform_responsive.css")

        self.assertLess(extra_head, responsive)
        self.assertEqual(base.count("system/ux_platform_responsive.css"), 1)
        self.assertTrue(
            (ROOT / "src/static/system/ux_platform_responsive.css").exists()
        )

    def test_responsive_owner_is_semantic_and_not_a_repair_stylesheet(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")

        self.assertIn("Responsive data-surface owner", css)
        self.assertNotIn("repair_v8.css", css.lower())
        self.assertNotIn("mobile_final_fix.css", css.lower())
        self.assertNotIn("acceptance_patch.css", css.lower())
        self.assertNotIn("zoom:", css.lower())
        self.assertNotIn("transform: scale(", css.lower())
        self.assertNotIn("#", css)

    def test_mobile_page_overflow_and_touch_contract_are_explicit(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")

        self.assertIn("overflow-x: clip", css)
        self.assertIn("2.75rem", css)
        self.assertIn(".da-icon-button", css)
        self.assertIn(".da-menu-button", css)
        self.assertIn(".authority-tabs button", css)
        self.assertIn("button.draft-editor-ribbon-button", css)

    def test_ordinary_registry_cards_have_real_consumers(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")

        for consumer in (
            ".document-list-card .da-table",
            ".equipment-filter-card ~ .da-card.ux-stack .da-table",
            ".journal-registry-table",
            ".opdoc-filter-card + .da-card .da-table",
            ".personnel-employee-table",
        ):
            self.assertIn(consumer, css)

        self.assertIn('content: "Стабильный код"', css)
        self.assertIn('content: "Рабочее место"', css)
        self.assertIn('content: "Квалификация"', css)

    def test_operational_rights_has_mobile_master_detail_contract(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")
        authority = read("src/templates/organizations/authority_registry.html")

        self.assertIn(".authority-publication-banner > div", css)
        self.assertIn(".authority-matrix .authority-matrix-person", css)
        self.assertIn(".authority-right-cell:not(:has(a))", css)
        self.assertIn(".authority-holders-table", css)
        self.assertIn('content: attr(aria-label)', css)
        self.assertIn('data-authority-panel="holders"', authority)
        self.assertIn("authority-holders-table", authority)

    def test_defect_normative_form_owns_inner_wide_viewport(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")
        journal = read("src/templates/equipment_defects/_registry_repair2_journal.html")

        self.assertIn(".ux-intrinsic-wide", css)
        self.assertIn(".defect-journal-view .defect-register-wrap", css)
        self.assertIn("overflow-x: auto", css)
        self.assertIn("overscroll-behavior-inline: contain", css)
        self.assertIn("defect-register-wrap", journal)
        self.assertIn("defect-register", journal)

    def test_opj_mobile_contract_uses_responsive_controls_and_stacked_ledger(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")
        toolbar = read("src/templates/operational_log/_shift_workspace_toolbar.html")
        rows = read("src/templates/operational_log/_shift_workspace_rows.html")
        detail = read("src/templates/operational_log/detail.html")

        self.assertIn('.opj-toolbar[data-ribbon-mode="compact"]', css)
        self.assertIn('.opj-toolbar[data-ribbon-mode="expanded"]', css)
        self.assertIn('.opj-view-switch [data-view-mode="spread"]', css)
        self.assertIn(".draft-ledger-form", css)
        self.assertIn(".approved-journal-row", css)
        self.assertIn("data-ribbon-mode", toolbar)
        self.assertIn("draft-ledger-form", rows)
        self.assertIn("approved-journal-table", detail)

    def test_wide_specialist_consumers_receive_stage_width(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")

        self.assertIn("@media screen and (min-width: 100rem)", css)
        self.assertIn("--authority-tree-width: clamp(19rem, 18vw, 24rem)", css)
        self.assertIn(".authority-matrix-page .authority-tabs", css)
        self.assertIn(".personnel-directory-workspace", css)
        self.assertIn(".opdoc-filter-card + .da-card .da-table", css)
        self.assertIn('.opj-workspace[data-page-width="full"]', css)
        self.assertIn('.opj-workspace[data-view-mode="spread"]', css)

    def test_topbar_mobile_context_is_not_permanent_ellipsis(self) -> None:
        css = read("src/static/system/ux_platform_responsive.css")
        topbar = read("src/templates/shared/direction_a/_topbar.html")

        self.assertIn(".da-workplace strong", css)
        self.assertIn("white-space: normal", css)
        self.assertIn("text-overflow: clip", css)
        self.assertIn('class="da-workplace"', topbar)

    def test_existing_browser_matrix_still_blocks_document_level_overflow(self) -> None:
        browser = read("tests/browser_theme/run.py")

        self.assertIn("(1920, 1080)", browser)
        self.assertIn("(2560, 1440)", browser)
        self.assertIn("(390, 844)", browser)
        self.assertIn('f"document overflow {route}', browser)
        self.assertIn('width_state["scrollWidth"] > width_state["innerWidth"] + 2', browser)
