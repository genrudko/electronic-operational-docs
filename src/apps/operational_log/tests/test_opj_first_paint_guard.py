from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalFirstPaintGuardTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_shift_template_hides_workspace_in_head_until_final_pages_exist(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")

        self.assertIn(
            "[data-draft-workspace]:not(.is-opj-first-paint-ready)",
            template,
        )
        self.assertIn("opj_first_paint_guard.js", template)
        self.assertIn("opjlifecycle00604", template)
        self.assertLess(
            template.index("opj_first_paint_guard.js"),
            template.index("{% block content %}"),
        )

    def test_guard_reveals_only_materialized_single_or_spread_page(self) -> None:
        script = self.source(
            "static/operational_log/opj_first_paint_guard.js"
        )

        self.assertIn('querySelectorAll("[data-page-body]")', script)
        self.assertIn("body.childElementCount > 0", script)
        self.assertIn('classList.add("is-opj-first-paint-ready")', script)
        self.assertIn("MutationObserver(reveal)", script)
        self.assertIn("observer.observe(workspace", script)
