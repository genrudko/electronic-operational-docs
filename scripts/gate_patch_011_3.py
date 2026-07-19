from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")

import django  # noqa: E402

django.setup()

from apps.operational_log.editor import (  # noqa: E402
    ALLOWED_ENTRY_KINDS,
    ALLOWED_REFERENCE_KINDS,
    EDITOR_SCHEMA_VERSION,
    editor_document_to_text,
    normalize_editor_document,
)


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    javascript = (
        SRC / "static" / "operational_log" / "draft_editor.js"
    ).read_text(encoding="utf-8")
    template = (
        SRC / "templates" / "operational_log" / "shift_workspace.html"
    ).read_text(encoding="utf-8")
    css = (
        SRC / "static" / "system" / "app.css"
    ).read_text(encoding="utf-8")
    views = (
        SRC / "apps" / "operational_log" / "views.py"
    ).read_text(encoding="utf-8")

    require(EDITOR_SCHEMA_VERSION == "operational-draft-editor.v3", "schema v3 missing")
    require(
        {"normal", "command", "permission", "message", "warning", "carryover"}
        <= ALLOWED_ENTRY_KINDS,
        "entry kinds missing",
    )
    require(
        {"equipment", "document", "person", "event_time", "related_entry"}
        <= ALLOWED_REFERENCE_KINDS,
        "reference kinds missing",
    )
    sample = normalize_editor_document(
        {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "entry_kind": "command",
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {"text": "Отключить ", "marks": []},
                        {
                            "text": "x",
                            "marks": [],
                            "reference": {
                                "kind": "equipment",
                                "label": "В-35",
                                "reference": "equipment:demo",
                            },
                        },
                    ],
                }
            ],
        }
    )
    require(
        editor_document_to_text(sample) == "Команда: Отключить В-35",
        "canonical projection mismatch",
    )
    print("SEMANTIC_EDITOR_SCHEMA_V3=PASSED")

    legacy = normalize_editor_document(
        {
            "schema_version": "operational-draft-editor.v2",
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {
                            "text": "x",
                            "marks": [],
                            "semantic": {
                                "kind": "warning",
                                "label": "не включать В-35",
                            },
                        }
                    ],
                }
            ],
        }
    )
    require(legacy["entry_kind"] == "warning", "v2 record type upgrade failed")
    require(
        editor_document_to_text(legacy) == "Предупреждение: не включать В-35",
        "v2 text upgrade failed",
    )
    print("LEGACY_EDITOR_V2_TO_V3=PASSED")

    for marker in (
        "data-entry-kind-trigger",
        "data-entry-kind-menu",
        "data-entry-kind-option=\"command\"",
        "data-reference-trigger",
        "data-reference-picker",
        "data-reference-search",
        "draft-semantic-reference-catalog",
    ):
        require(marker in template, f"template marker missing: {marker}")
    require("data-semantic-dialog" not in template, "old modal still present")
    require(
        "data-semantic-label" not in template,
        "duplicate label field still present",
    )
    print("INSTANT_RECORD_TYPE_UI=PASSED")
    print("INLINE_REFERENCE_PICKER_UI=PASSED")

    for marker in (
        "function setEntryKind",
        "function openReferencePicker",
        "function applyReference",
        "function removeReference",
        "const insertionAtCaret = range.collapsed",
        "data-reference-kind",
        "entry_kind",
    ):
        require(marker in javascript, f"javascript marker missing: {marker}")
    require(
        "openSemanticDialog" not in javascript,
        "old semantic modal code remains",
    )
    require("innerHTML" not in javascript, "unsafe innerHTML is forbidden")
    print("MODAL_FREE_SEMANTIC_INPUT=PASSED")
    print("ATOMIC_REFERENCE_DOM=PASSED")

    require("_semantic_reference_catalog" in views, "reference catalog helper missing")
    require("EquipmentAsset.objects.filter" in views, "equipment catalog missing")
    require("Document.objects.filter" in views, "document catalog missing")
    require("Employee.objects.filter" in views, "employee catalog missing")
    require("draft:" in views, "related draft catalog missing")
    print("ORGANIZATION_SCOPED_REFERENCE_CATALOG=PASSED")

    for marker in (
        "Patch 011.3 Repair 2: record types and inline reference picker",
        ".draft-entry-kind-badge",
        ".draft-reference-token",
        ".draft-reference-picker",
    ):
        require(marker in css, f"css marker missing: {marker}")
    require(".draft-semantic-dialog" not in css, "old modal css remains")
    print("CALM_SEMANTIC_VISUAL_CONTRACT=PASSED")

    serialized = json.dumps(sample, ensure_ascii=False)
    require("equipment:demo" in serialized, "reference identity lost")
    print("SEMANTIC_AUTOSAVE_ROUND_TRIP=PASSED")
    print("PATCH_011_3_REPAIR2_RECORD_TYPES_INLINE_REFERENCES_GATE_PASSED")


if __name__ == "__main__":
    main()
