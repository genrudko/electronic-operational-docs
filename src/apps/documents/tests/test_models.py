from __future__ import annotations

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.documents.models import AuditEvent, Document, DocumentLink, DocumentType, DocumentVersion
from apps.documents.services import (
    create_document_draft,
    create_document_link,
    register_document,
    update_document_draft,
)

from .factories import document_context


class DocumentCoreModelTests(TestCase):
    def setUp(self) -> None:
        self.employee, self.user, self.document_type = document_context(code="DOC")

    def _draft(self, title: str = "Черновик", body: str = "Содержимое") -> Document:
        return create_document_draft(
            document_type=self.document_type,
            actor=self.employee,
            title=title,
            content={"subject": "Тема", "body": body},
        )

    def test_document_type_normalizes_code_and_prefix(self):
        item = DocumentType.objects.create(
            organization=self.employee.organization,
            code="  SPECIAL  ",
            name="Специальный",
            number_prefix=" sp ",
            number_width=5,
        )
        self.assertEqual(item.code, "special")
        self.assertEqual(item.number_prefix, "SP")

    def test_document_rejects_type_from_other_organization(self):
        other_employee, _, other_type = document_context(code="OTHER")
        with self.assertRaises(ValidationError):
            Document.objects.create(
                organization=self.employee.organization,
                document_type=other_type,
                title="Чужой тип",
                created_by=self.employee,
            )
        self.assertNotEqual(other_employee.organization, self.employee.organization)

    def test_create_draft_creates_version_and_audit_event(self):
        document = self._draft()
        self.assertEqual(document.status, Document.Status.DRAFT)
        self.assertIsNotNone(document.current_version)
        self.assertEqual(document.current_version.version_number, 1)
        self.assertEqual(document.current_version.status, DocumentVersion.Status.DRAFT)
        self.assertEqual(document.current_version.content["body"], "Содержимое")
        self.assertTrue(
            AuditEvent.objects.filter(
                document=document,
                event_type=AuditEvent.EventType.DOCUMENT_CREATED,
            ).exists()
        )

    def test_update_draft_updates_current_version_and_audits(self):
        document = self._draft()
        updated = update_document_draft(
            document=document,
            actor=self.employee,
            title="Новый заголовок",
            content={"subject": "Новая тема", "body": "Новый текст"},
        )
        updated.refresh_from_db()
        updated.current_version.refresh_from_db()
        self.assertEqual(updated.title, "Новый заголовок")
        self.assertEqual(updated.current_version.content["body"], "Новый текст")
        self.assertTrue(
            AuditEvent.objects.filter(
                document=updated,
                event_type=AuditEvent.EventType.DRAFT_UPDATED,
            ).exists()
        )

    def test_registration_fixes_document_and_version(self):
        document = self._draft()
        result = register_document(document=document, actor=self.employee)
        result.document.refresh_from_db()
        result.version.refresh_from_db()

        self.assertEqual(result.document.status, Document.Status.REGISTERED)
        self.assertEqual(result.version.status, DocumentVersion.Status.REGISTERED)
        self.assertTrue(result.registration_number.startswith("DOC-"))
        self.assertEqual(result.document.registration_number, result.registration_number)
        self.assertEqual(result.document.registered_by, self.employee)
        self.assertEqual(result.version.registered_by, self.employee)
        self.assertTrue(
            AuditEvent.objects.filter(
                document=result.document,
                event_type=AuditEvent.EventType.DOCUMENT_REGISTERED,
            ).exists()
        )

    def test_server_counter_allocates_unique_sequential_numbers(self):
        first = register_document(document=self._draft("Первый"), actor=self.employee).document
        second = register_document(document=self._draft("Второй"), actor=self.employee).document
        self.assertEqual(first.sequence_number, 1)
        self.assertEqual(second.sequence_number, 2)
        self.assertNotEqual(first.registration_number, second.registration_number)

    def test_registration_requires_non_empty_body(self):
        document = self._draft(body="")
        with self.assertRaises(ValidationError):
            register_document(document=document, actor=self.employee)
        document.refresh_from_db()
        self.assertEqual(document.status, Document.Status.DRAFT)

    def test_registered_document_cannot_be_saved(self):
        document = register_document(document=self._draft(), actor=self.employee).document
        document.title = "Попытка изменения"
        with self.assertRaises(ValidationError):
            document.save()

    def test_registered_version_cannot_be_saved(self):
        result = register_document(document=self._draft(), actor=self.employee)
        result.version.content = {"body": "Подмена"}
        with self.assertRaises(ValidationError):
            result.version.save()

    def test_bulk_update_is_blocked(self):
        document = self._draft()
        with self.assertRaises(ValidationError):
            Document.objects.filter(pk=document.pk).update(title="Массовое изменение")
        with self.assertRaises(ValidationError):
            DocumentVersion.objects.filter(document=document).update(title="Подмена")

    def test_physical_delete_is_blocked_for_instance_and_queryset(self):
        document = self._draft()
        with self.assertRaises(ValidationError):
            document.delete()
        with self.assertRaises(ValidationError):
            Document.objects.filter(pk=document.pk).delete()
        with self.assertRaises(ValidationError):
            document.current_version.delete()

    def test_audit_event_is_append_only(self):
        document = self._draft()
        event = document.audit_events.first()
        event.payload = {"changed": True}
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            AuditEvent.objects.filter(pk=event.pk).delete()

    def test_document_link_rejects_self_reference(self):
        document = register_document(document=self._draft(), actor=self.employee).document
        with self.assertRaises(ValidationError):
            create_document_link(
                source_document=document,
                target_document=document,
                link_type=DocumentLink.LinkType.RELATED,
                actor=self.employee,
            )

    def test_document_link_rejects_other_organization(self):
        source = register_document(document=self._draft(), actor=self.employee).document
        other_employee, _, other_type = document_context(code="OTHER")
        target = create_document_draft(
            document_type=other_type,
            actor=other_employee,
            title="Другой документ",
            content={"body": "Содержимое"},
        )
        target = register_document(document=target, actor=other_employee).document
        with self.assertRaises(ValidationError):
            create_document_link(
                source_document=source,
                target_document=target,
                link_type=DocumentLink.LinkType.RELATED,
                actor=self.employee,
            )

    def test_link_creation_is_append_only_and_audited(self):
        source = register_document(document=self._draft("Источник"), actor=self.employee).document
        target = register_document(document=self._draft("Цель"), actor=self.employee).document
        link = create_document_link(
            source_document=source,
            target_document=target,
            link_type=DocumentLink.LinkType.BASED_ON,
            actor=self.employee,
        )
        self.assertTrue(
            AuditEvent.objects.filter(
                document=source,
                event_type=AuditEvent.EventType.DOCUMENT_LINK_CREATED,
                entity_id=str(link.pk),
            ).exists()
        )
        link.link_type = DocumentLink.LinkType.RELATED
        with self.assertRaises(ValidationError):
            link.save()
        with self.assertRaises(ValidationError):
            link.delete()
