from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

OLD_UNCONDITIONAL_SCROLL_HANDLER = re.compile(
    r'window\.addEventListener\(\s*"scroll",\s*\(\)\s*=>\s*\{\s*'
    r'hideFloatingToolbar\(\);\s*'
    r'hideEntryKindMenu\(\);\s*'
    r'hideReferencePicker\(\);\s*'
    r'\},\s*true\s*\);',
    re.DOTALL,
)
GUARDED_REFERENCE_SCROLL_HANDLER = re.compile(
    r'window\.addEventListener\(\s*"scroll",\s*\(event\)\s*=>\s*\{\s*'
    r'hideFloatingToolbar\(\);\s*'
    r'const target = event\.target;\s*'
    r'if\s*\(\s*'
    r'target instanceof Element\s*'
    r'&&\s*target\.closest\("\[data-reference-picker\]"\)\s*'
    r'\)\s*\{\s*return;\s*\}\s*'
    r'hideEntryKindMenu\(\);\s*'
    r'hideReferencePicker\(\);\s*'
    r'\},\s*true\s*\);',
    re.DOTALL,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    editor = (
        SRC / "static" / "operational_log" / "draft_editor.js"
    ).read_text(encoding="utf-8")
    workspace = (
        SRC / "static" / "operational_log" / "draft_workspace.js"
    ).read_text(encoding="utf-8")
    navigation = (
        SRC / "static" / "operational_log" / "draft_reference_navigation.js"
    ).read_text(encoding="utf-8")
    template = (
        SRC / "templates" / "operational_log" / "shift_workspace.html"
    ).read_text(encoding="utf-8")
    css = (SRC / "static" / "system" / "app.css").read_text(
        encoding="utf-8"
    )

    require(
        GUARDED_REFERENCE_SCROLL_HANDLER.search(editor) is not None,
        "guarded reference-picker scroll handler missing",
    )
    require(
        OLD_UNCONDITIONAL_SCROLL_HANDLER.search(editor) is None,
        "old unconditional scroll listener remains",
    )
    print("REFERENCE_PICKER_INTERNAL_SCROLL=PASSED")

    for marker in (
        "let editorOverlayActive = false;",
        "function isEditorOverlayTarget",
        '"eod:editor-overlay-state"',
        '"eod:reveal-draft-reference"',
        "revealChronologicalRow(row);",
    ):
        require(marker in workspace, f"workspace marker missing: {marker}")
    print("EDITOR_OVERLAY_PAGINATION_GUARD=PASSED")

    for marker in (
        ".draft-reference-token",
        "draft-reference-preview",
        "catalogByReference",
        "captureViewport",
        "restoreEditorAndViewport",
        'new CustomEvent("eod:editor-overlay-state"',
        'new CustomEvent("eod:reveal-draft-reference"',
        'return { mode: "url", value: `/equipment/items/${rawId}/` };',
        'return { mode: "url", value: `/documents/${rawId}/` };',
        'return { mode: "url", value: "/organization/" };',
        'return { mode: "draft", value: rawId };',
        "event.stopImmediatePropagation();",
    ):
        require(marker in navigation, f"navigation marker missing: {marker}")
    require("innerHTML" not in navigation, "unsafe innerHTML is forbidden")
    print("REFERENCE_PREVIEW_AND_NAVIGATION=PASSED")

    editor_index = template.index("operational_log/draft_editor.js")
    workspace_index = template.index("operational_log/draft_workspace.js")
    navigation_index = template.index(
        "operational_log/draft_reference_navigation.js"
    )
    require(
        editor_index < workspace_index < navigation_index,
        "deferred script order is invalid",
    )
    print("REFERENCE_NAVIGATION_SCRIPT_ORDER=PASSED")

    for marker in (
        "Patch 011.3 Repair 3: stable popovers and reference navigation",
        ".draft-reference-preview",
        ".draft-reference-preview-actions",
    ):
        require(marker in css, f"css marker missing: {marker}")
    print("REFERENCE_PREVIEW_VISUAL_CONTRACT=PASSED")

    migrations = list(
        (SRC / "apps" / "operational_log" / "migrations").glob("0006*.py")
    )
    require(not migrations, "Repair 3 must not add migration 0006")
    print("NO_DATABASE_SCHEMA_CHANGE=PASSED")
    print(
        "PATCH_011_3_REPAIR3_STABLE_POPOVERS_"
        "REFERENCE_NAVIGATION_GATE_PASSED"
    )


if __name__ == "__main__":
    main()
