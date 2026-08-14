import pathlib

from django.test import SimpleTestCase, TestCase
from django.urls import reverse


ROOT = pathlib.Path(__file__).resolve().parents[4]


def read_source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class SystemSmokeTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Электронная оперативная документация")
        self.assertContains(
            response,
            "Ядро структурированных журналов готово к установке утверждённых форм",
        )
        self.assertContains(response, "Утверждённые формы журналов")
        self.assertContains(response, "Управление и ведение")
        self.assertNotContains(response, "Локальный профиль разработки")

    def test_health_endpoint(self):
        response = self.client.get(reverse("system:health"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["database"])
        self.assertIn(payload["database_vendor"], {"sqlite", "postgresql"})
        self.assertIn(payload["profile"], {"development", "postgresql"})
        self.assertIn("local_server_time", payload)
        self.assertIn("time_zone", payload)


class UxPlatformRepairV11SourceContractTests(SimpleTestCase):
    def test_opj_width_profiles_have_distinct_geometry_and_persistence_chain(self):
        shared_css = read_source("src/static/system/ux_platform_compositions.css")
        lifecycle_css = read_source(
            "src/static/operational_log/opj_lifecycle_acceptance_repair.css"
        )
        workspace_js = read_source("src/static/operational_log/draft_workspace.js")

        self.assertIn('data-page-width="standard"', shared_css)
        self.assertIn("width:min(100%,72rem)", shared_css)
        self.assertIn('data-page-width="wide"', lifecycle_css)
        self.assertIn("width: min(100%, 1680px) !important", lifecycle_css)
        self.assertIn('data-page-width="full"', lifecycle_css)
        self.assertIn("width: 100% !important", lifecycle_css)
        self.assertIn('["standard", "wide", "full"].includes(normalized)', workspace_js)
        self.assertIn("workspace.dataset.pageWidth = pageWidthPreference", workspace_js)
        self.assertIn('"journal_width"', workspace_js)
        self.assertIn("pageWidthPreference.toUpperCase()", workspace_js)
        self.assertIn("payload.journal_width", workspace_js)

    def test_personnel_contours_use_server_resolvable_destinations(self):
        directory = read_source("src/templates/organizations/directory.html")
        authority = read_source("src/templates/organizations/authority_registry.html")

        self.assertNotIn("authority_registry' %}#dispatch", directory)
        self.assertNotIn("authority_registry' %}#related", directory)
        self.assertIn("view=dispatch", directory)
        self.assertIn("view=related&amp;scope=grid", directory)
        self.assertIn("view=related&amp;scope=site", directory)
        self.assertIn("view=related&amp;scope=commercial", directory)
        self.assertIn('data-initial-view="{{ initial_view }}"', authority)
        self.assertIn('request.GET.view|default:"matrix"', authority)
        self.assertIn(
            'data-authority-panel="dispatch"'
            "{% if initial_view != 'dispatch' %} hidden",
            authority,
        )
        self.assertIn(
            'data-authority-panel="related"'
            "{% if initial_view != 'related' %} hidden",
            authority,
        )

    def test_personnel_grid_geometry_has_intentional_stretch_ownership(self):
        css = read_source("src/static/organizations/personnel_directory.css")

        self.assertIn(".personnel-contours {", css)
        self.assertIn("align-items:stretch", css)
        self.assertIn("grid-template-rows:auto minmax(0,1fr) auto", css)
        self.assertIn(".personnel-recent-grid {", css)
        self.assertIn("align-items:start", css)
        self.assertIn(".personnel-directory-relation-heading", css)
        self.assertIn("padding:var(--theme-space-2) var(--theme-space-4)", css)
        self.assertIn(".personnel-service-relations", css)
        self.assertIn(".personnel-service-relation", css)

    def test_authority_controls_headers_and_audit_have_semantic_contracts(self):
        template = read_source("src/templates/organizations/authority_registry.html")
        css = read_source("src/static/organizations/personnel_authority_matrix.css")
        js = read_source("src/static/organizations/personnel_authority_matrix.js")

        self.assertIn('data-expand-all><svg', template)
        self.assertNotIn("#icon-add", template)
        self.assertIn("data-expand-all-label", template)
        self.assertIn("Свернуть всё", template)
        self.assertIn("collapsed.size === 0", js)
        self.assertIn("Развернуть всё", js)
        self.assertIn("Свернуть всё", js)
        identity_header_selector = (
            ".authority-right-header > "
            ":is(.matrix-sticky-name,.matrix-sticky-position,.matrix-sticky-qualification)"
        )
        self.assertIn(identity_header_selector, css)
        self.assertIn("vertical-align:middle", css)
        self.assertIn('data-active-view="{{ initial_view }}"', template)
        self.assertIn('authority-toolbar[data-active-view="checks"]', css)
        self.assertIn("toolbar.dataset.activeView = activeView", js)
        self.assertIn("authority-evaluation-header", template)
        for label in (
            "Дата и время",
            "Сотрудник",
            "Контекст",
            "Проверяемое действие",
            "Объект",
            "Результат",
        ):
            self.assertIn(label, template)
        self.assertIn("authority_action_label", template)
        self.assertIn("authority_action_technical_label", template)
        self.assertIn("item.subject_type }} · {{ item.subject_id", template)
        self.assertIn(".authority-evaluation-row[hidden] { display:none; }", css)
        self.assertIn("@media (max-width:56.25rem)", css)

    def test_human_text_and_import_profiles_do_not_use_arbitrary_word_breaking(self):
        shared_css = read_source("src/static/system/ux_platform_compositions.css")
        imports = read_source("src/templates/imports/list.html")

        readable_rule = shared_css.split(
            ".ux-profile-strip .data-profile-chip strong,.ux-readable-value",
            maxsplit=1,
        )[1].split("}", maxsplit=1)[0]
        self.assertIn("overflow-wrap:break-word", readable_rule)
        self.assertNotIn("overflow-wrap:anywhere", readable_rule)
        technical_rule = shared_css.split(
            ".ux-technical,.ux-technical-chip",
            maxsplit=1,
        )[1].split("}", maxsplit=1)[0]
        self.assertIn("overflow-wrap:anywhere", technical_rule)
        self.assertIn("import-profile-grid", imports)
        self.assertIn("import-profile-card", imports)
        self.assertIn("Уровень данных", imports)
        self.assertIn("Экспорт", imports)
        self.assertIn("mapping_template_count", imports)
        self.assertIn("import-safety-notice", imports)
        self.assertIn("import-header-actions__primary", imports)
        self.assertIn("import-header-nav", imports)

    def test_management_filter_and_operational_document_metadata_are_compact(self):
        dispatching = read_source("src/templates/dispatching/registry.html")
        opdocs = read_source("src/templates/operational_documents/registry.html")

        self.assertIn(
            "ux-compact-filter-row disclosure-body equipment-filter-form",
            dispatching,
        )
        self.assertNotIn(
            "ux-form-grid disclosure-body equipment-filter-form",
            dispatching,
        )
        self.assertIn("opdoc-record-meta__technical", opdocs)
        self.assertIn("Техническая запись", opdocs)
        self.assertNotIn(
            'class="da-status-chip is-warning">Техническая запись',
            opdocs,
        )
        self.assertIn("not record.is_source_bound", opdocs)
