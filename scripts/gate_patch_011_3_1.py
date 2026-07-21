from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, marker: str, message: str) -> None:
    if not condition:
        raise RuntimeError(message)
    print(f"{marker}=PASSED")


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def main() -> None:
    editor = read("src/static/operational_log/draft_editor.js")
    workspace = read("src/static/operational_log/draft_workspace.js")
    navigation = read(
        "src/static/operational_log/draft_reference_navigation.js"
    )
    template = read(
        "src/templates/operational_log/shift_workspace.html"
    )
    base = read("src/templates/base.html")
    css = read("src/static/system/app.css")
    views = read("src/apps/operational_log/views.py")
    services = read("src/apps/operational_log/services.py")

    require(
        'event.key === "Enter"' in editor
        and '"ctrl-enter"' in editor
        and '"eod:finish-draft-edit"' in editor
        and "deactivate(form)" in editor,
        "DRAFT_EDIT_COMPLETION_SHORTCUTS",
        "Ctrl+Enter/Esc completion runtime is incomplete",
    )
    require(
        'event.code === "KeyA"' in editor
        and "selectEntireEditor(controller)" in editor
        and "selection.removeAllRanges();" in editor,
        "REFERENCE_AWARE_SELECT_ALL",
        "reference-aware Ctrl+A runtime is incomplete",
    )
    require(
        "tokenPointerGesture" in navigation
        and "event.shiftKey" in navigation
        and "selection && !selection.isCollapsed" in navigation,
        "REFERENCE_SELECTION_GESTURES",
        "reference token selection gestures are not protected",
    )
    require(
        "data-entry-kind-trigger" in template
        and "draft-floating-kind-trigger" in template
        and "data-entry-kind-current" in template,
        "FLOATING_ENTRY_KIND_MENU",
        "floating entry-kind control is missing",
    )
    require(
        "data-remove-draft" in template
        and "data-restore-url" in template
        and "data-inline-undo" in template
        and "data-inline-undo-close" in template
        and "removeDraftRow(" in workspace
        and "undoRemovedDraft(" in workspace
        and "10000" in workspace,
        "SEAMLESS_DELETE_WITH_UNDO",
        "seamless delete/undo contract is incomplete",
    )
    require(
        "_json_requested" in views
        and '"is_removed": removed.is_removed' in views
        and '"is_removed": restored.is_removed' in views
        and "locked_entry.position = last_position + 10" not in services,
        "AJAX_SOFT_DELETE_POSITION_PRESERVATION",
        "AJAX delete/restore or position preservation is incomplete",
    )
    require(
        "Сохранено ·" in template
        and "Запись №" in template
        and "Версия&nbsp;" in template
        and "draft-meta-chip" in css,
        "EXPLAINED_RECORD_METADATA",
        "record metadata remains ambiguous",
    )
    require(
        "draft-row-action-toolbar" in css
        and "draft-row-action.is-danger" in css
        and "draft-inline-undo" in css
        and "draft-row-restored" in css,
        "POLISHED_RECORD_ACTIONS",
        "record action and undo visual contract is incomplete",
    )
    require(
        "?v=011343" in template
        and "?v=011343" in base
        and 'const RUNTIME_REVISION = "011343";' in editor,
        "PATCH_011_3_1_CACHE_REVISION",
        "runtime cache revision is incomplete",
    )
    require(
        {path.name for path in (ROOT / "src/apps/operational_log/migrations").glob("0006*.py")}
        == {"0006_alter_operationaldraftentry_editor_schema_version.py"},
        "CONTROLLED_EDITOR_SCHEMA_EVOLUTION",
        "unexpected operational_log schema evolution detected",
    )
    print("PATCH_011_3_1_ENTRY_COMPLETION_UNDO_UX_GATE_PASSED")


if __name__ == "__main__":
    main()
