from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformRenderedConsumersV9SourceContractTests(SimpleTestCase):
    """Bounded regressions for Repair v9 rendered-consumer ownership.

    These checks guard the source-level causes that previously let valid platform
    primitives render incorrectly. Final viewport geometry is still verified by
    the browser/manual acceptance pass on the exact deployed SHA.
    """

    def test_equipment_relation_links_preserve_semantic_stack_geometry(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        template = read("src/templates/equipment/detail.html")

        self.assertGreaterEqual(template.count('class="ux-value-stack"'), 4)
        self.assertIn("li > a:not(.ux-value-stack) { display:block; }", css)
        self.assertIn("li > a.ux-value-stack", css)
        self.assertNotIn("equipment-relation-list li > a { display:block;", css)

    def test_documents_relations_render_identity_as_two_semantic_levels(self) -> None:
        template = read("src/templates/documents/detail.html")

        self.assertIn('class="ux-value-stack" href="{% url \'documents:detail\' link.target_document.public_id %}"', template)
        self.assertIn('class="ux-value-stack" href="{% url \'documents:detail\' link.source_document.public_id %}"', template)
        self.assertIn('class="ux-value-primary">{{ link.target_document.title }}', template)
        self.assertIn('class="ux-technical">{{ link.target_document.registration_number }}', template)
        self.assertIn('class="ux-value-primary">{{ link.source_document.title }}', template)
        self.assertIn('class="ux-technical">{{ link.source_document.registration_number }}', template)

    def test_form_action_footer_spans_the_canonical_grid(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        template = read("src/templates/documents/detail.html")

        self.assertIn(".ux-form-grid > .ux-form-actions,.ux-form-grid > .ux-filter-actions { grid-column:1 / -1; }", css)
        self.assertIn('<form class="ux-form-grid"', template)
        self.assertIn('<div class="ux-form-actions"><button class="da-button" type="submit">Создать связь</button></div>', template)

    def test_authority_condition_popovers_have_one_active_controller(self) -> None:
        script = read("src/static/organizations/personnel_authority_matrix.js")

        self.assertIn("let activeConditionOwner = null", script)
        self.assertIn('popover.style.display = "none"', script)
        self.assertIn('popover.style.position = "fixed"', script)
        self.assertIn("activeConditionOwner && activeConditionOwner !== owner", script)
        self.assertIn('event.key === "Escape"', script)
        self.assertIn('lastPointerType !== "touch" && lastPointerType !== "pen"', script)
        self.assertIn('window.addEventListener("scroll", scheduleConditionPlacement, true)', script)

    def test_authority_width_chain_reaches_actual_matrix_viewport(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        responsive = read("src/static/system/ux_platform_responsive.css")

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
        self.assertIn("overflow: visible", responsive)

    def test_personnel_external_contacts_receive_available_wide_surface(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        template = read("src/templates/organizations/_external_operational_contacts.html")

        self.assertIn("authority-external-directory-table", template)
        self.assertIn(".authority-panel:has(.authority-external-directory-table)", css)
        self.assertIn(".authority-table-wrap:has(.authority-external-directory-table)", css)
        self.assertIn(".authority-external-directory-table", css)

    def test_operational_documents_wide_profile_reaches_table_surface(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        template = read("src/templates/operational_documents/registry.html")

        self.assertIn('class="da-card opdoc-filter-card"', template)
        self.assertIn(".da-page:has(.opdoc-filter-card) > main", css)
        self.assertIn(".opdoc-filter-card + .da-card .da-table-wrap", css)
        self.assertIn(".opdoc-filter-card + .da-card .da-table", css)

    def test_opj_single_page_owns_canvas_instead_of_hiding_spread_half(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        workspace = read("src/templates/operational_log/shift_workspace.html")

        self.assertIn('data-view-mode="{{ workspace_preferences.view_mode }}"', workspace)
        self.assertIn('.opj-workspace[data-view-mode="single"] .opj-editor-container', css)
        self.assertIn('.opj-workspace[data-view-mode="single"] .opj-ledger-surface', css)
        self.assertIn("width:min(100%,112rem)", css)
        self.assertIn("margin-inline:auto", css)
        self.assertIn('.opj-workspace[data-view-mode="spread"] .opj-editor-container', css)

    def test_v9_does_not_add_specificity_or_repair_stylesheet_debt(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")

        self.assertEqual(css.count("!important"), 3)
        self.assertFalse((ROOT / "src/static/system/repair_v9.css").exists())
        self.assertFalse((ROOT / "src/static/system/final_final.css").exists())
        self.assertNotIn("@media print", css)
