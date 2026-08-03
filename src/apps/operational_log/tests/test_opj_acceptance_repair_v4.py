from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalFourthAcceptanceRepairSourceTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_marker_runtime_does_not_renumber_or_use_joined_source_text(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")

        self.assertNotIn("function renumber", partial)
        self.assertNotIn("marker.source_text", partial)
        self.assertNotIn("Исходных отметок", partial)
        self.assertIn(".opj-rich-segment.is-normative-open", partial)
        self.assertIn(".opj-rich-segment.is-normative-close", partial)
        self.assertIn("data-marker-source-list", partial)
        self.assertIn("item.textContent = value", partial)

    def test_marker_tooltip_is_a_viewport_portal(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("document.body.append(popover)", partial)
        self.assertIn("window.innerWidth - box.width - margin", partial)
        self.assertIn("window.innerHeight - box.height - margin", partial)
        self.assertIn(".opj-marker-popover.is-floating", css)
        self.assertIn("position: fixed !important", css)
        self.assertIn("max-height: min(440px, calc(100vh - 24px))", css)
        self.assertIn('font-family: var(--font-interface, "Onest Variable"', css)

    def test_final_state_is_hidden_before_first_paint_without_client_renumber(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn(
            ".approved-journal-table:not(.is-opj-chronology-ready) tbody",
            css,
        )
        self.assertIn('classList.add("is-opj-chronology-ready")', partial)
        self.assertNotIn("target.textContent = `№", partial)

    def test_emergency_outline_matches_compact_accepted_oval(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("inset: -0.08rem -0.20rem !important", css)
        self.assertIn("border: 2px solid", css)
        self.assertIn("border-radius: 999px !important", css)
        self.assertIn("transform: none !important", css)

    def test_removal_marker_remains_visible_and_only_prior_install_is_crossed(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertNotIn("marker.hidden", partial)
        self.assertIn('if (source) source.classList.add("is-cleared")', partial)
        self.assertIn(
            ".draft-normative-marker.is-cleared > .draft-normative-marker-cross",
            css,
        )
