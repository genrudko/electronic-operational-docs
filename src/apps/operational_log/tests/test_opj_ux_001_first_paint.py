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

        self.assertIn('data-direction-a-shell', shared_base)
        for forbidden in (
            "buildGeneratedShell",
            "document.body.insertBefore",
            "content.append(main)",
            "data-direction-a-generated",
        ):
            self.assertNotIn(forbidden, shell_script)
