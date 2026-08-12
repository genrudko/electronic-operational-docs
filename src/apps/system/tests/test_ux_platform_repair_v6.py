from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformRepairV6SourceContractTests(SimpleTestCase):
    def test_authority_layout_css_is_not_runtime_injected(self) -> None:
        script = read("src/static/organizations/personnel_authority_followup.js")
        self.assertNotIn('createElement("link")', script)
        self.assertNotIn("document.head.append", script)
        self.assertNotIn("personnel_authority_followup.css", script)
        self.assertIn("Progressive enhancement only", script)

    def test_authority_matrix_is_the_synchronous_geometry_owner(self) -> None:
        matrix = read("src/static/organizations/personnel_authority_matrix.css")
        repair = read("src/static/organizations/personnel_authority_repair.css")
        followup = read("src/static/organizations/personnel_authority_followup.css")
        self.assertIn("canonical matrix/hierarchy presentation", matrix)
        self.assertIn("--authority-tree-width:clamp", matrix)
        self.assertIn("grid-template-columns:var(--authority-tree-width)", matrix)
        self.assertIn("Deprecated presentation layer neutralized", repair)
        self.assertIn("Deprecated late follow-up stylesheet neutralized", followup)
        self.assertNotIn(".authority-workspace", repair)
        self.assertNotIn(".authority-workspace", followup)

    def test_server_default_authority_state_is_geometry_stable_before_js(self) -> None:
        template = read("src/templates/organizations/authority_registry.html")
        matrix_css = read("src/static/organizations/personnel_authority_matrix.css")
        matrix_js = read("src/static/organizations/personnel_authority_matrix.js")
        self.assertIn('data-authority-view="matrix" aria-pressed="true"', template)
        self.assertIn('data-authority-panel="holders" hidden', template)
        self.assertIn('data-authority-panel="dispatch" hidden', template)
        self.assertIn('[data-filter-for="holders"]', matrix_css)
        self.assertNotIn('item.textContent = "▾"', matrix_js)
        self.assertNotIn('item.textContent = "▸"', matrix_js)
        self.assertIn("system/icons.svg#", matrix_js)
        self.assertIn('iconSvg("icon-chevron-right")', matrix_js)
        self.assertIn('iconSvg("icon-add")', matrix_js)

    def test_platform_has_normal_wide_and_specialist_profiles(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        for token in (
            "--ux-page-normal-max",
            "--ux-page-wide-max",
            "--ux-page-gutter",
            "main.ux-page-wide",
            "main.ux-page-specialist",
        ):
            self.assertIn(token, css)
        self.assertIn("main.authority-main", css)
        self.assertIn("main.opj-shift-main", css)
        self.assertIn("width:100%; max-width:none", re.sub(r"\s+", " ", css))

    def test_personnel_specialist_allocation_is_adaptive(self) -> None:
        css = read("src/static/organizations/personnel_directory.css")
        compact = re.sub(r"\s+", "", css)
        self.assertIn("grid-template-columns:clamp(20rem,24%,30rem)minmax(0,1fr)", compact)
        self.assertIn("overflow-wrap:normal", compact)
        self.assertIn("word-break:normal", compact)
        self.assertIn("min-height:var(--theme-control-height-sm)", compact)

    def test_opj_full_and_spread_measure_against_specialist_stage(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        compact = re.sub(r"\s+", " ", css)
        self.assertIn('opj-workspace[data-page-width="full"] { width:100%; max-width:none; }', compact)
        self.assertIn('opj-workspace[data-view-mode="spread"] .opj-editor-container { min-width:0; grid-template-columns:repeat(2,minmax(0,1fr))', compact)
        self.assertIn("font-size:clamp(1.3rem,1.25vw,1.65rem)", compact)
        self.assertIn("font-size:var(--theme-font-size-xs)", compact)

    def test_equipment_relation_consumers_keep_label_and_code_separate(self) -> None:
        template = read("src/templates/equipment/detail.html")
        self.assertGreaterEqual(template.count('class="ux-value-stack"'), 4)
        self.assertGreaterEqual(template.count('class="ux-value-primary"'), 4)
        self.assertGreaterEqual(template.count('class="ux-technical technical-only"'), 4)

    def test_opj_meaningful_controls_do_not_use_micro_font_literals_in_platform_bridge(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        opj_bridge = css.split("Specialist OPJ", 1)[1]
        for literal in ("0.52rem", "0.53rem", "0.58rem", "0.61rem", "0.64rem"):
            self.assertNotIn(literal, opj_bridge)
