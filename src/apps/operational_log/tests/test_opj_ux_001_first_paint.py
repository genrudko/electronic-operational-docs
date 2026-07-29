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

    def test_final_shared_shell_layer_owns_desktop_and_mobile_geometry(self) -> None:
        base = self.source("templates/base.html")
        shell_css = self.source("static/system/direction_a_shell_final.css")

        extra_head = base.index("{% block extra_head %}{% endblock %}")
        final_layer = base.index("system/direction_a_shell_final.css")
        self.assertLess(extra_head, final_layer)
        for marker in (
            "body.da-active .da-shell",
            "body.da-active .da-sidebar",
            "body.da-active .da-topbar",
            "body.da-active .da-page",
            "body.da-active .da-page > main",
            "max-width: var(--da-page-max)",
            "@media (max-width: 1320px) and (min-width: 981px)",
            "--da-sidebar-width: 232px",
            "@media (max-width: 980px)",
            "width: min(310px, 88vw)",
            "body.da-active.da-nav-open .da-sidebar",
            "body.da-active .da-menu-button",
            "padding: 18px 14px 30px",
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
