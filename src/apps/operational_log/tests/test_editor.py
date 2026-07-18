from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ..editor import (
    EDITOR_SCHEMA_VERSION,
    editor_document_to_text,
    normalize_editor_document,
    plain_text_to_editor_document,
)
from ..models import DraftRevisionAction
from ..services import update_draft_entry
from .base import OperationalLogTestCase


class ControlledEditorDocumentTests(SimpleTestCase):
    def test_plain_text_round_trip_preserves_paragraphs(self) -> None:
        document = plain_text_to_editor_document("Первая\n\nТретья")
        self.assertEqual(document["schema_version"], EDITOR_SCHEMA_VERSION)
        self.assertEqual(editor_document_to_text(document), "Первая\n\nТретья")
        empty = normalize_editor_document(plain_text_to_editor_document(""))
        self.assertEqual(editor_document_to_text(empty), "")

    def test_lists_have_stable_plain_text_projection(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": EDITOR_SCHEMA_VERSION,
                "blocks": [
                    {
                        "type": "bullet_list",
                        "items": [
                            {"segments": [{"text": "Первое", "marks": []}]},
                            {"segments": [{"text": "Второе", "marks": []}]},
                        ],
                    },
                    {
                        "type": "ordered_list",
                        "items": [
                            {"segments": [{"text": "Шаг", "marks": ["bold"]}]},
                        ],
                    },
                ],
            }
        )
        self.assertEqual(
            editor_document_to_text(document),
            "• Первое\n• Второе\n1. Шаг",
        )

    def test_unknown_mark_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_editor_document(
                {
                    "schema_version": EDITOR_SCHEMA_VERSION,
                    "blocks": [
                        {
                            "type": "paragraph",
                            "segments": [
                                {"text": "Текст", "marks": ["script"]},
                            ],
                        }
                    ],
                }
            )

    def test_unknown_structure_field_is_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_editor_document(
                {
                    "schema_version": EDITOR_SCHEMA_VERSION,
                    "blocks": [],
                    "html": "<b>не сохранять</b>",
                }
            )

    def test_plain_html_like_text_remains_literal_text(self) -> None:
        document = normalize_editor_document(
            plain_text_to_editor_document("<b>не HTML</b>")
        )
        self.assertEqual(editor_document_to_text(document), "<b>не HTML</b>")


class ControlledEditorPersistenceTests(OperationalLogTestCase):
    def test_model_save_backfills_legacy_plain_text_document(self) -> None:
        entry = self.shift.draft_entries.filter(is_removed=False).first()
        entry.editor_payload = {}
        entry.content = "Обычный\nтекст"
        entry.save()
        entry.refresh_from_db()
        self.assertEqual(entry.editor_schema_version, EDITOR_SCHEMA_VERSION)
        self.assertEqual(
            editor_document_to_text(entry.editor_payload),
            "Обычный\nтекст",
        )

    def test_service_persists_document_and_v2_revision_snapshot(self) -> None:
        entry = self.shift.draft_entries.filter(is_removed=False).first()
        document = {
            "schema_version": EDITOR_SCHEMA_VERSION,
            "blocks": [
                {
                    "type": "paragraph",
                    "segments": [
                        {"text": "Команда", "marks": ["bold"]},
                        {"text": " принята", "marks": ["underline"]},
                    ],
                }
            ],
        }
        saved = update_draft_entry(
            entry=entry,
            actor=self.actor,
            expected_version=entry.version,
            event_at=entry.event_at,
            content="клиентская проекция не является источником",
            editor_payload=document,
        )
        self.assertEqual(saved.content, "Команда принята")
        self.assertEqual(
            saved.editor_payload,
            normalize_editor_document(document),
        )
        preserved_version = saved.version
        preserved = update_draft_entry(
            entry=saved,
            actor=self.actor,
            expected_version=preserved_version,
            event_at=saved.event_at,
            content=saved.content,
            editor_payload=None,
        )
        self.assertEqual(preserved.version, preserved_version)
        self.assertEqual(preserved.editor_payload, saved.editor_payload)
        revision = saved.revisions.order_by("-revision_number").first()
        self.assertEqual(revision.action, DraftRevisionAction.UPDATED)
        self.assertEqual(
            revision.snapshot["schema_version"],
            "operational-draft-entry.v2",
        )
        self.assertEqual(
            revision.snapshot["draft"]["editor_payload"],
            saved.editor_payload,
        )
