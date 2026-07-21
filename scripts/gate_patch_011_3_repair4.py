from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
REVISION = "011342"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def require_markers(text: str, markers: tuple[str, ...], label: str) -> None:
    missing = [marker for marker in markers if marker not in text]
    require(not missing, f"{label}: missing markers {missing}")


def main() -> None:
    editor = (
        SRC / "static" / "operational_log" / "draft_editor.js"
    ).read_text(encoding="utf-8")
    workspace = (
        SRC / "static" / "operational_log" / "draft_workspace.js"
    ).read_text(encoding="utf-8")
    navigation = (
        SRC
        / "static"
        / "operational_log"
        / "draft_reference_navigation.js"
    ).read_text(encoding="utf-8")
    template = (
        SRC / "templates" / "operational_log" / "shift_workspace.html"
    ).read_text(encoding="utf-8")
    base_template = (SRC / "templates" / "base.html").read_text(
        encoding="utf-8"
    )
    css = (SRC / "static" / "system" / "app.css").read_text(
        encoding="utf-8"
    )

    require_markers(
        editor,
        (
            f'const RUNTIME_REVISION = "{REVISION}";',
            "function referenceWheelPixels(event)",
            "function handleReferencePickerWheel(event)",
            "surface.scrollTop = Math.max(",
            "event.preventDefault();",
            "event.stopPropagation();",
            'referencePicker?.addEventListener(',
            '"wheel",',
            "{passive: false},",
            "if (referencePicker && !referencePicker.hidden)",
        ),
        "reference picker wheel ownership",
    )
    print("REFERENCE_PICKER_WHEEL_OWNERSHIP=PASSED")

    require_markers(
        editor,
        (
            "function captureEntryKindViewport",
            "function restoreEntryKindViewport",
            "rowTop: row?.getBoundingClientRect().top ?? null",
            "window.requestAnimationFrame(restore);",
            "controller.editor.focus({preventScroll: true});",
            "restoreEntryKindViewport(controller);",
        ),
        "entry-kind viewport stability",
    )
    print("ENTRY_KIND_VIEWPORT_STABILITY=PASSED")

    require_markers(
        navigation,
        (
            f'const RUNTIME_REVISION = "{REVISION}";',
            "token.dataset.referenceValue",
            'token.getAttribute("data-reference-value")',
            "catalogByReference.get(identity)",
            'return { mode: "url", value: `/equipment/items/${rawId}/` };',
            'return { mode: "url", value: `/documents/${rawId}/` };',
            'return { mode: "url", value: "/organization/" };',
            'return { mode: "draft", value: rawId };',
        ),
        "reference target resolution",
    )
    require("innerHTML" not in navigation, "unsafe innerHTML is forbidden")
    print("REFERENCE_TARGET_RESOLUTION=PASSED")

    for asset in (
        "draft_editor.js",
        "draft_workspace.js",
        "draft_reference_navigation.js",
    ):
        require(
            f"operational_log/{asset}' %}}?v={REVISION}" in template,
            f"cache revision missing for {asset}",
        )
    require(
        f"system/app.css' %}}?v={REVISION}" in base_template,
        "cache revision missing for app.css",
    )
    print("RUNTIME_CACHE_REVISION=PASSED")

    editor_index = template.index("operational_log/draft_editor.js")
    workspace_index = template.index("operational_log/draft_workspace.js")
    navigation_index = template.index(
        "operational_log/draft_reference_navigation.js"
    )
    require(
        editor_index < workspace_index < navigation_index,
        "deferred script order is invalid",
    )
    require_markers(
        workspace,
        (
            "let editorOverlayActive = false;",
            '"eod:editor-overlay-state"',
            '"eod:reveal-draft-reference"',
            "revealChronologicalRow(row);",
        ),
        "workspace overlay contract",
    )
    print("WORKSPACE_OVERLAY_CONTRACT=PASSED")

    require_markers(
        css,
        (
            "Patch 011.3 Repair 4: validated runtime fixes",
            "overscroll-behavior: contain;",
            ".draft-reference-preview-actions > [hidden]",
            "display: none !important;",
            "z-index: 170;",
        ),
        "runtime visual contract",
    )
    print("REFERENCE_RUNTIME_VISUAL_CONTRACT=PASSED")

    migrations = {
        path.name
        for path in (
            SRC / "apps" / "operational_log" / "migrations"
        ).glob("0006*.py")
    }
    require(
        migrations
        == {"0006_alter_operationaldraftentry_editor_schema_version.py"},
        "unexpected operational_log schema evolution detected",
    )
    print("CONTROLLED_EDITOR_SCHEMA_EVOLUTION=PASSED")
    print("PATCH_011_3_REPAIR4_VALIDATED_RUNTIME_GATE_PASSED")


if __name__ == "__main__":
    main()
