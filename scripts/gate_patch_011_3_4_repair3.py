from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "011344"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition: bool, marker: str, message: str) -> None:
    if not condition:
        raise RuntimeError(message)
    print(f"{marker}=PASSED")


def main() -> None:
    editor = read("src/static/operational_log/draft_editor.js")
    workspace = read("src/static/operational_log/draft_workspace.js")
    navigation = read(
        "src/static/operational_log/draft_reference_navigation.js"
    )
    template = read("src/templates/operational_log/shift_workspace.html")
    base = read("src/templates/base.html")
    css = read("src/static/system/app.css")

    require(
        "function hasEmergencyAnnotation(controller)" in editor
        and "function updateEmergencyActionState(controller)" in editor
        and "data-normative-remove-emergency" in template
        and "Снять аварийную отметку с записи" in template,
        "ENTRY_LEVEL_EMERGENCY_TOGGLE",
        "emergency annotation cannot be explicitly removed from the entry",
    )
    require(
        "border: 2px solid #dc2626 !important" in css
        and "border-color: #ff4d4f !important" in css
        and ".draft-ledger-time input:focus" in css,
        "FORCED_RED_EMERGENCY_OUTLINE",
        "emergency time outline is not reliably red in all focus/theme states",
    )
    require(
        "function setNormativeMenuMessage(message, tone" in editor
        and "Аварийная отметка снимается отдельной командой." in editor
        and 'window.alert("В выделенном фрагменте нет нормативной отметки.")'
        not in editor,
        "INLINE_NORMATIVE_FEEDBACK",
        "normative removal still uses a blocking native alert",
    )
    require(
        "function captureViewportAnchor(row, supplied" in workspace
        and "function restoreViewportAnchor(snapshot)" in workspace
        and "scroll: false" in workspace
        and "restoreViewportAnchor(viewport);" in workspace,
        "STABLE_CTRL_ENTER_VIEWPORT",
        "Ctrl+Enter completion does not preserve the row viewport anchor",
    )
    require(
        'finishEditorInteraction(previousController, "outside-click")'
        in editor
        and "!previousController.form.contains(event.target)" in editor
        and "event.detail?.viewport || null" in workspace,
        "OUTSIDE_CANVAS_FINISH_AND_SAVE",
        "outside canvas click does not finish and save the active entry",
    )
    require(
        "[data-normative-menu]" in workspace
        and "isEditorOverlayTarget(event.target)" in editor,
        "EDITOR_OVERLAY_EXCLUSION",
        "normative editor overlays can incorrectly trigger completion",
    )
    require(
        all(f"?v={REVISION}" in source for source in (template, base))
        and all(
            f'const RUNTIME_REVISION = "{REVISION}";' in source
            for source in (editor, navigation)
        ),
        "PATCH_011_3_4_REPAIR3_CACHE_REVISION",
        "Repair 3 runtime cache revision is incomplete",
    )
    require(
        not list(
            (ROOT / "src/apps/operational_log/migrations").glob("0007*.py")
        ),
        "NO_DATABASE_SCHEMA_CHANGE",
        "Repair 3 must not introduce operational_log migration 0007",
    )
    print("PATCH_011_3_4_REPAIR3_STABLE_FINISH_EMERGENCY_GATE_PASSED")


if __name__ == "__main__":
    main()
