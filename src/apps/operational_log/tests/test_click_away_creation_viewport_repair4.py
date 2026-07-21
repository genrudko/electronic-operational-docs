from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011364"


class ClickAwayCreationViewportRepair4Tests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_pointerdown_captures_inline_creation_anchor_before_blur(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn('document.addEventListener("pointerdown"', workspace)
        self.assertIn("state.finishAfterMaterialize = true;", workspace)
        self.assertIn(
            "state.clickAwayViewport = captureViewportAnchor(state.record);",
            workspace,
        )

    def test_async_materialization_honors_click_away_intent(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn("finishAfterMaterialize: false", workspace)
        self.assertIn("clickAwayViewport: null", workspace)
        self.assertIn("await finishDraftEditing(", workspace)
        self.assertIn('"inline-click-away"', workspace)
        self.assertIn("focusContent && !state.finishAfterMaterialize", workspace)

    def test_finishing_state_blocks_delayed_pagination_race(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn(
            'activeDraftForm.dataset.finishing === "true"',
            workspace,
        )
        self.assertIn("cancelScheduledPagination();", workspace)
        self.assertIn("flushDeferredPaginationImmediately();", workspace)
        completion = workspace.split(
            "async function finishDraftEditing",
            1,
        )[1].split("function rowText", 1)[0]
        self.assertLess(
            completion.index("flushDeferredPaginationImmediately();"),
            completion.index("restoreViewportAnchor(viewport);"),
        )

    def test_empty_click_away_cancellation_preserves_anchor(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        cancellation = workspace.split(
            "function cancelInlineCreation",
            1,
        )[1].split("function inlineCreationHasMeaningfulInput", 1)[0]
        self.assertIn("captureViewportAnchor(record, suppliedViewport)", cancellation)
        self.assertIn("viewport.row = replacement;", cancellation)
        self.assertIn("restoreViewportAnchor(viewport);", cancellation)

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
