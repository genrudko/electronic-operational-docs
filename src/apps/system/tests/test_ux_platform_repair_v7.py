from __future__ import annotations

import re
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class UxPlatformRepairV7SourceContractTests(SimpleTestCase):
    def test_specialist_and_wide_profiles_reach_useful_workspaces(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        compact = re.sub(r"\s+", "", css)

        self.assertIn("body.ux-platform.opj-clean-journal-page.da-page:has(>main.opj-main)", compact)
        self.assertIn(".da-page:has(.personnel-layout)", css)
        self.assertIn(".authority-workspace", css)
        self.assertIn(".authority-table-wrap", css)
        self.assertIn(".approved-journal-shell", css)
        self.assertIn("width:100%;max-width:none", compact)

    def test_opj_interaction_layer_uses_canonical_dense_geometry(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        compact = re.sub(r"\s+", "", css)

        self.assertIn(":is(.opj-toolbar-primary,.opj-editor-toolbar,.opj-action-strip)", compact)
        self.assertIn("padding:var(--theme-space-2)var(--theme-space-3)", compact)
        self.assertIn("min-height:var(--theme-control-height-sm)", compact)
        self.assertIn('opj-workspace[data-page-width="full"].opj-editor-container', compact)
        self.assertIn('opj-workspace[data-view-mode="spread"].opj-editor-container', compact)

    def test_registered_and_working_opj_share_operational_header_hierarchy(self) -> None:
        css = read("src/static/system/ux_platform_compositions.css")
        registered = read("src/templates/operational_log/detail.html")

        self.assertIn("opj-clean-journal-page .journal-workspace-bar", css)
        self.assertIn("opj-clean-journal-page .journal-workspace-title h1", css)
        self.assertIn("journal-workspace-title", registered)
        self.assertIn("<h1>{{ journal.title }}</h1>", registered)

    def test_equipment_and_documents_separate_human_and_technical_values(self) -> None:
        equipment = read("src/templates/equipment/site_detail.html")
        documents = read("src/templates/documents/detail.html")

        for template in (equipment, documents):
            self.assertIn("ux-value-stack", template)
            self.assertIn("ux-value-primary", template)
            self.assertIn("ux-value-secondary ux-technical technical-only", template)

        self.assertNotIn("<strong>{{ row.display_name }}</strong><code", equipment)
        self.assertNotIn("<strong>{{ row.display_name }}</strong></a>\n            <code", documents)

    def test_repair_does_not_create_another_acceptance_stylesheet(self) -> None:
        static_root = ROOT / "src/static"
        forbidden = ("repair_v7.css", "final_fix.css", "owner_acceptance_patch.css")
        existing = {path.name for path in static_root.rglob("*.css")}

        for name in forbidden:
            self.assertNotIn(name, existing)
