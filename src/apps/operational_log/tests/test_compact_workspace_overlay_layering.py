from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011350"


class CompactWorkspaceOverlayLayeringTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_workspace_has_one_sticky_control_surface(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")
        workspace = self.source("static/operational_log/draft_workspace.js")
        css = self.source("static/system/app.css")
        self.assertIn("draft-command-primary-row", template)
        self.assertEqual(template.count("data-page-navigation"), 1)
        self.assertIn("draft-clean-copy-action", template)
        self.assertNotIn("shift-book-clean-copy", template)
        self.assertNotIn("--draft-page-navigation-top", workspace)
        self.assertNotIn("--draft-command-bar-height", workspace)
        self.assertNotIn("new ResizeObserver", workspace)
        self.assertIn("--layer-journal-sticky", css)
        self.assertIn("position: static;", css)

    def test_compact_ribbon_is_default_and_persisted_locally(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn('data-ribbon-mode="compact"', template)
        self.assertIn("data-ribbon-mode-toggle", template)
        self.assertIn('aria-expanded="false"', template)
        self.assertIn("eod.operationalJournal.ribbonMode", workspace)
        self.assertIn("function normalizeRibbonMode", workspace)
        self.assertIn("function applyRibbonMode", workspace)
        self.assertIn('ribbonMode === "compact" ? "expanded" : "compact"', workspace)

    def test_global_navigation_menu_is_accessible_and_viewport_clamped(self) -> None:
        base = self.source("templates/base.html")
        javascript = self.source("static/system/app.js")
        css = self.source("static/system/app.css")
        self.assertEqual(base.count("data-nav-menu class="), 2)
        self.assertEqual(base.count("data-nav-menu-trigger"), 2)
        self.assertEqual(base.count("data-nav-menu-panel"), 2)
        self.assertIn("function positionMenu(menu)", javascript)
        self.assertIn("viewportWidth - measured.width - VIEWPORT_MARGIN", javascript)
        self.assertIn("viewportHeight - viewportTop - VIEWPORT_MARGIN", javascript)
        self.assertIn('event.key === "Escape" && activeMenu', javascript)
        self.assertIn("closeMenu(activeMenu, true)", javascript)
        self.assertIn("!activeMenu.contains(event.target)", javascript)
        self.assertIn("--layer-global-header", css)
        self.assertIn("--layer-global-menu", css)
        self.assertIn("overflow-y: auto;", css)

    def test_runtime_assets_are_local_and_revisioned(self) -> None:
        base = self.source("templates/base.html")
        template = self.source("templates/operational_log/shift_workspace.html")
        editor = self.source("static/operational_log/draft_editor.js")
        navigation = self.source("static/operational_log/draft_reference_navigation.js")
        for source in (base, template):
            self.assertIn(f"?v={REVISION}", source)
            self.assertNotIn("https://cdn", source.lower())
        self.assertIn(f'const RUNTIME_REVISION = "{REVISION}";', editor)
        self.assertIn(f'const RUNTIME_REVISION = "{REVISION}";', navigation)

    def test_patch_is_schema_neutral(self) -> None:
        migrations = ROOT / "apps/operational_log/migrations"
        self.assertFalse(list(migrations.glob("0007*.py")))
