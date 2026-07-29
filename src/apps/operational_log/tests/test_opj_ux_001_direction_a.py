from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase
from django.urls import reverse

from .base import OperationalLogTestCase

ROOT = Path(__file__).resolve().parents[3]
ASSET_REVISION = "opjux00102"


class OpjDirectionAStaticContractTests(SimpleTestCase):
    def source(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_base_loads_one_shared_layer_and_one_specialised_enhancer(self) -> None:
        base = self.source("templates/base.html")
        for asset in (
            "system/direction_a.css",
            "system/direction_a.js",
            "operational_log/opj_ux_001.css",
            "operational_log/opj_ux_001.js",
        ):
            self.assertIn(asset, base)
        self.assertEqual(base.count(f"?v={ASSET_REVISION}"), 4)
        for obsolete in (
            "direction_a_shell.css",
            "direction_a_shell_repair1.css",
            "opj_ux_001_repair1.css",
            "opj_ux_001_repair1.js",
        ):
            self.assertNotIn(obsolete, base)

    def test_shared_layer_contains_real_cross_module_primitives(self) -> None:
        css = self.source("static/system/direction_a.css")
        for marker in (
            "--da-canvas",
            ".da-shell",
            ".da-sidebar",
            ".da-topbar",
            ".da-page-header",
            ".da-button",
            ".da-field",
            ".da-segmented",
            ".da-panel",
            ".da-status",
            ".da-alert",
            ".da-table",
            ".da-overlay",
            ".da-hierarchy",
            "body.da-nav-open",
            "@media (max-width: 980px)",
        ):
            self.assertIn(marker, css)
        for forbidden in ("defect-da-", "opj-", "equipment-defect"):
            self.assertNotIn(forbidden, css)

    def test_shared_shell_supports_home_opj_and_accepted_defect_markup(self) -> None:
        script = self.source("static/system/direction_a.js")
        for marker in (
            'path.startsWith("/operations/journal/")',
            'path.startsWith("/operations/defects/")',
            'path === "/"',
            "data-direction-a-shell",
            "buildGeneratedShell",
            "adoptServerRenderedShell",
            "defect-da-shell",
            "da-shell",
            "da-page-header",
            "da-button",
            "da-status",
        ):
            self.assertIn(marker, script)
        self.assertNotIn("register_entry(", script)

    def test_defect_and_operational_journal_are_both_shared_consumers(self) -> None:
        defect_sidebar = self.source(
            "templates/equipment_defects/_direction_a_sidebar.html"
        )
        defect_header = self.source(
            "templates/equipment_defects/_registry_repair2_header.html"
        )
        opj_registry = self.source("templates/operational_log/registry.html")
        home = self.source("templates/system/home.html")
        for marker in (
            "da-sidebar",
            "da-brand",
            "da-navigation",
            "da-user",
        ):
            self.assertIn(marker, defect_sidebar)
        for marker in (
            "da-page-header",
            "da-button",
            "da-segmented",
            "da-field",
            "da-panel-flat",
        ):
            self.assertIn(marker, defect_header)
        for marker in ("da-page-header", "da-alert", "da-panel", "da-table"):
            self.assertIn(marker, opj_registry)
        for marker in ("da-page-header", "da-alert", "da-card", "da-status"):
            self.assertIn(marker, home)

    def test_opj_enhancer_keeps_only_specialised_workspace_behaviour(self) -> None:
        script = self.source("static/operational_log/opj_ux_001.js")
        for marker in (
            "Зарегистрированный журнал",
            "Рабочий черновик",
            'parsed.querySelector(".approved-journal-table")',
            "draft-semantic-reference-catalog",
            "opj-reference-tree",
            "MutationObserver",
            "applySharedPrimitiveClasses",
        ):
            self.assertIn(marker, script)
        for forbidden in (
            "buildSidebar",
            "buildTopbar",
            "data-opj-direction-a-shell",
            "register_entry(",
            "/shift/register/",
            "/shift/handover/",
            "/shift/close/",
            "Подписать чистовик",
        ):
            self.assertNotIn(forbidden, script)

    def test_opj_styles_keep_only_journal_specific_geometry(self) -> None:
        css = self.source("static/operational_log/opj_ux_001.css")
        for marker in (
            ".opj-registered-context",
            ".opj-work-boundary",
            ".approved-journal-shell",
            ".paged-draft-workspace",
            ".draft-command-bar",
            ".opj-reference-tree-site",
            "@media (max-width: 720px)",
        ):
            self.assertIn(marker, css)
        for forbidden in (
            ".eod-da-shell",
            ".eod-da-sidebar",
            ".eod-da-topbar",
            ".defect-da-shell",
        ):
            self.assertNotIn(forbidden, css)


class OpjDirectionAWorkspaceViewTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(
            get_user_model().objects.get(username="operator.demo")
        )

    def test_workspace_loads_shared_assets_without_fake_lifecycle(self) -> None:
        response = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(response.status_code, 200)
        for asset in (
            "system/direction_a.css",
            "system/direction_a.js",
            "operational_log/opj_ux_001.css",
            "operational_log/opj_ux_001.js",
        ):
            self.assertContains(response, asset)
        for forbidden in (
            "Подготовить смену к сдаче",
            "Передать смену",
            "Принять смену",
            "Закрыть смену",
        ):
            self.assertNotContains(response, forbidden)
