from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalFirstPaintGuardTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_render_blocking_repair_css_neutralizes_stale_hide_rule(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("opj_lifecycle_acceptance_repair.css", template)
        self.assertLess(
            template.index("opj_lifecycle_acceptance_repair.css"),
            template.index("{% block content %}"),
        )
        self.assertIn(
            "html body.opj-workspace-page main.opj-shift-main "
            "[data-draft-workspace]",
            css,
        )
        self.assertIn("visibility: visible !important", css)

    def test_compatibility_guard_reveals_synchronously(self) -> None:
        script = self.source(
            "static/operational_log/opj_first_paint_guard.js"
        )

        self.assertIn('classList.add("is-opj-first-paint-ready")', script)
        self.assertIn('dataset.opjFirstPaintGuard = "disabled"', script)
        self.assertNotIn("MutationObserver", script)
        self.assertNotIn("requestAnimationFrame", script)
        self.assertNotIn("setTimeout", script)
        self.assertNotIn("childElementCount", script)
