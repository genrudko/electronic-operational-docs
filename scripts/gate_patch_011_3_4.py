from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
REVISION = "011343"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")

import django  # noqa: E402

django.setup()

from apps.operational_log.editor import (  # noqa: E402
    ALLOWED_MARKS,
    EDITOR_SCHEMA_VERSION,
    editor_document_to_text,
    normalize_editor_document,
)


def read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def require(condition: bool, marker: str, message: str) -> None:
    if not condition:
        raise RuntimeError(message)
    print(f"{marker}=PASSED")


def main() -> None:
    editor_py = read("src/apps/operational_log/editor.py")
    views = read("src/apps/operational_log/views.py")
    editor_js = read("src/static/operational_log/draft_editor.js")
    workspace_js = read("src/static/operational_log/draft_workspace.js")
    navigation = read(
        "src/static/operational_log/draft_reference_navigation.js"
    )
    template = read("src/templates/operational_log/shift_workspace.html")
    base = read("src/templates/base.html")
    css = read("src/static/system/app.css")
    migration = read(
        "src/apps/operational_log/migrations/"
        "0006_alter_operationaldraftentry_editor_schema_version.py"
    )

    require(
        EDITOR_SCHEMA_VERSION == "operational-draft-editor.v4"
        and '"annotations"' in editor_py
        and {
            "bold",
            "italic",
            "underline",
            "strike",
            "text_red",
            "text_blue",
        }
        <= ALLOWED_MARKS,
        "STRUCTURED_EDITOR_SCHEMA_V4",
        "editor v4 or safe formatting whitelist is incomplete",
    )

    install_id = "normative_source_0001"
    normalized = normalize_editor_document(
        {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "entry_kind": "normal",
            "annotations": [
                {
                    "id": install_id,
                    "kind": "pz_install",
                    "label": "Установлено ПЗ №109",
                    "pz_number": "№109",
                }
            ],
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {
                            "text": "Установлено ПЗ №109",
                            "marks": ["text_red"],
                            "annotations": [install_id],
                        }
                    ],
                }
            ],
        }
    )
    require(
        normalized["annotations"][0]["pz_number"] == "109"
        and editor_document_to_text(normalized) == "Установлено ПЗ №109",
        "NUMBERED_PZ_SEMANTICS",
        "PZ number or plain-text projection is invalid",
    )

    require(
        all(
            marker in editor_js
            for marker in (
                "function activeNormativeSources",
                "function showNormativeSourceStep",
                "function showPzNumberStep",
                "source_entry: source.entry_reference",
                "source_annotation: source.id",
                "function closedNormativeIds",
                "is-normative-cleared",
            )
        ),
        "LINKED_INSTALL_REMOVE_LIFECYCLE",
        "installation/removal lifecycle is incomplete",
    )

    require(
        all(
            marker in template
            for marker in (
                "data-normative-trigger",
                "data-normative-menu",
                'data-normative-action="emergency"',
                'data-normative-action="zn_on"',
                'data-normative-action="zn_off"',
                'data-normative-action="pz_install"',
                'data-normative-action="pz_remove"',
                "data-draft-visas",
            )
        ),
        "NORMATIVE_MARK_ACTION_UI",
        "normative action UI is incomplete",
    )

    require(
        'top.textContent = annotation.kind.startsWith("pz_") ? "ПЗ" : "ЗН";'
        in editor_js
        and "draft-normative-marker-bolt" in editor_js
        and 'bottom.textContent = annotation.pz_number ? `№${annotation.pz_number}` : "";'
        in editor_js
        and "draft-normative-marker-cross" in editor_js,
        "PZ_UPPER_LABEL_LOWER_NUMBER",
        "PZ marker does not have upper label, bolt and lower number",
    )

    require(
        all(
            marker in css
            for marker in (
                ".draft-normative-text.is-normative-open",
                ".draft-normative-text.is-normative-close",
                ".is-normative-open.is-normative-cleared",
                ".draft-normative-marker.is-cleared",
                "rotate(45deg)",
                "rotate(-45deg)",
                ".draft-ledger-row.is-emergency-event",
            )
        ),
        "RED_BLUE_UNDERLINES_AND_BLUE_X",
        "red/blue underlines, blue X or emergency outline is missing",
    )

    require(
        "preview" in views
        and "draft-reference-preview-summary" in navigation
        and "draft-reference-preview-facts" in navigation
        and "draft-reference-preview-technical" in navigation
        and "function renderPreviewFacts(facts)" in navigation
        and "eod:reference-catalog-updated" in editor_js
        and "eod:reference-catalog-updated" in navigation,
        "RICH_SEMANTIC_REFERENCE_PREVIEWS",
        "rich semantic previews are incomplete",
    )
    require(
        "innerHTML" not in editor_js and "innerHTML" not in navigation,
        "SAFE_DOM_ONLY",
        "unsafe innerHTML is forbidden",
    )

    require(
        f'const RUNTIME_REVISION = "{REVISION}";' in editor_js
        and f'const RUNTIME_REVISION = "{REVISION}";' in navigation
        and template.count(f"?v={REVISION}") == 3
        and f"?v={REVISION}" in base
        and "row.dataset.entryVersion" in workspace_js,
        "PATCH_011_3_4_CACHE_AND_LIVE_PREVIEW_REVISION",
        "runtime cache or live preview version refresh is incomplete",
    )

    require(
        "operational-draft-editor.v4" in migration
        and "0005_alter_operationaldraftentry_editor_schema_version"
        in migration,
        "EDITOR_V4_MIGRATION",
        "controlled editor v4 migration is missing",
    )

    print(
        "PATCH_011_3_4_RICH_PREVIEWS_NORMATIVE_MARKS_GATE_PASSED"
    )


if __name__ == "__main__":
    main()
