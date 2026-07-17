from datetime import date

from django.core.exceptions import ValidationError

from apps.workplace_docs.models import (
    RevisionStatus,
    SourceKind,
    StorageForm,
    WorkplaceDocumentAuditEvent,
    WorkplaceDocumentEntry,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)
from apps.workplace_docs.services import approve_revision

from .base import WorkplaceDocumentTestBase


class WorkplaceDocumentModelTests(WorkplaceDocumentTestBase):
    def test_list_rejects_workplace_from_other_organization(self) -> None:
        item = WorkplaceDocumentList(
            organization=self.organization,
            workplace=self.foreign_workplace,
            code="invalid",
            title="Некорректный перечень",
        )
        with self.assertRaises(ValidationError):
            item.full_clean()

    def test_revision_rejects_invalid_effective_window(self) -> None:
        document_list = self.create_document_list()
        revision = WorkplaceDocumentRevision(
            document_list=document_list,
            revision_number=1,
            effective_from=date(2026, 2, 1),
            effective_until=date(2026, 1, 31),
        )
        with self.assertRaises(ValidationError):
            revision.save()

    def test_entry_requires_normative_or_text_basis(self) -> None:
        revision = self.create_revision(with_entry=False)
        entry = WorkplaceDocumentEntry(
            revision=revision,
            code="EMPTY-BASIS",
            title="Позиция без основания",
            source_kind=SourceKind.LOCAL,
            storage_form=StorageForm.PAPER,
        )
        with self.assertRaises(ValidationError):
            entry.save()

    def test_local_normative_from_other_organization_is_rejected(self) -> None:
        revision = self.create_revision(with_entry=False)
        entry = WorkplaceDocumentEntry(
            revision=revision,
            code="FOREIGN",
            title="Чужой локальный документ",
            source_kind=SourceKind.LOCAL,
            storage_form=StorageForm.ELECTRONIC,
            normative_document=self.foreign_local_normative,
        )
        with self.assertRaises(ValidationError):
            entry.save()

    def test_approved_revision_is_immutable(self) -> None:
        revision = approve_revision(revision=self.create_revision(), actor=self.employee)
        revision.change_summary = "Попытка изменения"
        with self.assertRaises(ValidationError):
            revision.save()

    def test_entry_of_approved_revision_is_immutable(self) -> None:
        revision = approve_revision(revision=self.create_revision(), actor=self.employee)
        entry = revision.entries.get()
        entry.title = "Изменённое наименование"
        with self.assertRaises(ValidationError):
            entry.save()

    def test_protected_querysets_block_update_and_delete(self) -> None:
        self.create_revision()
        with self.assertRaises(ValidationError):
            WorkplaceDocumentRevision.objects.update(change_summary="bulk")
        with self.assertRaises(ValidationError):
            WorkplaceDocumentList.objects.all().delete()

    def test_audit_event_is_append_only(self) -> None:
        revision = approve_revision(revision=self.create_revision(), actor=self.employee)
        event = WorkplaceDocumentAuditEvent.objects.get(revision=revision)
        self.assertEqual(event.event_type, WorkplaceDocumentAuditEvent.EventType.REVISION_APPROVED)
        self.assertEqual(revision.status, RevisionStatus.APPROVED)
        event.snapshot = {"changed": True}
        with self.assertRaises(ValidationError):
            event.save()
        with self.assertRaises(ValidationError):
            event.delete()
