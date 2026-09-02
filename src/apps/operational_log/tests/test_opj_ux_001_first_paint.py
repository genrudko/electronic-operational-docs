from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OpjDirectionAFirstPaintTests(SimpleTestCase):
    def source(self, relative_path: str) -> str:
        return (ROOT / relative_path).read_text(encoding="utf-8")

    def test_shared_and_operational_screens_activate_direction_a_in_server_html(
        self,
    ) -> None:
        base = self.source("templates/base.html")
        wrapper = self.source("templates/shared/direction_a/base.html")

        self.assertIn('class="ux-platform da-active {% block body_class %}', base)
        self.assertIn('{% extends "base.html" %}', wrapper)
        for relative_path in (
            "templates/operational_log/registry.html",
            "templates/operational_log/detail.html",
            "templates/operational_log/shift_workspace.html",
        ):
            with self.subTest(relative_path=relative_path):
                template = self.source(relative_path)
                self.assertIn('{% extends "shared/direction_a/base.html" %}', template)

    def test_first_paint_contract_does_not_restore_generated_shell(self) -> None:
        base = self.source("templates/base.html")
        shell_script = self.source("static/system/direction_a.js")

        self.assertIn("data-direction-a-shell", base)
        for forbidden in (
            "buildGeneratedShell",
            "document.body.insertBefore",
            "content.append(main)",
            "data-direction-a-generated",
        ):
            self.assertNotIn(forbidden, shell_script)

    def test_shared_shell_templates_have_one_class_and_data_contract(self) -> None:
        shared_shell = "\n".join(
            (
                self.source("templates/base.html"),
                self.source("templates/shared/direction_a/_sidebar.html"),
                self.source("templates/shared/direction_a/_topbar.html"),
            )
        )

        for marker in (
            'class="da-shell"',
            'class="da-sidebar"',
            'class="da-topbar"',
            "data-direction-a-shell",
            "data-direction-a-sidebar",
            "data-direction-a-topbar",
        ):
            self.assertIn(marker, shared_shell)
        self.assertNotIn("defect-da-", shared_shell)
        self.assertNotIn("data-defect-shell-", shared_shell)

    def test_final_shared_shell_layer_owns_presentation_and_geometry(self) -> None:
        base = self.source("templates/base.html")
        platform_css = self.source("static/system/ux_platform.css")

        platform_layer = base.index("system/ux_platform.css")
        opj_layer = base.index("operational_log/opj_ux_001.css")
        extra_head = base.index("{% block extra_head %}")
        self.assertLess(platform_layer, opj_layer)
        self.assertLess(platform_layer, extra_head)
        for marker in (
            "body.ux-platform",
            "font-family: var(--theme-font-ui)",
            ".da-shell",
            ".da-sidebar",
            ".da-topbar",
            ".da-navigation > a",
            ".da-user-avatar",
            ".da-page",
            "@media (max-width: 980px)",
        ):
            self.assertIn(marker, platform_css)
        self.assertNotIn("direction_a_shell_final.css", base)

    def test_opj_specialised_layer_keeps_workspace_geometry_and_shared_tokens(self) -> None:
        opj_css = self.source("static/operational_log/opj_ux_001.css")
        controls_css = self.source("static/operational_log/opj_workspace_controls.css")

        for marker in (
            "body.opj-direction-a",
            "--opj-editor-surface: var(--theme-surface-document)",
            "--opj-header-surface: var(--theme-table-header)",
            ".opj-editor-container",
            ".opj-ledger-surface",
        ):
            self.assertIn(marker, opj_css)
        self.assertIn('data-view-mode="spread"', controls_css)
        for source in (opj_css, controls_css):
            self.assertNotIn("zoom:", source)
            self.assertNotIn("transform: scale(", source)

    def test_defect_feature_script_delegates_shared_shell_interaction(self) -> None:
        defect_script = self.source(
            "static/equipment_defects/ux_foundation_repair2.js"
        )
        self.assertIn(
            'if (document.querySelector("[data-direction-a-shell]")) return;',
            defect_script,
        )
