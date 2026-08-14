from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformMobileClosureSourceContractTests(SimpleTestCase):
    def test_shared_phone_surfaces_are_semantic_and_do_not_break_human_words(self) -> None:
        css = read("src/static/system/ux_mobile_surfaces.css")

        self.assertIn("Mobile functional data-surface compositions", css)
        self.assertIn("@media screen and (max-width: 47.99rem)", css)
        self.assertIn(".ux-mobile-record-card", css)
        self.assertIn(".ux-mobile-audit-card", css)
        self.assertIn("overflow-wrap: break-word", css)
        self.assertIn("word-break: normal", css)
        self.assertNotIn("overflow-wrap: anywhere", css)
        self.assertNotIn("repair_v12.css", css.lower())
        self.assertNotIn("mobile_final.css", css.lower())
        self.assertNotIn("!important", css)

    def test_opj_mobile_toolbar_is_a_command_composition_not_wrapped_desktop_ribbon(self) -> None:
        page = read("src/templates/operational_log/shift_workspace.html")
        toolbar = read("src/templates/operational_log/_shift_workspace_toolbar.html")
        css = read("src/static/system/ux_mobile_surfaces.css")

        self.assertIn("system/ux_mobile_surfaces.css", page)
        self.assertIn('data-ribbon-mode="compact"', toolbar)
        self.assertIn("opj-ribbon-toggle-mobile-label", toolbar)
        self.assertIn("opj-mobile-command-caption", toolbar)
        self.assertIn("Связать", toolbar)
        self.assertIn("Авто", toolbar)
        self.assertIn("Найти", toolbar)
        self.assertIn("Открыть", toolbar)
        self.assertIn('.opj-toolbar[data-ribbon-mode="compact"] .opj-editor-toolbar', css)
        self.assertIn(".opj-tool-group:nth-child(1)", css)
        self.assertIn(".opj-tool-group:nth-child(2)", css)
        self.assertIn("min-height: 2.75rem", css)
        self.assertIn(".opj-clean-summary-meta", css)

    def test_operational_document_revisions_have_phone_audit_cards(self) -> None:
        template = read("src/templates/operational_documents/record_detail.html")

        self.assertIn("opdoc-revision-history", template)
        self.assertIn("opdoc-revision-desktop-table", template)
        self.assertIn("opdoc-revision-mobile-list", template)
        self.assertIn("ux-mobile-audit-card", template)
        self.assertIn("revision.actor.full_name", template)
        self.assertIn("revision.created_at", template)
        self.assertIn("revision.comment", template)

    def test_workplace_document_lists_and_positions_have_phone_cards(self) -> None:
        registry = read("src/templates/workplace_docs/registry.html")
        detail = read("src/templates/workplace_docs/detail.html")
        css = read("src/static/system/ux_mobile_surfaces.css")

        self.assertIn("workplace-document-desktop-table", registry)
        self.assertIn("workplace-document-mobile-list", registry)
        self.assertIn("ux-mobile-record-card", registry)
        self.assertIn("workplace-document-entry-desktop-table", detail)
        self.assertIn("workplace-document-entry-mobile-list", detail)
        self.assertIn("entry.get_requirement_kind_display", detail)
        self.assertIn("entry.get_storage_form_display", detail)
        self.assertIn("entry.basis_text", detail)
        self.assertIn("word-break: normal", css)
        self.assertNotIn("overflow-wrap:anywhere", css)

    def test_import_attempts_have_phone_audit_cards(self) -> None:
        template = read("src/templates/imports/list.html")
        css = read("src/static/system/ux_mobile_surfaces.css")

        self.assertIn("import-attempt-desktop-table", template)
        self.assertIn("import-attempt-mobile-list", template)
        self.assertIn("batch.original_filename", template)
        self.assertIn("batch.get_target_registry_display", template)
        self.assertIn("batch.data_profile.name", template)
        self.assertIn("batch.data_rows", template)
        self.assertIn("batch.created_by.full_name", template)
        self.assertIn("batch.created_at", template)
        self.assertIn("width: fit-content", css)

    def test_rights_phone_matrix_is_employee_first_grouped_and_touch_accessible(self) -> None:
        css = read("src/static/organizations/personnel_authority_matrix.css")
        js = read("src/static/organizations/personnel_authority_followup.js")
        template = read("src/templates/organizations/authority_registry.html")

        self.assertIn("authority-mobile-preamble-disclosure", css)
        self.assertIn("authority-mobile-matrix", css)
        self.assertIn("authority-mobile-employee", css)
        self.assertIn("authority-mobile-right-group", css)
        self.assertIn("authority-mobile-marker", css)
        self.assertIn("width:2.75rem", css)
        self.assertIn("height:2.75rem", css)
        self.assertIn("word-break:normal", css)

        self.assertIn("enhancePreamble", js)
        self.assertIn("buildMobileMatrix", js)
        self.assertIn("buildMobileEmployee", js)
        self.assertIn("rightMetadata", js)
        self.assertIn("data-mobile-condition-trigger", js)
        self.assertIn('setAttribute("aria-expanded"', js)
        self.assertIn('setAttribute("aria-controls"', js)
        self.assertIn("MutationObserver", js)
        self.assertIn("Непредоставленные права скрыты", js)

        self.assertIn("authority-category-header", template)
        self.assertIn("data-right-column", template)
        self.assertIn("authority-condition-popover", template)
        self.assertIn("authority-qualification-layout", template)

    def test_personnel_odd_contour_owns_full_phone_row_only(self) -> None:
        css = read("src/static/organizations/personnel_directory.css")

        self.assertIn("@media (max-width:47.99rem)", css)
        self.assertIn(".personnel-contours > .personnel-contour-card:last-child:nth-child(odd)", css)
        self.assertIn("grid-column:1 / -1", css)

    def test_new_phone_surfaces_preserve_desktop_tables(self) -> None:
        opdoc = read("src/templates/operational_documents/record_detail.html")
        registry = read("src/templates/workplace_docs/registry.html")
        detail = read("src/templates/workplace_docs/detail.html")
        imports = read("src/templates/imports/list.html")

        for template in (opdoc, registry, detail, imports):
            self.assertIn("<table", template)
            self.assertIn("da-table", template)
