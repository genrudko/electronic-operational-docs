from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ..editor import (
    EDITOR_SCHEMA_VERSION,
    LEGACY_EDITOR_SCHEMA_VERSIONS,
    editor_document_to_text,
    normalize_editor_document,
)
from ..forms import DraftEntryAutoSaveForm
from ..models import DraftRevisionAction
from ..services import update_draft_entry
from .base import OperationalLogTestCase


class SemanticEditorDocumentTests(SimpleTestCase):
    def semantic_document(
        self,
        kind: str,
        label: str,
        reference: str = "",
    ) -> dict:
        semantic = {"kind": kind, "label": label}
        if reference:
            semantic["reference"] = reference
        return {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {
                            "text": "клиентская проекция",
                            "marks": [],
                            "semantic": semantic,
                        }
                    ],
                }
            ],
        }

    def test_legacy_v1_document_is_upgraded_without_text_loss(self) -> None:
        legacy_version = next(iter(LEGACY_EDITOR_SCHEMA_VERSIONS))
        document = normalize_editor_document(
            {
                "schema_version": legacy_version,
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
        self.assertEqual(editor_document_to_text(document), "Старая запись")

    def test_command_has_authoritative_plain_text_projection(self) -> None:
        document = normalize_editor_document(
            self.semantic_document("command", "включить В-35")
        )
        self.assertEqual(
            editor_document_to_text(document),
            "Команда: включить В-35",
        )
        segment = document["blocks"][0]["segments"][0]
        self.assertEqual(segment["text"], "Команда: включить В-35")

    def test_reference_semantic_preserves_normalized_reference(self) -> None:
        document = normalize_editor_document(
            self.semantic_document(
                "equipment",
                "В-35 Т-1-8",
                "equipment:demo-35",
            )
        )
        segment = document["blocks"][0]["segments"][0]
        self.assertEqual(editor_document_to_text(document), "В-35 Т-1-8")
        self.assertEqual(
            segment["semantic"]["reference"],
            "equipment:demo-35",
        )

    def test_unknown_semantic_kind_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_editor_document(
                self.semantic_document("dangerous_html", "текст")
            )

    def test_unknown_semantic_field_is_rejected(self) -> None:
        document = self.semantic_document("message", "текст")
        document["blocks"][0]["segments"][0]["semantic"]["html"] = "<b>x</b>"
        with self.assertRaises(ValidationError):
            normalize_editor_document(document)

    def test_empty_semantic_label_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_editor_document(
                self.semantic_document("warning", "   ")
            )

    def test_plain_segments_do_not_merge_through_semantic_token(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": EDITOR_SCHEMA_VERSION,
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {"text": "Отключить ", "marks": []},
                            {
                                "text": "неавторитетно",
                                "marks": [],
                                "semantic": {
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

    def test_carryover_projection_is_explicit(self) -> None:
        document = normalize_editor_document(
            self.semantic_document("carryover", "контроль заявки № 15")
        )
        self.assertEqual(
            editor_document_to_text(document),
            "На следующую смену: контроль заявки № 15",
        )

    def test_autosave_form_accepts_legacy_schema_and_normalizes_payload(self) -> None:
        legacy_version = next(iter(LEGACY_EDITOR_SCHEMA_VERSIONS))
        form = DraftEntryAutoSaveForm(
            data={
                "public_id": "00000000-0000-0000-0000-000000000001",
                "expected_version": 1,
                "event_at": "2026-07-19T00:00",
                "content": "старое содержание",
                "editor_schema_version": legacy_version,
                "editor_payload": {
                    "schema_version": legacy_version,
                    "blocks": [
                        {
                            "type": "paragraph",
                            "segments": [
                                {"text": "старое содержание", "marks": []}
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


class SemanticEditorPersistenceTests(OperationalLogTestCase):
    def test_service_persists_semantic_payload_and_revision(self) -> None:
        entry = self.shift.draft_entries.filter(is_removed=False).first()
        document = {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {"text": "Получено ", "marks": []},
                        {
                            "text": "клиентская проекция",
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
        saved = update_draft_entry(
            entry=entry,
            actor=self.actor,
            expected_version=entry.version,
            event_at=entry.event_at,
            content="неавторитетная проекция",
            editor_payload=document,
        )
        self.assertEqual(
            saved.content,
            "Получено Разрешение: на включение В-35",
        )
        semantic = saved.editor_payload["blocks"][0]["segments"][1]
        self.assertEqual(semantic["semantic"]["kind"], "permission")
        revision = saved.revisions.order_by("-revision_number").first()
        self.assertEqual(revision.action, DraftRevisionAction.UPDATED)
        self.assertEqual(
            revision.snapshot["draft"]["editor_payload"],
            saved.editor_payload,
        )
