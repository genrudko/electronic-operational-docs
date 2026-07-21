from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "011343"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition: bool, marker: str, message: str) -> None:
    if not condition:
        raise RuntimeError(message)
    print(f"{marker}=PASSED")


def main() -> None:
    workspace = read("src/static/operational_log/draft_workspace.js")
    editor = read("src/static/operational_log/draft_editor.js")
    navigation = read(
        "src/static/operational_log/draft_reference_navigation.js"
    )
    template = read("src/templates/operational_log/shift_workspace.html")
    base = read("src/templates/base.html")
    css = read("src/static/system/app.css")

    require(
        "function ensureBlankCreationSlot(anchorRow)" in workspace
        and "ensureBlankCreationSlot(state.row);" in workspace
        and '.draft-empty-record:not(.is-inline-creating)' in css,
        "PENDING_REMOVAL_FREES_CREATION_SLOT",
        "pending removal does not immediately expose a creation slot",
    )
    require(
        'record.setAttribute("role", "button")' in workspace
        and 'record.addEventListener("click", (event) =>' in workspace
        and '"Создать запись в этой свободной строке"' in workspace
        and 'event.target.closest?.("input, textarea, button, a")' in workspace,
        "WHOLE_BLANK_ROW_CREATION",
        "the whole free row is not an accessible creation target",
    )
    require(
        "Boolean(inlineCreation?.record?.isConnected)" in workspace
        and "markPaginationPending();" in workspace
        and "flushDeferredPagination();" in workspace,
        "INLINE_CREATION_PAGINATION_OWNERSHIP",
        "pagination can still tear down active inline creation",
    )
    require(
        "data-inline-undo-close" in template
        and "function dismissInlineRemoval(state)" in workspace
        and "closeButton.onclick = () => dismissInlineRemoval(state);" in workspace
        and ".draft-inline-undo-close" in css,
        "INLINE_UNDO_DISMISS",
        "inline undo cannot be dismissed immediately",
    )
    require(
        "seconds === 0" in workspace
        and "window.queueMicrotask(() => finalizeRemovedDraft(state, true))"
        in workspace,
        "UNDO_ZERO_SECOND_FINALIZATION",
        "undo placeholder can remain stuck at zero seconds",
    )
    require(
        "data-page-navigation" in template
        and "const commandBar = workspace.querySelector" in workspace
        and '"--draft-page-navigation-top"' in workspace
        and ".draft-page-navigation {\n    position: sticky;" in css
        and "stickyLayoutObserver?.observe(commandBar);" in workspace,
        "STICKY_PAGE_NAVIGATION_OFFSET",
        "page navigation is not offset below the measured sticky command bar",
    )
    require(
        'editor.addEventListener("beforeinput", (event) =>' in editor
        and "function simplifiedTimeCommitInput(event)" in editor
        and "function formatSimplifiedTimeAfterCommit(controller)" in editor
        and "formatSimplifiedTimeAtCaret(" in editor,
        "ROBUST_SIMPLIFIED_TIME_COMMIT",
        "simplified time conversion lacks beforeinput/input fallback",
    )
    require(
        "data-pz-number-panel" in template
        and "data-pz-number-input" in template
        and "data-pz-number-preview" in template
        and "function showPzNumberStep" in editor
        and "function updatePzNumberPreview" in editor
        and ".draft-pz-number-layout" in css,
        "EMBEDDED_PZ_NUMBER_WORKFLOW",
        "PZ number workflow is not embedded in the normative menu",
    )
    require(
        "window.prompt" not in editor
        and "function showNormativeSourceStep" in editor
        and "data-normative-source-panel" in template,
        "NATIVE_PZ_PROMPTS_REMOVED",
        "native prompt remains in the PZ/source workflow",
    )
    require(
        all(
            f'?v={REVISION}' in source
            for source in (template, base)
        )
        and all(
            f'const RUNTIME_REVISION = "{REVISION}";' in source
            for source in (editor, navigation)
        ),
        "PATCH_011_3_4_REPAIR2_CACHE_REVISION",
        "Repair 2 runtime cache revision is incomplete",
    )
    require(
        not list(
            (ROOT / "src/apps/operational_log/migrations").glob("0007*.py")
        ),
        "NO_DATABASE_SCHEMA_CHANGE",
        "Repair 2 must not introduce operational_log migration 0007",
    )
    print("PATCH_011_3_4_REPAIR2_STABLE_ENTRY_CREATION_GATE_PASSED")


if __name__ == "__main__":
    main()
