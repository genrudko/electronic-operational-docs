from django.core.exceptions import ValidationError

from apps.organizations.models import Organization, Workplace

from ..models import (
    EntryForm,
    OperationalJournal,
    OperationalLogAuditEvent,
    OperationalLogDocumentLink,
    OperationalLogEntry,
    OperationalLogEquipmentLink,
)
from ..services import register_entry
from .base import OperationalLogTestCase


class OperationalLogModelTests(OperationalLogTestCase):
    def test_journal_normalizes_code(self) -> None:
        journal = OperationalJournal(
            organization=self.organization,
            workplace=self.workplace,
            code="  SECOND-LOG  ",
            title="Второй журнал",
        )
        journal.save()
        self.assertEqual(journal.code, "second-log")

    def test_journal_rejects_workplace_from_other_organization(self) -> None:
        other = Organization.objects.create(code="OTHER", name="Другая организация")
        workplace = Workplace.objects.create(
            organization=other, code="OTHER", name="Другое место"
        )
        journal = OperationalJournal(
            organization=self.organization,
            workplace=workplace,
            code="invalid",
            title="Недопустимый журнал",
        )
        with self.assertRaises(ValidationError):
            journal.full_clean()

    def test_journal_identity_is_frozen_after_first_entry(self) -> None:
        journal = OperationalJournal.objects.get(pk=self.journal.pk)
        journal.title = "Подменённое название"
        with self.assertRaises(ValidationError):
            journal.save()

    def test_registered_entry_cannot_be_changed_or_deleted(self) -> None:
        entry = self.journal.entries.order_by("sequence_number").first()
        entry.content = "Подмена"
        with self.assertRaises(ValidationError):
            entry.save()
        with self.assertRaises(ValidationError):
            entry.delete()

    def test_queryset_update_and_delete_are_blocked(self) -> None:
        with self.assertRaises(ValidationError):
            OperationalLogEntry.objects.filter(journal=self.journal).update(
                content="Подмена"
            )
        with self.assertRaises(ValidationError):
            OperationalLogEntry.objects.filter(journal=self.journal).delete()

    def test_free_and_typed_contracts_are_enforced(self) -> None:
        with self.assertRaises(ValidationError):
            register_entry(
                journal=self.journal,
                actor=self.actor,
                event_at=self.event_time(),
                entry_form=EntryForm.FREE_TEXT,
                type_code="forbidden",
                type_title="Лишний тип",
                content="Свободная запись",
            )
        with self.assertRaises(ValidationError):
            register_entry(
                journal=self.journal,
                actor=self.actor,
                event_at=self.event_time(),
                entry_form=EntryForm.TYPED,
                content="Нет типа",
            )

    def test_links_and_audit_event_are_immutable(self) -> None:
        entry = self.journal.entries.filter(equipment_links__isnull=False).first()
        equipment_link = OperationalLogEquipmentLink.objects.filter(entry=entry).first()
        document_link = OperationalLogDocumentLink.objects.filter(
            entry__journal=self.journal
        ).first()
        audit = OperationalLogAuditEvent.objects.filter(
            entry__journal=self.journal
        ).first()
        for item in (equipment_link, document_link, audit):
            with self.assertRaises(ValidationError):
                item.delete()
