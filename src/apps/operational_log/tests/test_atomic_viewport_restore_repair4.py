from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011344"


class AtomicViewportRestoreRepair4Tests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_finishing_save_cannot_start_smooth_chronology_reveal(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn('form.dataset.finishing !== "true"', workspace)
        self.assertIn("&& !form.contains(document.activeElement)", workspace)

    def test_viewport_anchor_is_restored_before_first_paint(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        immediate = workspace.index(
            "// Chromium cannot paint the temporary row-store position."
        )
        first_restore = workspace.index("        restore();", immediate)
        first_frame = workspace.index(
            "        window.requestAnimationFrame(() => {",
            immediate,
        )
        self.assertLess(first_restore, first_frame)

    def test_programmatic_viewport_restore_is_never_smooth(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn('behavior: "auto"', workspace)
        self.assertIn("window.scrollBy({", workspace)
        self.assertIn("window.scrollTo({", workspace)

    def test_completion_still_uses_non_scrolling_chronology_path(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn(
            'const chronologyApplied = applyPendingChronology(form, {',
            workspace,
        )
        self.assertIn("            scroll: false,", workspace)
        self.assertIn("            viewport,", workspace)

    def test_runtime_cache_revision_is_consistent(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        navigation = self.source(
            "static/operational_log/draft_reference_navigation.js"
        )
        template = self.source("templates/operational_log/shift_workspace.html")
        base = self.source("templates/base.html")
        self.assertIn(f'const RUNTIME_REVISION = "{REVISION}";', editor)
        self.assertIn(f'const RUNTIME_REVISION = "{REVISION}";', navigation)
        self.assertIn(f"?v={REVISION}", template)
        self.assertIn(f"?v={REVISION}", base)
