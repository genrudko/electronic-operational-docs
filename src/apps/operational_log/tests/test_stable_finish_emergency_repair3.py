from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011352"


class StableFinishEmergencyRepair3Tests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_emergency_mark_is_explicitly_toggleable_for_whole_entry(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        template = self.source("templates/operational_log/shift_workspace.html")
        self.assertIn("function hasEmergencyAnnotation(controller)", editor)
        self.assertIn("function updateEmergencyActionState(controller)", editor)
        self.assertIn("data-normative-remove-emergency", template)
        self.assertIn("Снять аварийную отметку с записи", template)

    def test_emergency_outline_remains_red_during_focus(self) -> None:
        css = self.source("static/system/app.css")
        self.assertIn(
            ".draft-ledger-row.is-emergency-event .draft-ledger-time input:focus",
            css,
        )
        self.assertIn("border: 2px solid #dc2626 !important", css)
        self.assertIn("border-color: #ff4d4f !important", css)

    def test_text_removal_failure_uses_inline_normative_feedback(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn("function setNormativeMenuMessage(message, tone", editor)
        self.assertIn(
            "Аварийная отметка снимается отдельной командой.",
            editor,
        )
        self.assertNotIn(
            'window.alert("В выделенном фрагменте нет нормативной отметки.")',
            editor,
        )

    def test_finish_event_carries_visual_viewport_anchor(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn("rowTop: row?.getBoundingClientRect().top ?? null", editor)
        self.assertIn('finishEditorInteraction(previousController, "outside-click")', editor)
        self.assertIn("formatSimplifiedTimeAfterCommit(controller);", editor)

    def test_ctrl_enter_completion_uses_row_anchor_not_smooth_reveal(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn("function captureViewportAnchor(row, supplied", workspace)
        self.assertIn("function restoreViewportAnchor(snapshot)", workspace)
        self.assertIn("scroll: false", workspace)
        self.assertIn("restoreViewportAnchor(viewport);", workspace)

    def test_outside_canvas_click_finishes_active_editor(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn(
            'finishEditorInteraction(previousController, "outside-click")',
            editor,
        )
        self.assertIn(
            "!previousController.form.contains(event.target)",
            editor,
        )

    def test_normative_popover_is_treated_as_editor_overlay(self) -> None:
        workspace = self.source("static/operational_log/draft_workspace.js")
        self.assertIn('[data-normative-menu]', workspace)

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
