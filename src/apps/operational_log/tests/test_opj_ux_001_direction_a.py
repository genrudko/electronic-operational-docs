from __future__ import annotations

from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase
from django.urls import reverse

from .base import OperationalLogTestCase


ROOT = Path(__file__).resolve().parents[3]
ASSET_REVISION = "opjux00101"


class OpjDirectionAStaticContractTests(SimpleTestCase):
    def source(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_base_loads_shared_shell_and_opj_enhancer(self) -> None:
        base = self.source("templates/base.html")
        for asset in (
            "system/direction_a_shell.css",
            "operational_log/opj_ux_001.css",
            "operational_log/opj_ux_001.js",
        ):
            self.assertIn(asset, base)
        self.assertEqual(base.count(f"?v={ASSET_REVISION}"), 3)

    def test_shared_shell_is_light_responsive_and_reusable(self) -> None:
        css = self.source("static/system/direction_a_shell.css")
        for marker in (
            "--eod-da-bg",
            ".eod-da-shell",
            ".eod-da-sidebar",
            ".eod-da-topbar",
            ".eod-da-navigation",
            "body.eod-da-nav-open",
            "@media (max-width: 980px)",
        ):
            self.assertIn(marker, css)
        self.assertNotIn("equipment-defect", css)
        self.assertNotIn("defect-da-", css)

    def test_opj_enhancer_preserves_specialised_workspace_boundary(self) -> None:
        script = self.source("static/operational_log/opj_ux_001.js")
        for marker in (
            'path.startsWith("/operations/journal/")',
            "data-opj-direction-a-shell",
            "Зарегистрированный журнал",
            "Рабочий черновик текущей смены",
            'parsed.querySelector(".approved-journal-table")',
            "Записи показаны в хронологическом порядке",
            "draft-semantic-reference-catalog",
            "opj-reference-tree",
            "MutationObserver",
        ):
            self.assertIn(marker, script)
        for forbidden in (
            "register_entry(",
            "/shift/register/",
            "/shift/handover/",
            "/shift/close/",
            "Подписать чистовик",
        ):
            self.assertNotIn(forbidden, script)

    def test_opj_styles_keep_registered_and_draft_layers_distinct(self) -> None:
        css = self.source("static/operational_log/opj_ux_001.css")
        for marker in (
            ".opj-registered-context",
            ".opj-work-boundary",
            ".paged-draft-workspace",
            ".draft-command-bar",
            ".opj-reference-tree-site",
            "@media (max-width: 720px)",
        ):
            self.assertIn(marker, css)


class OpjDirectionAWorkspaceViewTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.client.force_login(
            get_user_model().objects.get(username="operator.demo")
        )

    def test_workspace_loads_direction_a_assets_without_fake_lifecycle(self) -> None:
        response = self.client.get(
            reverse(
                "operational_log:shift_workspace",
                args=(self.journal.pk,),
            )
        )
        self.assertEqual(response.status_code, 200)
        for asset in (
            "system/direction_a_shell.css",
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
