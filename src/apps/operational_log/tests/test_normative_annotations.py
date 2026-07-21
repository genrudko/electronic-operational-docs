from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from ..editor import (
    EDITOR_SCHEMA_VERSION,
    editor_document_to_text,
    normalize_editor_document,
)
from ..models import DraftRevisionAction
from ..services import update_draft_entry
from .base import OperationalLogTestCase

SOURCE_ID = "normative_source_0001"
CLOSE_ID = "normative_close_0001"


def pz_install_document() -> dict[str, object]:
    return {
        "schema_version": EDITOR_SCHEMA_VERSION,
        "entry_kind": "normal",
        "annotations": [
            {
                "id": SOURCE_ID,
                "kind": "pz_install",
                "label": "Установлено ПЗ №109 на выводах Г-24",
                "pz_number": "№109",
            }
        ],
        "blocks": [
            {
                "type": "paragraph",
                "segments": [
                    {
                        "text": "Установлено ПЗ №109 на выводах Г-24",
                        "marks": ["bold", "text_red"],
                        "annotations": [SOURCE_ID],
                    }
                ],
            }
        ],
    }


class NormativeAnnotationDocumentTests(SimpleTestCase):
    def test_v3_is_upgraded_to_v4_without_text_loss(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": "operational-draft-editor.v3",
                "entry_kind": "normal",
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {"text": "Включён ЗН Т-1", "marks": []}
                        ],
                    }
                ],
            }
        )
        self.assertEqual(document["schema_version"], EDITOR_SCHEMA_VERSION)
        self.assertEqual(document["annotations"], [])
        self.assertEqual(editor_document_to_text(document), "Включён ЗН Т-1")

    def test_pz_install_keeps_number_and_safe_marks(self) -> None:
        document = normalize_editor_document(pz_install_document())
        annotation = document["annotations"][0]
        self.assertEqual(annotation["kind"], "pz_install")
        self.assertEqual(annotation["pz_number"], "109")
        segment = document["blocks"][0]["segments"][0]
        self.assertEqual(segment["annotations"], [SOURCE_ID])
        self.assertEqual(segment["marks"], ["bold", "text_red"])
        self.assertEqual(
            editor_document_to_text(document),
            "Установлено ПЗ №109 на выводах Г-24",
        )

    def test_pz_removal_requires_link_to_original_installation(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_editor_document(
                {
                    "schema_version": EDITOR_SCHEMA_VERSION,
                    "entry_kind": "normal",
                    "annotations": [
                        {
                            "id": CLOSE_ID,
                            "kind": "pz_remove",
                            "label": "Снято ПЗ №109",
                            "pz_number": "109",
                        }
                    ],
                    "blocks": [
                        {
                            "type": "paragraph",
                            "segments": [
                                {
                                    "text": "Снято ПЗ №109",
                                    "marks": [],
                                    "annotations": [CLOSE_ID],
                                }
                            ],
                        }
                    ],
                }
            )

    def test_pz_removal_preserves_source_identity(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": EDITOR_SCHEMA_VERSION,
                "entry_kind": "normal",
                "annotations": [
                    {
                        "id": CLOSE_ID,
                        "kind": "pz_remove",
                        "label": "Снято ПЗ №109",
                        "pz_number": "109",
                        "source_entry": (
                            "draft:00000000-0000-0000-0000-000000000001"
                        ),
                        "source_annotation": SOURCE_ID,
                    }
                ],
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {
                                "text": "Снято ПЗ №109",
                                "marks": ["text_blue"],
                                "annotations": [CLOSE_ID],
                            }
                        ],
                    }
                ],
            }
        )
        annotation = document["annotations"][0]
        self.assertEqual(annotation["source_annotation"], SOURCE_ID)
        self.assertEqual(annotation["pz_number"], "109")

    def test_emergency_annotation_may_apply_to_the_whole_row(self) -> None:
        document = normalize_editor_document(
            {
                "schema_version": EDITOR_SCHEMA_VERSION,
                "entry_kind": "warning",
                "annotations": [
                    {
                        "id": "emergency_event_001",
                        "kind": "emergency",
                        "label": "Аварийное событие",
                    }
                ],
                "blocks": [
                    {
                        "type": "paragraph",
                        "segments": [
                            {"text": "Срабатывание защиты", "marks": []}
                        ],
                    }
                ],
            }
        )
        self.assertEqual(document["annotations"][0]["kind"], "emergency")
        self.assertEqual(
            editor_document_to_text(document),
            "Предупреждение: Срабатывание защиты",
        )

    def test_unattached_text_annotation_is_rejected(self) -> None:
        payload = pz_install_document()
        payload["blocks"] = [
            {
                "type": "paragraph",
                "segments": [{"text": "Текст", "marks": []}],
            }
        ]
        with self.assertRaises(ValidationError):
            normalize_editor_document(payload)


class NormativeAnnotationPersistenceTests(OperationalLogTestCase):
    def test_service_persists_annotation_and_revision_snapshot(self) -> None:
        entry = self.shift.draft_entries.filter(is_removed=False).first()
        saved = update_draft_entry(
            entry=entry,
            actor=self.actor,
            expected_version=entry.version,
            event_at=entry.event_at,
            content="Клиентская проекция",
            editor_payload=pz_install_document(),
        )
        self.assertEqual(saved.editor_schema_version, EDITOR_SCHEMA_VERSION)
        self.assertEqual(saved.editor_payload["annotations"][0]["pz_number"], "109")
        revision = saved.revisions.order_by("-revision_number").first()
        self.assertEqual(revision.action, DraftRevisionAction.UPDATED)
        self.assertEqual(
            revision.snapshot["draft"]["editor_payload"],
            saved.editor_payload,
        )
