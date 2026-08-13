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
        self.assertTrue((ROOT / "src/static/system/ux_platform_responsive.css").exists())

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
        browser_path = ROOT / "tests/browser_theme/run.py"
        if not browser_path.exists():
            self.skipTest("repository-only browser acceptance harness is not packaged in runtime images")
        browser = browser_path.read_text(encoding="utf-8")

        self.assertIn("(1920, 1080)", browser)
        self.assertIn("(2560, 1440)", browser)
        self.assertIn("(390, 844)", browser)
        self.assertIn('f"document overflow {route}', browser)
        self.assertIn('width_state["scrollWidth"] > width_state["innerWidth"] + 2', browser)

    def test_v9_equipment_relation_links_preserve_semantic_stack_geometry(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        template = read("src/templates/equipment/detail.html")

        self.assertGreaterEqual(template.count('class="ux-value-stack"'), 4)
        self.assertIn("li > a:not(.ux-value-stack) { display:block; }", css)
        self.assertIn("li > a.ux-value-stack", css)
        self.assertNotIn("equipment-relation-list li > a { display:block;", css)

    def test_v9_documents_relations_and_action_footer_are_semantic(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        template = read("src/templates/documents/detail.html")

        self.assertIn(
            'class="ux-value-stack" href="{% url \'documents:detail\' '
            'link.target_document.public_id %}"',
            template,
        )
        self.assertIn(
            'class="ux-value-stack" href="{% url \'documents:detail\' '
            'link.source_document.public_id %}"',
            template,
        )
        self.assertIn('class="ux-value-primary">{{ link.target_document.title }}', template)
        self.assertIn('class="ux-technical">{{ link.target_document.registration_number }}', template)
        self.assertIn('class="ux-value-primary">{{ link.source_document.title }}', template)
        self.assertIn('class="ux-technical">{{ link.source_document.registration_number }}', template)
        self.assertIn(
            ".ux-form-grid > .ux-form-actions,.ux-form-grid > .ux-filter-actions "
            "{ grid-column:1 / -1; }",
            css,
        )
        self.assertIn(
            '<div class="ux-form-actions"><button class="da-button" type="submit">'
            "Создать связь</button></div>",
            template,
        )

    def test_v9_authority_condition_popovers_have_one_active_controller(self) -> None:
        script = read("src/static/organizations/personnel_authority_matrix.js")

        self.assertIn("let activeConditionOwner = null", script)
        self.assertIn('popover.style.display = "none"', script)
        self.assertIn('popover.style.position = "fixed"', script)
        self.assertIn("activeConditionOwner && activeConditionOwner !== owner", script)
        self.assertIn('event.key === "Escape"', script)
        self.assertIn('lastPointerType !== "touch" && lastPointerType !== "pen"', script)
        self.assertIn('window.addEventListener("scroll", scheduleConditionPlacement, true)', script)

    def test_v9_width_chain_reaches_actual_specialist_and_wide_consumers(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        responsive = read("src/static/system/ux_platform_responsive.css")
        contacts = read("src/templates/organizations/_external_operational_contacts.html")
        opdocs = read("src/templates/operational_documents/registry.html")

        for consumer in (
            ".da-page:has(> main.authority-main) > main.authority-main",
            "main.authority-main > .authority-matrix-page",
            ".authority-matrix-page > .authority-workspace",
            ".authority-workspace > .authority-matrix-panel",
            ".authority-matrix-panel > .authority-matrix-scroll",
        ):
            self.assertIn(consumer, css)
        self.assertIn("--authority-tree-width: clamp(19rem, 18vw, 24rem)", responsive)
        self.assertIn(".authority-matrix-page .authority-tabs", responsive)
        self.assertIn("authority-external-directory-table", contacts)
        self.assertIn(".authority-panel:has(.authority-external-directory-table)", css)
        self.assertIn(".authority-table-wrap:has(.authority-external-directory-table)", css)
        self.assertIn("opdoc-filter-card", opdocs)
        self.assertIn(".da-page:has(.opdoc-filter-card) > main", css)
        self.assertIn(".opdoc-filter-card + .da-card .da-table-wrap", css)
        self.assertIn(".opdoc-filter-card + .da-card .da-table", css)

    def test_v9_opj_single_page_owns_canvas_without_spread_regression(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        workspace = read("src/templates/operational_log/shift_workspace.html")
        controls = read("src/static/operational_log/opj_workspace_controls.js")

        self.assertIn('data-opj-presentation-mode="single-spread"', workspace)
        self.assertIn('workspace.dataset.viewMode === "spread"', controls)
        self.assertIn('attributeFilter: ["data-view-mode"]', controls)
        self.assertIn('.opj-workspace[data-view-mode="single"] .opj-editor-container', css)
        self.assertIn('.opj-workspace[data-view-mode="single"] .opj-ledger-surface', css)
        self.assertIn("width:min(100%,112rem)", css)
        self.assertIn("margin-inline:auto", css)
        self.assertIn('.opj-workspace[data-view-mode="spread"] .opj-editor-container', css)
        self.assertNotIn("@media print", css)

    def test_v9_does_not_add_repair_stylesheet_or_specificity_debt(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")

        self.assertEqual(css.count("!important"), 3)
        self.assertFalse((ROOT / "src/static/system/repair_v9.css").exists())
        self.assertFalse((ROOT / "src/static/system/final_final.css").exists())

    def test_v10_operational_documents_registry_has_compact_semantic_geometry(self) -> None:
        template = read("src/templates/operational_documents/registry.html")

        self.assertIn('class="da-page-header opdoc-page-header"', template)
        self.assertNotIn('class="da-page-header da-page-header-compact"', template)
        self.assertIn('class="ux-kicker">Формы по утверждённым источникам', template)
        self.assertIn('class="da-field ux-field-two-thirds"', template)
        self.assertGreaterEqual(template.count('class="da-field ux-field-third"'), 4)
        self.assertIn('class="opdoc-date-range ux-field-full"', template)
        self.assertIn('class="ux-form-actions"', template)
        self.assertIn(".opdoc-registry-notices", template)
        self.assertIn("padding:var(--theme-space-3)", template)

    def test_v10_operational_documents_related_entities_are_semantic_links(self) -> None:
        template = read("src/templates/operational_documents/record_detail.html")

        self.assertIn('>← К журналам</a>', template)
        self.assertIn("equipment:detail", template)
        self.assertIn("documents:detail", template)
        self.assertIn('class="ux-value-primary">{{ item.dispatcher_name_snapshot }}', template)
        self.assertIn('class="ux-technical">{{ item.equipment_code_snapshot }}', template)
        self.assertIn('class="ux-value-primary">{{ item.title_snapshot }}', template)
        self.assertIn('class="opdoc-related-relation">{{ item.get_link_type_display }}', template)
        self.assertIn(".opdoc-related-link:hover", template)
        self.assertIn(".opdoc-related-link:focus-visible", template)
        self.assertIn("padding:var(--theme-space-3)", template)
        self.assertNotIn(
            "{{ item.target_record.registration_number }} · "
            "{{ item.target_record.title }}",
            template,
        )

    def test_v10_personnel_current_route_and_compact_workspace_are_server_owned(self) -> None:
        template = read("src/templates/organizations/directory.html")
        css = read("src/static/organizations/personnel_directory.css")

        self.assertIn('class="personnel-contour-card is-current"', template)
        self.assertIn('aria-current="page"', template)
        self.assertIn("grid-template-columns:minmax(19rem,22rem) minmax(0,1fr)", css)
        self.assertIn("grid-template-columns:clamp(19rem,17vw,23rem) minmax(0,1fr)", css)
        self.assertIn('.personnel-contour-card[aria-current="page"]', css)
        self.assertIn("background:var(--theme-selected)", css)
        self.assertNotIn("clamp(20rem,24%,30rem)", css)

    def test_v10_adds_no_repair_or_inventory_expanding_helper_files(self) -> None:
        self.assertFalse((ROOT / "src/static/operational_documents/operational_documents.css").exists())
        self.assertFalse((ROOT / "src/apps/system/tests/test_ux_platform_repair_v10.py").exists())
        self.assertFalse((ROOT / "tests/browser_theme/repair_v10.py").exists())
        self.assertFalse((ROOT / "src/static/system/repair_v10.css").exists())
