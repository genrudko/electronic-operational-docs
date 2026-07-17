from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection

from apps.documents.models import Document
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Workplace,
)

from ..models import EntryForm, OperationalJournalSequence, OperationalLogAuditEvent
from ..services import entry_snapshot, register_entry, verify_entry_integrity
from .base import OperationalLogTestCase


class OperationalLogServiceTests(OperationalLogTestCase):
    def test_registration_assigns_next_number_and_server_time(self) -> None:
        before = self.event_time(0)
        entry = register_entry(
            journal=self.journal,
            actor=self.actor,
            event_at=self.event_time(3),
            content="Новая свободная запись",
        )
        self.assertEqual(entry.sequence_number, 6)
        self.assertGreaterEqual(entry.registered_at, before)
        self.assertEqual(entry.entry_form, EntryForm.FREE_TEXT)

    def test_numbers_are_strictly_sequential(self) -> None:
        first = register_entry(
            journal=self.journal,
            actor=self.actor,
            event_at=self.event_time(5),
            content="Первая дополнительная запись",
        )
        second = register_entry(
            journal=self.journal,
            actor=self.actor,
            event_at=self.event_time(4),
            content="Вторая дополнительная запись",
        )
        self.assertEqual(second.sequence_number, first.sequence_number + 1)
        self.assertEqual(
            OperationalJournalSequence.objects.get(journal=self.journal).last_value,
            second.sequence_number,
        )

    def test_typed_registration_preserves_payload(self) -> None:
        entry = register_entry(
            journal=self.journal,
            actor=self.actor,
            event_at=self.event_time(),
            entry_form=EntryForm.TYPED,
            type_code="CHECK",
            type_title="Проверка",
            content="Типизированная проверка",
            typed_payload={"result": "ok"},
        )
        self.assertEqual(entry.type_code, "check")
        self.assertEqual(entry.typed_payload, {"result": "ok"})

    def test_equipment_link_keeps_dispatcher_name_snapshot(self) -> None:
        entry = register_entry(
            journal=self.journal,
            actor=self.actor,
            event_at=self.event_time(),
            content="Запись со связанным оборудованием",
            equipment=(self.equipment,),
        )
        link = entry.equipment_links.get()
        self.assertEqual(link.equipment_code_snapshot, "DEMO-KTP-01")
        self.assertTrue(link.dispatcher_name_snapshot)
        self.assertTrue(link.site_name_snapshot)

    def test_document_link_keeps_registered_identity(self) -> None:
        entry = register_entry(
            journal=self.journal,
            actor=self.actor,
            event_at=self.event_time(),
            content="Запись со связанным документом",
            documents=(self.document,),
        )
        link = entry.document_links.get()
        self.assertEqual(
            link.registration_number_snapshot, self.document.registration_number
        )
        self.assertEqual(link.title_snapshot, self.document.title)

    def test_cross_organization_actor_is_rejected(self) -> None:
        organization = Organization.objects.create(
            code="OTHER-ACTOR", name="Другая организация"
        )
        division = Division.objects.create(
            organization=organization, code="DIV", name="Подразделение"
        )
        position = Position.objects.create(
            organization=organization, code="POS", name="Должность"
        )
        workplace = Workplace.objects.create(
            organization=organization, code="WP", name="Рабочее место"
        )
        actor = Employee.objects.create(
            organization=organization,
            division=division,
            position=position,
            workplace=workplace,
            personnel_number="OTHER-1",
            last_name="Тестов",
            first_name="Иван",
        )
        with self.assertRaises(PermissionDenied):
            register_entry(
                journal=self.journal,
                actor=actor,
                event_at=self.event_time(),
                content="Недопустимая запись",
            )

    def test_draft_document_link_is_rejected_without_consuming_number(self) -> None:
        draft = Document.objects.filter(
            organization=self.organization,
            status=Document.Status.DRAFT,
        ).first()
        previous = OperationalJournalSequence.objects.get(
            journal=self.journal
        ).last_value
        with self.assertRaises(ValidationError):
            register_entry(
                journal=self.journal,
                actor=self.actor,
                event_at=self.event_time(),
                content="Недопустимая ссылка",
                documents=(draft,),
            )
        self.assertEqual(
            OperationalJournalSequence.objects.get(journal=self.journal).last_value,
            previous,
        )

    def test_entry_integrity_matches_audit_snapshot(self) -> None:
        entry = self.journal.entries.get(sequence_number=2)
        self.assertTrue(verify_entry_integrity(entry))
        audit = OperationalLogAuditEvent.objects.get(entry=entry)
        self.assertEqual(audit.snapshot, entry_snapshot(entry))
        self.assertEqual(audit.digest, entry.digest)

    def test_direct_database_tampering_is_detected(self) -> None:
        entry = self.journal.entries.get(sequence_number=1)
        with connection.cursor() as cursor:
            cursor.execute(
                "UPDATE operational_log_operationallogentry SET content = %s WHERE id = %s",
                ["Подмена через SQL", entry.pk],
            )
        entry.refresh_from_db()
        with self.assertRaises(ValidationError):
            verify_entry_integrity(entry)
