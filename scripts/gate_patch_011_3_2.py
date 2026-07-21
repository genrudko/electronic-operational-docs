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
    views = read("src/apps/operational_log/views.py")
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

    require(
        "data-inline-undo" in template
        and "showInlineRemovalPlaceholder" in workspace
        and "finalizeRemovedDraft" in workspace
        and "draft-inline-undo-button" in css
        and "data-draft-undo-stack" not in template,
        "INLINE_UNDO_AT_DELETED_ROW",
        "inline undo placeholder is incomplete",
    )
    require(
        "EquipmentAlias" in views
        and "active_reference_aliases" in views
        and '"terms":' in views,
        "REFERENCE_CATALOG_SEARCH_TERMS",
        "catalog aliases or search terms are missing",
    )
    require(
        "function russianSearchStem" in editor
        and "function levenshteinDistance" in editor
        and "function scoreReferenceItem" in editor
        and "termStems.some" in editor,
        "MORPHOLOGY_TOLERANT_REFERENCE_SEARCH",
        "morphology tolerant search is incomplete",
    )
    require(
        "data-auto-reference-toggle" in template
        and "data-auto-reference-scan" in template
        and "function applyAutomaticReferences" in editor
        and "function automaticReferenceSuggestion" in editor
        and "eod-auto-references" in editor,
        "AUTOMATIC_REFERENCE_MODE",
        "automatic reference mode is incomplete",
    )
    require(
        "candidates.length === 1" in editor
        and "data.autoReferenceCandidates" not in editor
        and "data-auto-reference-suggestion" in editor,
        "UNAMBIGUOUS_AUTO_LINK_POLICY",
        "ambiguous reference protection is incomplete",
    )
    require(
        "grid-template-columns: minmax(0, 1fr) auto;" in css
        and "balanced footer" in css
        and ".draft-ledger-lower" in css
        and ".draft-row-action-toolbar" in css,
        "BALANCED_RECORD_FOOTER",
        "balanced record footer is incomplete",
    )
    require(
        f'const RUNTIME_REVISION = "{REVISION}";' in editor
        and f'const RUNTIME_REVISION = "{REVISION}";' in navigation
        and template.count(f"?v={REVISION}") == 3
        and f"?v={REVISION}" in base,
        "PATCH_011_3_2_CACHE_REVISION",
        "cache revision is incomplete",
    )
    require(
        {path.name for path in (ROOT / "src/apps/operational_log/migrations").glob("0006*.py")}
        == {"0006_alter_operationaldraftentry_editor_schema_version.py"},
        "CONTROLLED_EDITOR_SCHEMA_EVOLUTION",
        "unexpected operational_log schema evolution detected",
    )
    print("PATCH_011_3_2_INLINE_UNDO_INTELLIGENT_REFERENCES_GATE_PASSED")


if __name__ == "__main__":
    main()
