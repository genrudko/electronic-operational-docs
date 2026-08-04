from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalFifthAcceptanceRepairSourceTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_marker_runtime_uses_exact_underlined_fragments(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")

        self.assertNotIn("function renumber", partial)
        self.assertNotIn("marker.source_text", partial)
        self.assertNotIn("Исходных отметок", partial)
        self.assertIn("function exactUnderlinedFragments", partial)
        self.assertIn(".opj-rich-segment.is-normative-open", partial)
        self.assertIn(".opj-rich-segment.is-normative-close", partial)
        self.assertIn("item.textContent = value", partial)
        self.assertIn("values.indexOf(value) === index", partial)

    def test_marker_tooltip_is_a_viewport_portal_with_project_font(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("document.body.append(popover)", partial)
        self.assertIn("window.innerWidth - box.width - margin", partial)
        self.assertIn("window.innerHeight - box.height - margin", partial)
        self.assertIn(".opj-marker-popover.is-floating", css)
        self.assertIn("position: fixed !important", css)
        self.assertIn("max-height: min(360px, calc(100vh - 24px))", css)
        self.assertIn('font-family: var(--font-interface, "Onest Variable"', css)

    def test_journal_rows_are_not_hidden_by_marker_chronology(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertNotIn(
            ".approved-journal-table:not(.is-opj-chronology-ready) tbody",
            css,
        )
        self.assertNotIn('classList.add("is-opj-chronology-ready")', partial)
        self.assertNotIn("target.textContent = `№", partial)
        self.assertIn("is-opj-first-paint-ready", partial)
        self.assertIn("[data-page-body]", partial)
        self.assertIn("MutationObserver(revealWhenMaterialized)", partial)

    def test_emergency_outline_matches_compact_heavy_accepted_oval(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("width: max-content !important", css)
        self.assertIn("min-width: 0 !important", css)
        self.assertIn("inset: -0.18rem -0.36rem !important", css)
        self.assertIn("border: 3px solid", css)
        self.assertIn("border-radius: 999px !important", css)
        self.assertIn("transform: none !important", css)

    def test_accepted_marker_card_geometry_is_fixed_and_centered(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("width: 38px !important", css)
        self.assertIn("height: 46px !important", css)
        self.assertIn("grid-template-rows: 10px 18px 10px !important", css)
        self.assertIn("border: 1.5px solid currentColor !important", css)
        self.assertIn("border-radius: 7px !important", css)
        self.assertIn("line-height: 18px !important", css)

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
        self.assertIn(
            ".draft-normative-marker.is-pz_remove",
            css,
        )
        self.assertIn("color: var(--theme-primary", css)

    def test_current_repair_assets_use_fresh_cache_revision(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("opjlifecycle00603", partial)
        self.assertIn("opjlifecycle00603", css)
