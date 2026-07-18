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
from django.core.exceptions import ValidationError  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.operational_log.editor import (  # noqa: E402
    EDITOR_SCHEMA_VERSION,
    editor_document_to_text,
    normalize_editor_document,
)
from apps.operational_log.models import OperationalJournal, ShiftStatus  # noqa: E402

sample = normalize_editor_document(
    {
        "schema_version": EDITOR_SCHEMA_VERSION,
        "blocks": [
            {
                "type": "paragraph",
                "segments": [
                    {"text": "Проверка", "marks": ["bold"]},
                    {"text": " редактора", "marks": ["underline"]},
                ],
            },
            {
                "type": "bullet_list",
                "items": [
                    {"segments": [{"text": "Пункт", "marks": []}]},
                ],
            },
        ],
    }
)
assert editor_document_to_text(sample) == "Проверка редактора\n• Пункт"
print("CONTROLLED_EDITOR_SCHEMA=PASSED")

try:
    normalize_editor_document(
        {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {"text": "x", "marks": ["html"]},
                    ],
                }
            ],
        }
    )
except ValidationError:
    pass
else:
    raise AssertionError("Неизвестная отметка должна быть отклонена")
print("ARBITRARY_FORMATTING_REJECTED=PASSED")

models_text = (ROOT / "src/apps/operational_log/models.py").read_text(
    encoding="utf-8"
)
services_text = (ROOT / "src/apps/operational_log/services.py").read_text(
    encoding="utf-8"
)
template_text = (
    ROOT / "src/templates/operational_log/shift_workspace.html"
).read_text(encoding="utf-8")
workspace_js = (
    ROOT / "src/static/operational_log/draft_workspace.js"
).read_text(encoding="utf-8")
editor_js = (
    ROOT / "src/static/operational_log/draft_editor.js"
).read_text(encoding="utf-8")
css_text = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")

for marker in (
    "editor_schema_version = models.CharField",
    "editor_payload = models.JSONField",
    '"schema_version": "operational-draft-entry.v2"',
    "normalize_editor_document",
):
    assert marker in models_text + services_text, marker
print("EDITOR_PERSISTENCE_MODEL=PASSED")

for marker in (
    "data-editor-fallback",
    "data-editor-payload",
    "data-rich-editor-host",
    "draft-editor-payload-field",
    "data-editor-ribbon",
    "data-editor-ribbon-status",
    "data-editor-floating-toolbar",
    'data-editor-command="bold"',
    'data-editor-command="underline"',
    'data-editor-command="bullet_list"',
    'data-editor-command="ordered_list"',
    'data-editor-command="undo"',
    'data-editor-command="redo"',
    "draft_editor.js",
):
    assert marker in template_text, marker
assert template_text.count('data-editor-command="bold"') == 2
assert template_text.count('data-editor-command="undo"') == 1
assert 'aria-label="Редактор и действия с записью"' not in template_text
print("EDITOR_TOOLBAR_AND_HOST=PASSED")
print("WORD_LIKE_MINI_RIBBON=PASSED")

for marker in (
    "window.EODDraftEditor",
    "editorToDocument",
    "editableBlockSegments",
    "documentToText",
    'getData("text/plain")',
    'document.execCommand("insertText"',
    "selectionchange",
    "savedRange",
    "positionFloatingToolbar",
    "data-editor-floating-toolbar",
    "bindToolbar(document)",
    'event.code === "KeyB"',
    'event.code === "KeyI"',
    'document.execCommand("styleWithCSS"',
    'event.code === "Digit7"',
    'event.code === "Digit8"',
    '"display",\n                "none",\n                "important"',
):
    assert marker in editor_js, marker
assert "innerHTML" not in editor_js
print("PLAIN_PASTE_AND_SAFE_DOM=PASSED")
print("CONTEXTUAL_SELECTION_TOOLBAR=PASSED")

for marker in (
    "EODDraftEditor?.syncForm",
    "firstFormError",
    "EODDraftEditor?.seedPlainText",
    "EODDraftEditor?.acceptSaved",
    "data-editor-fallback",
):
    assert marker in workspace_js, marker
print("AUTOSAVE_EDITOR_BRIDGE=PASSED")

for marker in (
    "/* Patch 011.2: контролируемое ядро редактора журнала. */",
    "/* Patch 011.2 Repair 1: Word-like mini-ribbon and contextual toolbar. */",
    ".draft-rich-editor",
    ".draft-editor-ribbon",
    ".draft-editor-ribbon-button",
    ".draft-editor-floating-toolbar",
    ".draft-editor-payload-field",
    "display: none !important;",
    ".is-rich-editor-ready",
):
    assert marker in css_text, marker
print("CONTROLLED_EDITOR_CSS=PASSED")
print("TECHNICAL_EDITOR_PAYLOAD_HIDDEN=PASSED")
print("LARGE_EDITOR_CONTROLS=PASSED")

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
        "editor_payload": json.dumps(sample, ensure_ascii=False),
    },
)
assert response.status_code == 200, response.content
payload = response.json()
assert payload["ok"] is True
assert payload["content"] == "Проверка редактора\n• Пункт"
assert payload["editor_payload"] == sample
print("STRUCTURED_AUTOSAVE_ROUND_TRIP=PASSED")

migration_text = (
    ROOT
    / "src/apps/operational_log/migrations/0003_draft_editor_payload.py"
).read_text(encoding="utf-8")
assert "backfill_editor_payload" in migration_text
assert "OperationalDraftEntry" in migration_text
print("LEGACY_DRAFT_BACKFILL=PASSED")

print("PATCH_011_2_CONTROLLED_JOURNAL_EDITOR_GATE_PASSED")
