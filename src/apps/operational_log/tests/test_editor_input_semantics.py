from __future__ import annotations

from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[3]
REVISION = "011363"


class EditorInputSemanticsRuntimeTests(SimpleTestCase):
    def source(self, relative: str) -> str:
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_caret_bookmarks_follow_editable_text_inside_reference(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn("function selectionEndpointBookmark", editor)
        self.assertIn("function positionFromTextBookmark", editor)
        self.assertIn("data-reference-token-label", editor)
        self.assertNotIn('token.contentEditable = "false";', editor)
        self.assertIn("restoreTextBookmark(controller.editor, bookmark);", editor)

    def test_reference_label_is_editable_and_stale_link_is_detached(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        navigation = self.source(
            "static/operational_log/draft_reference_navigation.js"
        )
        self.assertIn("function detachReferencesForEditing", editor)
        self.assertIn("function detachStaleReferences", editor)
        self.assertIn("referenceTokenLabel(token)", editor)
        self.assertIn("eod:edit-reference-token", editor)
        self.assertIn("data-reference-token-action", navigation)
        self.assertIn("event.ctrlKey || event.metaKey", navigation)

    def test_clipboard_text_excludes_reference_action(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        css = self.source("static/system/app.css")
        self.assertIn('editor.addEventListener("copy"', editor)
        self.assertRegex(
            editor,
            r'event\.clipboardData\.setData\(\s*"text/plain"',
        )
        self.assertIn("function sanitizeClipboardText", editor)
        self.assertIn("function clipboardTextFromNode", editor)
        self.assertIn("function clipboardTextFromChildren", editor)
        self.assertNotIn("container.innerText", editor)
        self.assertNotIn("draft-clipboard-serializer", editor)
        self.assertIn("↗", editor)
        self.assertIn(".draft-reference-token-action::before", css)
        self.assertIn('content: "↗";', css)

    def test_windows_navigation_stays_inside_active_editor(self) -> None:
        editor = self.source("static/operational_log/draft_editor.js")
        self.assertIn("function moveSelectionWithModify", editor)
        self.assertIn('"lineboundary"', editor)
        self.assertIn('"word"', editor)
        self.assertIn("function moveSelectionByPage", editor)
        self.assertIn("function editorVisualLineRects", editor)
        self.assertIn("function editorPositionFromPoint", editor)
        self.assertIn("function restoreWindowViewport", editor)
        page_navigation = editor.split(
            "function moveSelectionByPage",
            1,
        )[1].split("function placeCaretAfter", 1)[0]
        self.assertNotIn("moveSelectionWithModify(", page_navigation)
        self.assertIn('["PageUp", "PageDown"]', editor)
        self.assertIn("editorBoundaryPosition", editor)

    def test_runtime_revision_is_consistent(self) -> None:
        template = self.source("templates/operational_log/shift_workspace.html")
        base = self.source("templates/base.html")
        editor = self.source("static/operational_log/draft_editor.js")
        navigation = self.source(
            "static/operational_log/draft_reference_navigation.js"
        )
        self.assertIn(f'?v={REVISION}', template)
        self.assertIn(f'?v={REVISION}', base)
        self.assertIn(f'const RUNTIME_REVISION = "{REVISION}";', editor)
        self.assertIn(f'const RUNTIME_REVISION = "{REVISION}";', navigation)
