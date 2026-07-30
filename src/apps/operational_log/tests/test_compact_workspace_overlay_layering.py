from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
RUNTIME_REVISION = "011364"
WORKSPACE_REVISION = "opjux00105"


class CompactWorkspaceOverlayLayeringTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_workspace_has_one_compact_sticky_control_surface(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")
        toolbar = self.source(
            "templates/operational_log/_shift_workspace_toolbar.html"
        )
        workspace = self.source("static/operational_log/draft_workspace.js")
        css = self.source("static/operational_log/opj_workspace_controls.css")
        self.assertEqual(
            template.count("operational_log/_shift_workspace_toolbar.html"),
            1,
        )
        self.assertEqual(toolbar.count("data-page-navigation"), 1)
        self.assertNotIn("draft-clean-copy-action", toolbar)
        self.assertIn("Зарегистрированный журнал", template)
        self.assertNotIn("--draft-page-navigation-top", workspace)
        self.assertNotIn("--draft-command-bar-height", workspace)
        self.assertNotIn("new ResizeObserver", workspace)
        self.assertIn(".opj-workspace-page .opj-toolbar-primary", css)
        self.assertIn("min-height: 40px", css)
        self.assertIn(".opj-title-cluster", template)
        self.assertIn(".opj-title-cluster", css)

    def test_editor_toolbar_starts_compact_with_local_svg_commands(self) -> None:
        toolbar = self.source(
            "templates/operational_log/_shift_workspace_toolbar.html"
        )
        workspace = self.source("static/operational_log/draft_workspace.js")
        css = self.source("static/operational_log/opj_workspace_controls.css")
        self.assertIn('data-ribbon-mode="compact"', toolbar)
        self.assertIn("data-ribbon-mode-toggle", toolbar)
        self.assertIn("opj-command-symbols", toolbar)
        for icon in ("bold", "list", "link", "bolt"):
            self.assertIn(f'id="opj-icon-{icon}"', toolbar)
        self.assertIn("opj-time-format-example", toolbar)
        self.assertIn("1234", toolbar)
        self.assertIn("12:34", toolbar)
        self.assertIn("eod.operationalJournal.ribbonMode", workspace)
        self.assertIn("function applyRibbonMode", workspace)
        self.assertIn('data-ribbon-mode="compact"', css)
        self.assertIn('data-ribbon-mode="expanded"', css)

    def test_single_and_spread_reuse_existing_pagination(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")
        toolbar = self.source(
            "templates/operational_log/_shift_workspace_toolbar.html"
        )
        drawer = self.source(
            "templates/operational_log/_shift_workspace_drawer.html"
        )
        workspace = self.source("static/operational_log/draft_workspace.js")
        controls = self.source("static/operational_log/opj_workspace_controls.js")
        css = self.source("static/operational_log/opj_workspace_controls.css")
        for source in (toolbar, drawer):
            self.assertIn('data-view-mode="single"', source)
            self.assertIn('data-view-mode="spread"', source)
            self.assertIn("Разворот", source)
        self.assertIn('data-opj-presentation-mode="single-spread"', template)
        self.assertIn('data-page-shell="right"', template)
        self.assertIn('viewMode === "spread"', workspace)
        self.assertIn("renderCurrentPages", workspace)
        self.assertIn("syncPresentationState", controls)
        self.assertIn('data-view-mode="spread"', css)
        self.assertIn("position: static !important", css)
        self.assertIn("top: auto !important", css)

    def test_display_preferences_have_runtime_css_contracts(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")
        workspace = self.source("static/operational_log/draft_workspace.js")
        css = self.source("static/operational_log/opj_workspace_controls.css")
        self.assertIn(
            'data-initial-page-width="{{ ui_preferences.journal_width|lower }}"',
            template,
        )
        for marker in (
            "workspace.dataset.pageWidth",
            "workspace.dataset.journalEntrySize",
            "workspace.dataset.journalTimeSize",
            "workspace.dataset.journalDateSize",
            "workspace.dataset.journalTableHeaderSize",
        ):
            self.assertIn(marker, workspace)
        for marker in (
            'data-page-width="standard"',
            'data-page-width="wide"',
            'data-page-width="full"',
            'data-journal-entry-size="small"',
            'data-journal-time-size="large"',
            'data-journal-date-size="extra_large"',
            'data-journal-table-header-size="normal"',
            'html[data-theme="dark"]',
        ):
            self.assertIn(marker, css)

    def test_ledger_rows_are_content_driven_not_fixed_82_pixels(self) -> None:
        core = self.source("static/operational_log/opj_ux_001.css")
        controls = self.source("static/operational_log/opj_workspace_controls.css")
        self.assertIn("min-height: 82px", core)
        self.assertIn("min-height: 0", controls)
        self.assertIn("min-height: 24px", controls)
        self.assertIn(".opj-workspace .draft-empty-record", controls)
        self.assertIn("min-height: 36px", controls)

    def test_drawer_is_narrow_card_based_and_state_synced(self) -> None:
        drawer = self.source(
            "templates/operational_log/_shift_workspace_drawer.html"
        )
        css = self.source("static/operational_log/opj_workspace_controls.css")
        controls = self.source("static/operational_log/opj_workspace_controls.js")
        self.assertIn("opj-drawer-card", drawer)
        self.assertIn("opj-drawer-shift-summary", drawer)
        self.assertIn("width: min(360px, 100vw)", css)
        self.assertIn("syncDrawerState", controls)
        self.assertIn("aria-controls", controls)

    def test_runtime_assets_are_local_and_revisioned(self) -> None:
        base = self.source("templates/base.html")
        template = self.source("templates/operational_log/shift_workspace.html")
        editor = self.source("static/operational_log/draft_editor.js")
        navigation = self.source("static/operational_log/draft_reference_navigation.js")
        for source in (base, template):
            self.assertIn(f"?v={RUNTIME_REVISION}", source)
            self.assertNotIn("https://cdn", source.lower())
        self.assertIn(WORKSPACE_REVISION, template)
        self.assertIn("opj_workspace_controls.css", template)
        self.assertIn("opj_workspace_controls.js", template)
        self.assertIn(
            f'const RUNTIME_REVISION = "{RUNTIME_REVISION}";',
            editor,
        )
        self.assertIn(
            f'const RUNTIME_REVISION = "{RUNTIME_REVISION}";',
            navigation,
        )

    def test_patch_is_schema_neutral(self) -> None:
        migrations = ROOT / "apps/operational_log/migrations"
        self.assertFalse(list(migrations.glob("0007*.py")))
