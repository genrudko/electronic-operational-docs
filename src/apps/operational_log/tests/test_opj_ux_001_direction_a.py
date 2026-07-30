from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase
from django.urls import reverse

from .base import OperationalLogTestCase

ROOT = Path(__file__).resolve().parents[3]
ASSET_REVISION = "opjux00103"


class OpjPresentationRewriteStaticContractTests(SimpleTestCase):
    def source(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_base_exposes_server_rendered_shell_boundary(self) -> None:
        base = self.source("templates/base.html")
        for marker in (
            "{% block body_class %}",
            "{% block body %}",
            "system/direction_a.css",
            "system/direction_a.js",
            "operational_log/opj_ux_001.css",
            "operational_log/opj_ux_001.js",
        ):
            self.assertIn(marker, base)
        self.assertEqual(base.count(f"?v={ASSET_REVISION}"), 4)

    def test_shared_shell_is_one_server_rendered_composition(self) -> None:
        shared_base = self.source("templates/shared/direction_a/base.html")
        sidebar = self.source("templates/shared/direction_a/_sidebar.html")
        topbar = self.source("templates/shared/direction_a/_topbar.html")

        for marker in (
            "data-direction-a-shell",
            "shared/direction_a/_sidebar.html",
            "shared/direction_a/_topbar.html",
            'class="da-stage"',
            'class="da-page"',
        ):
            self.assertIn(marker, shared_base)
        for marker in (
            "data-direction-a-sidebar",
            'class="da-navigation"',
            "Оперативный журнал",
            "Журнал дефектов",
        ):
            self.assertIn(marker, sidebar)
        for marker in (
            "data-direction-a-topbar",
            "data-direction-a-toggle",
            'class="da-workplace"',
        ):
            self.assertIn(marker, topbar)

        shared_shell = "\n".join((shared_base, sidebar, topbar))
        self.assertNotIn("defect-da-", shared_shell)
        self.assertNotIn("data-defect-shell-", shared_shell)

    def test_shell_javascript_never_constructs_or_moves_application_layout(self) -> None:
        script = self.source("static/system/direction_a.js")
        for marker in (
            "[data-direction-a-shell]",
            "[data-direction-a-sidebar]",
            "[data-direction-a-scrim]",
            "[data-direction-a-toggle]",
            'document.body.classList.add("da-active")',
        ):
            self.assertIn(marker, script)
        for forbidden in (
            "buildGeneratedShell",
            "buildSidebar",
            "buildTopbar",
            "document.body.insertBefore",
            "content.append(main)",
            "data-direction-a-generated",
        ):
            self.assertNotIn(forbidden, script)

    def test_defect_and_opj_screens_extend_the_same_shared_base(self) -> None:
        for relative_path in (
            "templates/equipment_defects/registry.html",
            "templates/equipment_defects/detail.html",
            "templates/operational_log/registry.html",
            "templates/operational_log/detail.html",
            "templates/operational_log/shift_workspace.html",
        ):
            self.assertIn(
                '{% extends "shared/direction_a/base.html" %}',
                self.source(relative_path),
                relative_path,
            )

    def test_shift_workspace_is_new_single_page_composition(self) -> None:
        workspace = self.source("templates/operational_log/shift_workspace.html")
        for marker in (
            "data-draft-workspace",
            'data-opj-presentation-mode="single"',
            "operational_log/_shift_workspace_toolbar.html",
            "operational_log/_shift_workspace_rows.html",
            "operational_log/_shift_workspace_drawer.html",
            "operational_log/_shift_workspace_overlays.html",
            'data-page-shell="left"',
            'data-page-body="left"',
            'data-page-shell="right"',
            "draft_editor.js",
            "draft_workspace.js",
            "draft_reference_navigation.js",
        ):
            self.assertIn(marker, workspace)
        for forbidden in (
            "paged-draft-workspace",
            "large-book-workspace",
            'class="draft-book"',
            "draft-paper-stage",
            'data-view-mode="spread"',
            "Разворот",
            "CSS zoom",
        ):
            self.assertNotIn(forbidden, workspace)

    def test_editor_domain_and_concurrency_hooks_are_preserved(self) -> None:
        rows = self.source("templates/operational_log/_shift_workspace_rows.html")
        for marker in (
            "operational_log:autosave_draft",
            'name="expected_version"',
            "data-draft-version",
            'name="editor_schema_version"',
            "data-editor-schema-version",
            'name="editor_payload"',
            "data-editor-payload",
            "data-rich-editor-host",
            "operational_log:move_draft",
            "operational_log:remove_draft",
            "operational_log:restore_draft",
            "data-inline-undo",
        ):
            self.assertIn(marker, rows)

        toolbar = self.source("templates/operational_log/_shift_workspace_toolbar.html")
        for command in (
            "bold",
            "italic",
            "underline",
            "strike",
            "text_red",
            "text_blue",
            "clear",
            "bullet_list",
            "ordered_list",
            "undo",
            "redo",
        ):
            self.assertIn(f'data-editor-command="{command}"', toolbar)
        for marker in (
            "data-entry-kind-trigger",
            "data-reference-trigger",
            "data-auto-reference-toggle",
            "data-auto-reference-scan",
            "data-normative-trigger",
            "data-simplified-time-toggle",
        ):
            self.assertIn(marker, toolbar)

    def test_semantic_and_normative_presentations_keep_existing_contracts(self) -> None:
        overlays = self.source("templates/operational_log/_shift_workspace_overlays.html")
        for marker in (
            "data-reference-picker",
            'data-reference-kind-option="equipment"',
            'data-reference-kind-option="document"',
            'data-reference-kind-option="person"',
            'data-reference-kind-option="related_entry"',
            'data-reference-kind-option="event_time"',
            'data-normative-action="emergency"',
            'data-normative-action="zn_on"',
            'data-normative-action="pz_install"',
            'data-normative-action="zn_off"',
            'data-normative-action="pz_remove"',
            "draft-semantic-reference-catalog",
        ):
            self.assertIn(marker, overlays)

    def test_opj_enhancer_only_adapts_existing_server_markup(self) -> None:
        script = self.source("static/operational_log/opj_ux_001.js")
        for marker in (
            "forceSinglePagePresentation",
            'window.localStorage.setItem("eod-draft-view-mode", "single")',
            'parsed.querySelector(".approved-journal-table")',
            "draft-semantic-reference-catalog",
            "opj-reference-tree",
            "MutationObserver",
            "loadRegisteredContext",
        ):
            self.assertIn(marker, script)
        for forbidden in (
            "buildSidebar",
            "buildTopbar",
            "buildGeneratedShell",
            "register_entry(",
            "/shift/register/",
            "/shift/handover/",
            "/shift/close/",
            "Подписать чистовик",
        ):
            self.assertNotIn(forbidden, script)

    def test_new_css_has_normal_scale_and_responsive_workspace(self) -> None:
        css = self.source("static/operational_log/opj_ux_001.css")
        for marker in (
            ".opj-workspace-header",
            ".opj-toolbar",
            ".opj-editor-toolbar",
            ".opj-editor-container",
            ".opj-ledger-surface",
            ".opj-workspace .draft-ledger-form",
            ".opj-registered-context",
            ".opj-reference-tree-site",
            "@media (max-width: 980px)",
            "@media (max-width: 720px)",
        ):
            self.assertIn(marker, css)
        for forbidden in (
            "zoom:",
            "transform: scale(",
            ".eod-da-shell",
            ".eod-da-sidebar",
            ".eod-da-topbar",
            ".opj-da-",
        ):
            self.assertNotIn(forbidden, css)


class OpjPresentationRewriteViewTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(
            get_user_model().objects.get(username="operator.demo")
        )

    def test_registry_and_workspace_render_the_server_shell_immediately(self) -> None:
        for route_name, args in (
            ("operational_log:registry", ()),
            ("operational_log:detail", (self.journal.pk,)),
            ("operational_log:shift_workspace", (self.journal.pk,)),
        ):
            response = self.client.get(reverse(route_name, args=args))
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, "data-direction-a-shell", count=1)
            self.assertContains(response, "data-direction-a-sidebar", count=1)
            self.assertContains(response, "data-direction-a-topbar", count=1)
            self.assertNotContains(response, "data-direction-a-generated")

    def test_workspace_keeps_functional_contracts_without_fake_lifecycle(self) -> None:
        response = self.client.get(
            reverse("operational_log:shift_workspace", args=(self.journal.pk,))
        )
        self.assertEqual(response.status_code, 200)
        for marker in (
            "data-draft-workspace",
            'data-opj-presentation-mode="single"',
            "draft_editor.js",
            "draft_workspace.js",
            "draft_reference_navigation.js",
        ):
            self.assertContains(response, marker)
        for forbidden in (
            "Подготовить смену к сдаче",
            "Передать смену",
            "Принять смену",
            "Закрыть смену",
            "Разворот",
        ):
            self.assertNotContains(response, forbidden)
