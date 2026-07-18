from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")

import django  # noqa: E402

django.setup()

from django.contrib.auth import get_user_model  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.operational_log.editor import (  # noqa: E402
    EDITOR_SCHEMA_VERSION,
    LEGACY_EDITOR_SCHEMA_VERSIONS,
    editor_document_to_text,
    normalize_editor_document,
)
from apps.operational_log.models import OperationalJournal, ShiftStatus  # noqa: E402

semantic_document = normalize_editor_document(
    {
        "schema_version": EDITOR_SCHEMA_VERSION,
        "blocks": [
            {
                "type": "paragraph",
                "segments": [
                    {"text": "Получено ", "marks": []},
                    {
                        "text": "неавторитетно",
                        "marks": ["bold"],
                        "semantic": {
                            "kind": "permission",
                            "label": "на включение В-35",
                            "reference": "permission:demo-1",
                        },
                    },
                ],
            }
        ],
    }
)
assert semantic_document["schema_version"] == EDITOR_SCHEMA_VERSION
assert (
    editor_document_to_text(semantic_document)
    == "Получено Разрешение: на включение В-35"
)
print("SEMANTIC_EDITOR_SCHEMA_V2=PASSED")

legacy_version = next(iter(LEGACY_EDITOR_SCHEMA_VERSIONS))
legacy_document = normalize_editor_document(
    {
        "schema_version": legacy_version,
        "blocks": [
            {
                "type": "paragraph",
                "segments": [{"text": "Старая запись", "marks": []}],
            }
        ],
    }
)
assert legacy_document["schema_version"] == EDITOR_SCHEMA_VERSION
assert editor_document_to_text(legacy_document) == "Старая запись"
print("LEGACY_EDITOR_V1_COMPATIBILITY=PASSED")

template_text = (
    ROOT / "src/templates/operational_log/shift_workspace.html"
).read_text(encoding="utf-8")
editor_js = (
    ROOT / "src/static/operational_log/draft_editor.js"
).read_text(encoding="utf-8")
css_text = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
forms_text = (ROOT / "src/apps/operational_log/forms.py").read_text(
    encoding="utf-8"
)
editor_text = (ROOT / "src/apps/operational_log/editor.py").read_text(
    encoding="utf-8"
)

for marker in (
    "data-editor-semantic-trigger",
    "data-semantic-palette",
    "data-semantic-dialog",
    'data-semantic-option="command"',
    'data-semantic-option="permission"',
    'data-semantic-option="message"',
    'data-semantic-option="warning"',
    'data-semantic-option="equipment"',
    'data-semantic-option="document"',
    'data-semantic-option="person"',
    'data-semantic-option="event_time"',
    'data-semantic-option="related_entry"',
    'data-semantic-option="carryover"',
):
    assert marker in template_text, marker
assert template_text.count("data-editor-semantic-trigger") == 2
print("SEMANTIC_MINI_RIBBON_PALETTE=PASSED")

for marker in (
    "SEMANTIC_KINDS",
    "normalizeSemantic",
    "semanticProjection",
    "semanticToken",
    "insertSemantic",
    "updateSemanticToken",
    "openSemanticDialog",
    "bindSemanticUi",
    'event.code === "KeyM"',
    'contentEditable = "false"',
):
    assert marker in editor_js, marker
assert "innerHTML" not in editor_js
print("ATOMIC_SAFE_SEMANTIC_TOKENS=PASSED")

assert "SUPPORTED_EDITOR_SCHEMA_VERSIONS" in forms_text
assert "LEGACY_EDITOR_SCHEMA_VERSIONS" in editor_text
assert "SUPPORTED_EDITOR_SCHEMA_VERSIONS" in editor_text
print("SEMANTIC_FORM_COMPATIBILITY=PASSED")

for marker in (
    "/* Patch 011.3: semantic journal elements. */",
    ".draft-semantic-token",
    ".draft-semantic-palette",
    ".draft-semantic-dialog",
    ".draft-semantic-token-prefix",
):
    assert marker in css_text, marker
print("SEMANTIC_EDITOR_VISUAL_CONTRACT=PASSED")

user = get_user_model().objects.get(username="operator.demo")
journal = OperationalJournal.objects.get(code="shift-operational-log")
shift = journal.shifts.get(status=ShiftStatus.OPEN)
entry = shift.draft_entries.filter(is_removed=False).order_by("pk").first()
client = Client()
client.force_login(user)
response = client.post(
    reverse(
        "operational_log:autosave_draft",
        args=(journal.pk, entry.public_id),
    ),
    {
        "public_id": str(entry.public_id),
        "expected_version": entry.version,
        "event_at": timezone.localtime(entry.event_at).strftime(
            "%Y-%m-%dT%H:%M"
        ),
        "content": "неавторитетная проекция",
        "editor_schema_version": EDITOR_SCHEMA_VERSION,
        "editor_payload": json.dumps(
            semantic_document,
            ensure_ascii=False,
        ),
    },
)
assert response.status_code == 200, response.content
payload = response.json()
assert payload["ok"] is True
assert payload["content"] == "Получено Разрешение: на включение В-35"
assert (
    payload["editor_payload"]["blocks"][0]["segments"][1]["semantic"]["kind"]
    == "permission"
)
print("SEMANTIC_AUTOSAVE_ROUND_TRIP=PASSED")

print("PATCH_011_3_SEMANTIC_JOURNAL_ELEMENTS_GATE_PASSED")
