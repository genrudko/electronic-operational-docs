from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalFinalActionPrintRepairTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_actions_use_one_page_owned_controller_with_visible_coordinates(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        detail = self.source("templates/operational_log/detail.html")
        javascript = self.source("static/operational_log/opj_clean_journal.js")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertNotIn("opj_acceptance_action_repair.js", partial)
        self.assertIn("opj_clean_journal.js", detail)
        self.assertIn("actionPortal = source.cloneNode(true)", javascript)
        self.assertIn("document.body.append(actionPortal)", javascript)
        self.assertIn("overlay.style.left", javascript)
        self.assertIn("overlay.style.top", javascript)
        self.assertIn(".opj-action-portal", css)
        self.assertIn("right: auto !important", css)
        self.assertIn("bottom: auto !important", css)
        self.assertNotIn("inset: auto !important", css)

    def test_cleared_marker_is_crossed_across_the_complete_badge(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        for source in (partial, css):
            self.assertIn("top: 1px !important", source)
            self.assertIn("right: 1px !important", source)
            self.assertIn("bottom: 1px !important", source)
            self.assertIn("left: 1px !important", source)
            self.assertIn("width: auto !important", source)
            self.assertIn("height: auto !important", source)
            self.assertIn("transform: none !important", source)
            self.assertIn("width: 60px", source)
            self.assertIn("rotate(52deg)", source)
            self.assertIn("rotate(-52deg)", source)
        self.assertNotIn("width: calc(100% - 2px) !important", css)

    def test_print_visas_remain_a_native_table_cell(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        printed = self.source("templates/operational_log/print.html")

        self.assertIn(
            ".approved-journal-print-table td.journal-print-markers",
            partial,
        )
        self.assertIn("display: table-cell !important", partial)
        self.assertIn("overflow: hidden !important", partial)
        self.assertIn(
            "td.journal-print-markers > .opj-normative-marker",
            partial,
        )
        self.assertIn('td class="journal-print-markers"', printed)
