from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "011360"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(name: str, condition: bool) -> None:
    if not condition:
        raise SystemExit(f"{name}=FAILED")
    print(f"{name}=PASSED")


def main() -> None:
    editor = read("src/static/operational_log/draft_editor.js")
    navigation = read(
        "src/static/operational_log/draft_reference_navigation.js"
    )
    css = read("src/static/system/app.css")
    template = read("src/templates/operational_log/shift_workspace.html")
    base = read("src/templates/base.html")

    require(
        "LOGICAL_CARET_BOOKMARKS",
        "function selectionEndpointBookmark" in editor
        and "function positionFromTextBookmark" in editor
        and "restoreTextBookmark(controller.editor, bookmark);" in editor,
    )
    require(
        "EDITABLE_REFERENCE_LABEL",
        "data-reference-token-label" in editor
        and 'token.contentEditable = "false";' not in editor
        and "function detachReferencesForEditing" in editor
        and "function detachStaleReferences" in editor,
    )
    require(
        "CLEAN_CLIPBOARD_REFERENCE_ACTION",
        'editor.addEventListener("copy"' in editor
        and "function sanitizeClipboardText" in editor
        and ".draft-reference-token-action::before" in css
        and 'content: "↗";' in css,
    )
    require(
        "EDITOR_LOCAL_KEYBOARD_NAVIGATION",
        "function moveSelectionWithModify" in editor
        and '"lineboundary"' in editor
        and "function moveSelectionByPage" in editor
        and '["PageUp", "PageDown"]' in editor,
    )
    require(
        "REFERENCE_PREVIEW_EXPLICIT_ACTION",
        "data-reference-token-action" in navigation
        and "event.ctrlKey || event.metaKey" in navigation
        and "eod:edit-reference-token" in navigation,
    )
    require(
        "PATCH_011_3_6_CACHE_REVISION",
        f'const RUNTIME_REVISION = "{REVISION}";' in editor
        and f'const RUNTIME_REVISION = "{REVISION}";' in navigation
        and f"?v={REVISION}" in template
        and f"?v={REVISION}" in base,
    )
    require(
        "NO_DATABASE_SCHEMA_CHANGE",
        not any((ROOT / "src/apps").glob("*/migrations/*011_3_6*")),
    )
    print("PATCH_011_3_6_EDITOR_INPUT_SEMANTICS_GATE_PASSED")


if __name__ == "__main__":
    main()
