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
    views = read("src/apps/operational_log/views.py")
    forms = read("src/apps/operational_log/forms.py")
    editor = read("src/static/operational_log/draft_editor.js")
    workspace = read("src/static/operational_log/draft_workspace.js")
    navigation = read(
        "src/static/operational_log/draft_reference_navigation.js"
    )
    template = read("src/templates/operational_log/shift_workspace.html")
    base = read("src/templates/base.html")
    css = read("src/static/system/app.css")
    models = read("src/apps/organizations/models.py")
    context = read("src/apps/organizations/context_processors.py")
    migration = read(
        "src/apps/organizations/migrations/"
        "0006_journal_simplified_time_input.py"
    )

    require(
        "function personCompositeMatches" in editor
        and "priority: 110" in editor
        and "match.start < current.end" in editor
        and "source.map((value) => normalizeSingleLine(value))" in editor,
        "CONTEXT_AWARE_LONGEST_ENTITY",
        "context-aware longest entity selection is incomplete",
    )
    require(
        "_position_reference_terms" in views
        and 'acronym_parts.append("ЭМ")' in views
        and '"position_terms"' in views
        and "function personCompositeMatches" in editor
        and "includeMetadata: false" in editor,
        "POSITION_SURNAME_SINGLE_ENTITY",
        "position and surname are not resolved as one person entity",
    )
    require(
        "function equipmentTermPattern" in editor
        and "0*${numeric}" in editor
        and "equipmentLetterPattern" in editor
        and "trailingNumericPart" in editor,
        "EQUIPMENT_NUMERIC_NORMALIZATION",
        "equipment separators or leading zero normalization is incomplete",
    )
    require(
        "function refreshRelatedEntryCatalog" in editor
        and "[data-draft-card][data-draft-id]" in editor
        and "referenceCatalog.related_entry = items" in editor
        and '"event_time"' in views,
        "LIVE_RELATED_ENTRY_CATALOG",
        "related entry catalog is not refreshed from current rows",
    )
    require(
        "function relatedEntryTimeMatches" in editor
        and "function relatedEntryCueBefore" in editor
        and "item.event_at < currentAt" in editor
        and "priority: 130" in editor,
        "CONTEXTUAL_ENTRY_TIME_REFERENCE",
        "contextual references to earlier journal times are incomplete",
    )
    require(
        "journal_simplified_time_input" in models
        and "journal_simplified_time_input" in forms
        and "journal_simplified_time_input=False" in context
        and "journal_simplified_time_input" in migration
        and "data-simplified-time-toggle" in template
        and "eod:simplified-time-setting" in workspace,
        "USER_SIMPLIFIED_TIME_PREFERENCE",
        "user-scoped simplified time preference is incomplete",
    )
    require(
        "function simplifiedTimeValue" in editor
        and "function editableTextPositionBeforeCaret" in editor
        and "numeric >= 1900 && numeric <= 2099" in editor
        and "[\\p{L}\\p{N}№#\\-–—./]" in editor
        and "scheduleAutomaticReferences(controller, 40)" in editor,
        "SAFE_INLINE_TIME_SHORTHAND",
        "safe simplified time conversion in record text is incomplete",
    )
    require(
        f'const RUNTIME_REVISION = "{REVISION}";' in editor
        and f'const RUNTIME_REVISION = "{REVISION}";' in navigation
        and template.count(f"?v={REVISION}") == 3
        and f"?v={REVISION}" in base
        and ".draft-simplified-time-toggle.is-active" in css,
        "PATCH_011_3_3_CACHE_REVISION",
        "Patch 011.3.3 asset revision or visual contract is incomplete",
    )
    require(
        {
            path.name
            for path in (
                ROOT / "src/apps/operational_log/migrations"
            ).glob("0006*.py")
        }
        == {"0006_alter_operationaldraftentry_editor_schema_version.py"}
        and (
            ROOT
            / "src/apps/organizations/migrations/"
            "0006_journal_simplified_time_input.py"
        ).is_file(),
        "SCOPED_PREFERENCE_AND_EDITOR_MIGRATIONS",
        "unexpected migration scope",
    )
    print("PATCH_011_3_3_CONTEXT_AWARE_ENTITY_RESOLVER_GATE_PASSED")


if __name__ == "__main__":
    main()
