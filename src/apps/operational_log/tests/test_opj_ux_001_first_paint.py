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
        for relative_path in (
            "templates/shared/direction_a/base.html",
            "templates/operational_log/registry.html",
            "templates/operational_log/detail.html",
            "templates/operational_log/shift_workspace.html",
        ):
            with self.subTest(relative_path=relative_path):
                template = self.source(relative_path)
                self.assertIn("{% block body_class %}", template)
                self.assertIn("da-active", template)

    def test_first_paint_contract_does_not_restore_generated_shell(self) -> None:
        shared_base = self.source("templates/shared/direction_a/base.html")
        shell_script = self.source("static/system/direction_a.js")

        self.assertIn("data-direction-a-shell", shared_base)
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
                self.source("templates/shared/direction_a/base.html"),
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
        shell_css = self.source("static/system/direction_a_shell_final.css")

        extra_head = base.index("{% block extra_head %}{% endblock %}")
        final_layer = base.index("system/direction_a_shell_final.css")
        self.assertLess(extra_head, final_layer)
        self.assertIn("direction_a_shell_final.css' %}?v=opjux00110", base)
        for marker in (
            "html:has(body.da-active)",
            "scrollbar-gutter: stable",
            "font-family: Inter",
            "font-size: 14px",
            "body.da-active .da-shell",
            "body.da-active .da-sidebar",
            "body.da-active .da-topbar",
            "body.da-active .da-brand-copy strong",
            "body.da-active .da-nav-group-title",
            "body.da-active .da-user strong",
            "body.da-active .da-workplace strong",
            "body.da-active .da-topbar-value",
            "body.da-active .visually-hidden",
            "clip-path: inset(50%)",
            "body.da-active .da-page",
            "body.da-active .da-page > main",
            "max-width: var(--da-page-max)",
            "padding: 0",
            "-webkit-line-clamp: 2",
            "@media (max-width: 1320px) and (min-width: 981px)",
            "--da-sidebar-width: 232px",
            "@media (max-width: 980px)",
            "width: min(310px, 88vw)",
            "body.da-active.da-nav-open .da-sidebar",
            "body.da-active .da-menu-button",
            "padding: var(--da-page-padding-top-mobile) 14px 30px",
        ):
            self.assertIn(marker, shell_css)

    def test_opj_compact_start_and_dark_theme_cover_the_shared_shell(self) -> None:
        shell_css = self.source("static/system/direction_a_shell_final.css")
        for marker in (
            "body.da-active.opj-workspace-page",
            "--da-page-padding-top: 4px",
            "--da-page-padding-top-mobile: 8px",
            'html[data-theme="dark"] body.da-active.opj-workspace-page',
            "color-scheme: dark",
            ".da-sidebar",
            ".da-topbar",
            ".da-navigation > a",
            ".da-nav-child.is-active",
            ".da-user-avatar",
            ".da-button.is-secondary",
            ".opj-meta-item.is-success",
            ".opj-editor-container",
            'data-view-mode="spread"',
            "rgba(0, 0, 0, 0.34)",
        ):
            self.assertIn(marker, shell_css)

    def test_defect_feature_script_delegates_shared_shell_interaction(self) -> None:
        defect_script = self.source(
            "static/equipment_defects/ux_foundation_repair2.js"
        )
        self.assertIn(
            'if (document.querySelector("[data-direction-a-shell]")) return;',
            defect_script,
        )
