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
    workspace = read("src/static/operational_log/draft_workspace.js")
    editor = read("src/static/operational_log/draft_editor.js")
    navigation = read(
        "src/static/operational_log/draft_reference_navigation.js"
    )
    template = read("src/templates/operational_log/shift_workspace.html")
    base = read("src/templates/base.html")

    require(
        'form.dataset.finishing !== "true"' in workspace
        and "&& !form.contains(document.activeElement)" in workspace,
        "FINISH_TRANSACTION_SUPPRESSES_AUTO_REVEAL",
        "save can still start smooth chronology reveal during completion",
    )
    immediate_marker = (
        "// Chromium cannot paint the temporary row-store position."
    )
    require(
        immediate_marker in workspace
        and workspace.index("        restore();", workspace.index(immediate_marker))
        < workspace.index(
            "        window.requestAnimationFrame(() => {",
            workspace.index(immediate_marker),
        ),
        "SAME_TASK_VIEWPORT_RESTORE",
        "viewport anchor is restored only after a paint opportunity",
    )
    require(
        "window.scrollBy({" in workspace
        and "window.scrollTo({" in workspace
        and workspace.count('behavior: "auto"') >= 2,
        "NON_SMOOTH_PROGRAMMATIC_RESTORE",
        "programmatic viewport restoration can still animate",
    )
    require(
        'const chronologyApplied = applyPendingChronology(form, {'
        in workspace
        and "            scroll: false," in workspace
        and "            viewport," in workspace,
        "COMPLETION_USES_ANCHORED_CHRONOLOGY",
        "completion no longer routes chronology through the anchored path",
    )
    require(
        all(f"?v={REVISION}" in source for source in (template, base))
        and all(
            f'const RUNTIME_REVISION = "{REVISION}";' in source
            for source in (editor, navigation)
        ),
        "PATCH_011_3_4_REPAIR4_CACHE_REVISION",
        "Repair 4 runtime cache revision is incomplete",
    )
    require(
        not list(
            (ROOT / "src/apps/operational_log/migrations").glob("0007*.py")
        ),
        "NO_DATABASE_SCHEMA_CHANGE",
        "Repair 4 must not introduce operational_log migration 0007",
    )
    print("PATCH_011_3_4_REPAIR4_ATOMIC_VIEWPORT_RESTORE_GATE_PASSED")


if __name__ == "__main__":
    main()
