from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVISION = "011352"


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition: bool, marker: str, message: str) -> None:
    if not condition:
        raise RuntimeError(message)
    print(f"{marker}=PASSED")


def main() -> None:
    base = read("src/templates/base.html")
    template = read("src/templates/operational_log/shift_workspace.html")
    css = read("src/static/system/app.css")
    app_js = read("src/static/system/app.js")
    workspace = read("src/static/operational_log/draft_workspace.js")
    editor = read("src/static/operational_log/draft_editor.js")
    navigation = read("src/static/operational_log/draft_reference_navigation.js")

    require(
        "shift-book-summary-bar" in template
        and "Рабочий черновик" in template
        and "Автосохранение включено" in template
        and "shift-book-clean-copy" not in template,
        "COMPACT_JOURNAL_SUMMARY",
        "journal heading is not the compact non-sticky summary bar",
    )
    require(
        "draft-command-primary-row" in template
        and template.count("data-page-navigation") == 1
        and "draft-clean-copy-action" in template,
        "UNIFIED_COMMAND_SURFACE",
        "controls and pagination are not integrated into one command surface",
    )
    panel_index = template.index("data-open-view-drawer")
    toggle_index = template.index("data-ribbon-mode-toggle")
    clean_copy_index = template.index("draft-clean-copy-action")
    require(
        'data-ribbon-mode="compact"' in template
        and "draft-ribbon-mode-label" in template
        and "draft-ribbon-mode-chevron" in template
        and "data-ribbon-mode-icon" not in template
        and 'title="Развернуть ленту редактора"' not in template
        and panel_index < toggle_index < clean_copy_index
        and "eod.operationalJournal.ribbonMode" in workspace
        and "function applyRibbonMode" in workspace
        and "data-ribbon-mode-icon" not in workspace
        and "ribbonModeToggle.title" not in workspace
        and '.draft-ribbon-mode-toggle[aria-expanded="true"]' in css,
        "COMPACT_RIBBON_DEFAULT",
        "compact/expanded Ribbon control is not integrated into command actions",
    )
    require(
        "--draft-page-navigation-top" not in workspace
        and "--draft-command-bar-height" not in workspace
        and "new ResizeObserver" not in workspace
        and ".draft-page-navigation {" in css
        and "position: static;" in css,
        "INDEPENDENT_STICKY_PAGINATION_REMOVED",
        "obsolete sticky pagination measurement remains",
    )
    require(
        all(
            token in css
            for token in (
                "--layer-journal-sticky",
                "--layer-editor-overlay",
                "--layer-drawer",
                "--layer-toast",
                "--layer-global-header",
                "--layer-global-menu",
            )
        )
        and "data-nav-menu-panel" in base
        and "function positionMenu(menu)" in app_js
        and "closeMenu(activeMenu, true)" in app_js,
        "GLOBAL_OVERLAY_LAYER_CONTRACT",
        "global navigation overlay hierarchy or accessibility is incomplete",
    )
    require(
        all(f"?v={REVISION}" in source for source in (template, base))
        and f"system/app.js' %}}?v={REVISION}" in base
        and all(
            f'const RUNTIME_REVISION = "{REVISION}";' in source
            for source in (editor, navigation)
        ),
        "PATCH_011_3_5_CACHE_REVISION",
        "Patch 011.3.5 runtime cache revision is incomplete",
    )
    require(
        "https://cdn" not in base.lower()
        and "https://cdn" not in template.lower()
        and "G:\\" not in app_js
        and "G:\\" not in workspace,
        "PORTABLE_LOCAL_RUNTIME_ASSETS",
        "platform-specific or external runtime dependency was introduced",
    )
    require(
        not list((ROOT / "src/apps/operational_log/migrations").glob("0007*.py")),
        "NO_DATABASE_SCHEMA_CHANGE",
        "Patch 011.3.5 must not introduce operational_log migration 0007",
    )
    print("PATCH_011_3_5_COMPACT_WORKSPACE_OVERLAY_GATE_PASSED")


if __name__ == "__main__":
    main()
