from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ..editor import (
    EDITOR_SCHEMA_VERSION,
    editor_document_to_text,
    normalize_editor_document,
)
from ..forms import DraftEntryAutoSaveForm
from ..models import DraftRevisionAction
from ..services import update_draft_entry
from .base import OperationalLogTestCase


class SemanticEditorDocumentTests(SimpleTestCase):
    def test_legacy_v1_document_is_upgraded_without_text_loss(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": "operational-draft-editor.v1",
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {"text": "Старая запись", "marks": ["bold"]}
                        ],
                    }
                ],
            }
        )
        self.assertEqual(document["schema_version"], EDITOR_SCHEMA_VERSION)
        self.assertEqual(document["entry_kind"], "normal")
        self.assertEqual(editor_document_to_text(document), "Старая запись")

    def test_legacy_v2_command_becomes_record_type(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": "operational-draft-editor.v2",
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {
                                "text": "клиентская проекция",
                                "marks": [],
                                "semantic": {
                                    "kind": "command",
                                    "label": "отключить В-35",
                                },
                            }
                        ],
                    }
                ],
            }
        )
        self.assertEqual(document["entry_kind"], "command")
        self.assertEqual(
            document["blocks"][0]["segments"][0]["text"],
            "отключить В-35",
        )
        self.assertEqual(
            editor_document_to_text(document),
            "Команда: отключить В-35",
        )

    def test_v3_record_type_has_authoritative_projection(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": EDITOR_SCHEMA_VERSION,
                "entry_kind": "warning",
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [{"text": "Не включать В-35", "marks": []}],
                    }
                ],
            }
        )
        self.assertEqual(
            editor_document_to_text(document),
            "Предупреждение: Не включать В-35",
        )

    def test_inline_equipment_reference_preserves_plain_text(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": EDITOR_SCHEMA_VERSION,
                "entry_kind": "command",
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {"text": "Отключить ", "marks": []},
                            {
                                "text": "подмена клиента",
                                "marks": ["bold"],
                                "reference": {
                                    "kind": "equipment",
                                    "label": "В-35 Т-1",
                                    "reference": "equipment:demo-35",
                                },
                            },
                        ],
                    }
                ],
            }
        )
        segment = document["blocks"][0]["segments"][1]
        self.assertEqual(segment["text"], "В-35 Т-1")
        self.assertEqual(segment["reference"]["reference"], "equipment:demo-35")
        self.assertEqual(
            editor_document_to_text(document),
            "Команда: Отключить В-35 Т-1",
        )

    def test_unknown_entry_kind_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_editor_document(
                {
                    "schema_version": EDITOR_SCHEMA_VERSION,
                    "entry_kind": "dangerous_html",
                    "blocks": [{"type": "paragraph", "segments": []}],
                }
            )

    def test_unknown_reference_kind_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_editor_document(
                {
                    "schema_version": EDITOR_SCHEMA_VERSION,
                    "entry_kind": "normal",
                    "blocks": [
                        {
                            "type": "paragraph",
                            "segments": [
                                {
                                    "text": "x",
                                    "marks": [],
                                    "reference": {
                                        "kind": "script",
                                        "label": "x",
                                    },
                                }
                            ],
                        }
                    ],
                }
            )

    def test_unknown_reference_field_is_rejected(self) -> None:
        payload = {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "entry_kind": "normal",
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {
                            "text": "В-35",
                            "marks": [],
                            "reference": {
                                "kind": "equipment",
                                "label": "В-35",
                                "html": "<b>x</b>",
                            },
                        }
                    ],
                }
            ],
        }
        with self.assertRaises(ValidationError):
            normalize_editor_document(payload)

    def test_plain_segments_do_not_merge_through_reference(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": EDITOR_SCHEMA_VERSION,
                "entry_kind": "normal",
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {"text": "Отключить ", "marks": []},
                            {
                                "text": "В-35",
                                "marks": [],
                                "reference": {
                                    "kind": "equipment",
                                    "label": "В-35",
                                },
                            },
                            {"text": " для ремонта", "marks": []},
                        ],
                    }
                ],
            }
        )
        self.assertEqual(len(document["blocks"][0]["segments"]), 3)
        self.assertEqual(
            editor_document_to_text(document),
            "Отключить В-35 для ремонта",
        )

    def test_autosave_form_accepts_legacy_v2_and_normalizes_to_v3(self) -> None:
        form = DraftEntryAutoSaveForm(
            data={
                "public_id": "00000000-0000-0000-0000-000000000001",
                "expected_version": 1,
                "event_at": "2026-07-19T00:00",
                "content": "Команда: отключить В-35",
                "editor_schema_version": "operational-draft-editor.v2",
                "editor_payload": {
                    "schema_version": "operational-draft-editor.v2",
                    "blocks": [
                        {
                            "type": "paragraph",
                            "segments": [
                                {
                                    "text": "x",
                                    "marks": [],
                                    "semantic": {
                                        "kind": "command",
                                        "label": "отключить В-35",
                                    },
                                }
                            ],
                        }
                    ],
                },
            }
        )
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["editor_payload"]["schema_version"],
            EDITOR_SCHEMA_VERSION,
        )
        self.assertEqual(
            form.cleaned_data["editor_payload"]["entry_kind"],
            "command",
        )


class SemanticEditorPersistenceTests(OperationalLogTestCase):
    def test_service_persists_record_type_reference_and_revision(self) -> None:
        entry = self.shift.draft_entries.filter(is_removed=False).first()
        document = {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "entry_kind": "permission",
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {"text": "На включение ", "marks": []},
                        {
                            "text": "В-35",
                            "marks": ["bold"],
                            "reference": {
                                "kind": "equipment",
                                "label": "В-35",
                                "reference": "equipment:demo-1",
                            },
                        },
                    ],
                }
            ],
        }
        saved = update_draft_entry(
            entry=entry,
            actor=self.actor,
            expected_version=entry.version,
            event_at=entry.event_at,
            content="неавторитетная проекция",
            editor_payload=document,
        )
        self.assertEqual(saved.content, "Разрешение: На включение В-35")
        self.assertEqual(saved.editor_payload["entry_kind"], "permission")
        reference = saved.editor_payload["blocks"][0]["segments"][1]
        self.assertEqual(reference["reference"]["kind"], "equipment")
        revision = saved.revisions.order_by("-revision_number").first()
        self.assertEqual(revision.action, DraftRevisionAction.UPDATED)
        self.assertEqual(
            revision.snapshot["draft"]["editor_payload"],
            saved.editor_payload,
        )
