from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]


class OperationalJournalAcceptanceRepairSourceTests(SimpleTestCase):
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

    def test_grouped_server_marker_is_expanded_to_individual_cards(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")

        self.assertIn("data-marker-count", partial)
        self.assertIn("function expandGroupedMarkers", partial)
        self.assertIn("cloneNode(true)", partial)
        self.assertIn('clone.dataset.markerInstance = String(index)', partial)
        self.assertNotIn('<small class="opj-marker-count"', partial)

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

    def test_journal_is_never_hidden_or_revealed_by_marker_runtime(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertNotIn("ensureRepairStylesheet", partial)
        self.assertNotIn("opj-repair-css-pending", partial)
        self.assertNotIn("is-opj-first-paint-ready", partial)
        self.assertNotIn("visibility: hidden", partial)
        self.assertNotIn(
            ".approved-journal-table:not(.is-opj-chronology-ready) tbody",
            css,
        )
        self.assertNotIn('classList.add("is-opj-chronology-ready")', partial)
        self.assertNotIn("target.textContent = `№", partial)

    def test_critical_marker_style_is_available_before_marker_markup(self) -> None:
        partial = self.source("templates/operational_log/_normative_markers.html")

        style_position = partial.index("opj-marker-critical-00612")
        marker_position = partial.index("{% for marker in markers %}")
        self.assertLess(style_position, marker_position)
        self.assertIn("document.head.append(style)", partial)
        self.assertNotIn("opj_acceptance_action_repair.js", partial)

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

    def test_previously_accepted_marker_artwork_is_restored(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("width: 38px !important", css)
        self.assertIn("min-height: 49px !important", css)
        self.assertIn("grid-template-rows: auto 28px auto !important", css)
        self.assertIn("padding: 1px 2px 2px !important", css)
        self.assertIn("font-family: Arial, sans-serif !important", css)
        self.assertIn("font-size: 34px !important", css)
        self.assertIn("line-height: 26px !important", css)
        self.assertIn("transform: skew(-8deg) !important", css)
        self.assertNotIn("width: 42px !important", css)
        self.assertNotIn("height: 48px !important", css)

    def test_removal_marker_remains_visible_and_crosses_complete_source_badge(self) -> None:
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
        self.assertIn("top: 1px !important", css)
        self.assertIn("right: 1px !important", css)
        self.assertIn("bottom: 1px !important", css)
        self.assertIn("left: 1px !important", css)
        self.assertIn("width: auto !important", css)
        self.assertIn("height: auto !important", css)
        self.assertIn("transform: none !important", css)
        self.assertIn("width: 60px", css)
        self.assertIn("height: 2.5px", css)
        self.assertIn("rotate(52deg)", css)
        self.assertIn("rotate(-52deg)", css)
        self.assertNotIn("width: calc(100% - 2px) !important", css)
        self.assertIn(
            ".draft-normative-marker.is-pz_remove",
            css,
        )
        self.assertIn("color: #175cd3 !important", css)

    def test_clean_visas_cell_keeps_native_table_cell_geometry(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn(
            ".opj-clean-journal-page .approved-journal-visas.opj-clean-markers",
            css,
        )
        self.assertIn("display: table-cell !important", css)
        self.assertIn("vertical-align: top !important", css)

    def test_spread_mode_keeps_the_same_marker_artwork(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn(
            '.opj-workspace[data-view-mode="spread"] .opj-normative-marker',
            css,
        )
        self.assertIn("width: 38px !important", css)
        self.assertIn("min-height: 49px !important", css)

    def test_repair_v4_marker_tooltip_consumes_complete_theme_contract(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn("var(--theme-surface-raised", css)
        self.assertIn("color: var(--theme-text, #111827) !important", css)
        self.assertIn("color: var(--theme-text-muted) !important", css)
        self.assertIn("color: var(--theme-primary) !important", css)
        self.assertIn("color: var(--theme-primary-hover) !important", css)
        self.assertIn("var(--theme-shadow-overlay", css)
        self.assertNotIn("--theme-surface-elevated", css)

    def test_repair_v4_toolbar_states_do_not_hide_disabled_controls_with_opacity(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn(".draft-row-action):disabled", css)
        self.assertIn("background: var(--theme-control-disabled) !important", css)
        self.assertIn("color: var(--theme-text-muted) !important", css)
        self.assertIn("opacity: 1 !important", css)
        self.assertIn(".opj-register-draft-button", css)
        self.assertIn("background: var(--theme-primary) !important", css)
        self.assertIn("color: var(--theme-on-primary) !important", css)

    def test_repair_v4_spread_and_width_profiles_use_platform_geometry(self) -> None:
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertIn('.opj-workspace[data-page-width="wide"]', css)
        self.assertIn('.opj-workspace[data-page-width="full"]', css)
        self.assertIn("width: min(100%, 1680px) !important", css)
        self.assertIn("max-width: none !important", css)
        self.assertIn("--opj-grid-strong: var(--theme-border-strong)", css)
        self.assertIn("border-color: var(--theme-border-strong) !important", css)
        self.assertIn("background: var(--theme-surface-soft) !important", css)

    def test_repair_v4_disclosure_uses_canonical_svg_and_no_raw_caret(self) -> None:
        drawer = self.source("templates/operational_log/_shift_workspace_drawer.html")
        css = self.source(
            "static/operational_log/opj_lifecycle_acceptance_repair.css"
        )

        self.assertGreaterEqual(drawer.count("#icon-chevron-right"), 5)
        self.assertNotIn('class="opj-drawer-chevron" aria-hidden="true">⌄', drawer)
        self.assertNotIn('class="opj-drawer-chevron" aria-hidden="true">^', drawer)
        self.assertIn(".opj-drawer-chevron .ui-icon", css)
        self.assertIn("transform: rotate(90deg)", css)
        self.assertIn("color: var(--theme-primary-hover)", css)
