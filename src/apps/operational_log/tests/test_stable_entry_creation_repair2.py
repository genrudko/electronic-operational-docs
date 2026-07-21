from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011342"


class StableEntryCreationRepair2Tests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_pending_removal_immediately_frees_a_creation_slot(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn("function ensureBlankCreationSlot(anchorRow)", workspace)
        self.assertIn("ensureBlankCreationSlot(state.row);", workspace)
        self.assertIn("paginateByRecordCount();", workspace)

    def test_whole_blank_row_starts_inline_creation(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn('record.setAttribute("role", "button")', workspace)
        self.assertIn('record.addEventListener("click", (event) =>', workspace)
        self.assertIn("beginInlineCreation(", workspace)
        self.assertIn("Создать запись в этой свободной строке", workspace)

    def test_inline_creation_owns_pagination_until_completion(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn("Boolean(inlineCreation?.record?.isConnected)", workspace)
        self.assertIn("function flushDeferredPagination()", workspace)
        self.assertIn("flushDeferredPagination();", workspace)

    def test_undo_placeholder_has_close_and_zero_second_finalization(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        template = self.source("templates/operational_log/shift_workspace.html")
        self.assertIn("data-inline-undo-close", template)
        self.assertIn("function dismissInlineRemoval(state)", workspace)
        self.assertIn("seconds === 0", workspace)
        self.assertIn("window.queueMicrotask", workspace)

    def test_page_navigation_uses_measured_sticky_offset(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        template = self.source("templates/operational_log/shift_workspace.html")
        css = self.source("static/system/app.css")
        self.assertIn("data-page-navigation", template)
        self.assertIn('"--draft-page-navigation-top"', workspace)
        self.assertIn("stickyLayoutObserver?.observe(commandBar);", workspace)
        self.assertIn("position: sticky", css)

    def test_simplified_time_has_before_and_after_input_paths(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn('editor.addEventListener("beforeinput", (event) =>', editor)
        self.assertIn("function simplifiedTimeCommitInput(event)", editor)
        self.assertIn("function formatSimplifiedTimeAfterCommit(controller)", editor)
        self.assertIn("formatSimplifiedTimeAtCaret(", editor)

    def test_pz_number_uses_embedded_accessible_workflow(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        template = self.source("templates/operational_log/shift_workspace.html")
        self.assertIn("data-pz-number-panel", template)
        self.assertIn("data-pz-number-input", template)
        self.assertIn("data-pz-number-preview", template)
        self.assertIn("function showPzNumberStep", editor)
        self.assertNotIn("window.prompt", editor)

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
