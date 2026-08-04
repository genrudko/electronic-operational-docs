from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalFinalActionPrintRepairTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_actions_runtime_is_cache_busted_and_moves_real_menu(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        javascript = self.source(
            "static/operational_log/opj_acceptance_action_repair.js"
        )

        self.assertIn("opj-acceptance-action-repair-00611", partial)
        self.assertIn("opjlifecycle00611", partial)
        self.assertNotIn("opj-acceptance-action-repair-00609", partial)
        self.assertNotIn("opjlifecycle00609", partial)
        self.assertIn("document.body.append(menu)", javascript)
        self.assertIn("root.append(menu)", javascript)
        self.assertIn("delete menu.dataset.actionRepairPortal", javascript)
        self.assertIn('node.closest("[data-entry-actions]")', javascript)
        self.assertIn("event.stopImmediatePropagation()", javascript)
        self.assertIn("removeLegacyPortals", javascript)
        self.assertNotIn("actionPortal = source.cloneNode(true)", javascript)

    def test_cleared_marker_is_crossed_across_the_complete_badge(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")

        self.assertIn("top: 1px !important", partial)
        self.assertIn("left: 1px !important", partial)
        self.assertIn("width: calc(100% - 2px) !important", partial)
        self.assertIn("height: calc(100% - 2px) !important", partial)
        self.assertIn("width: 60px", partial)
        self.assertIn("rotate(52deg)", partial)
        self.assertIn("rotate(-52deg)", partial)
        self.assertNotIn("top: 12px !important", partial)
        self.assertNotIn("width: 31px", partial)

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
