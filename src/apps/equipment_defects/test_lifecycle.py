from __future__ import annotations

from datetime import timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from apps.operational_documents.services import canonical_json, sha256_text
from apps.operational_log.models import OperationalJournal
from apps.operational_log.services import register_entry

from .constants import (
    DEADLINE_EXTENSION_TEXT,
    ROLE_OPERATIONAL_ACKNOWLEDGER,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_RESOLVED,
)
from .models import DefectActionCode, EquipmentDefectOperationalLogLink
from .services import (
    acknowledge_resolution,
    close_defect,
    confirm_deadline,
    confirm_resolution,
    extend_deadline,
    register_defect,
)
from .test_support import EquipmentDefectSourceBoundBase


class EquipmentDefectLifecycleTests(EquipmentDefectSourceBoundBase, TestCase):
    def test_lifecycle_extension_acknowledgement_and_terminal_lock(self) -> None:
        record = self.register()
        with self.assertRaises(ValidationError):
            confirm_resolution(
                record=record,
                actor=self.supervisor,
                responsible=self.supervisor,
                resolved_at=timezone.now() - timedelta(minutes=30),
                work_summary="Попытка пропустить назначение срока.",
            )
        with self.assertRaises(ValidationError):
            close_defect(record=record, actor=self.supervisor)

        first_deadline = timezone.now() + timedelta(days=2)
        record = confirm_deadline(
            record=record,
            actor=self.supervisor,
            responsible=self.supervisor,
            deadline=first_deadline,
        )
        self.assertEqual(record.status_code, STATUS_IN_PROGRESS)

        second_deadline = first_deadline + timedelta(days=3)
        record = extend_deadline(
            record=record,
            actor=self.supervisor,
            new_deadline=second_deadline,
            reason="Требуется дополнительное безопасное окно работ.",
        )
        extension = record.equipment_defect_actions.get(
            action_code=DefectActionCode.DEADLINE_EXTENDED
        )
        self.assertEqual(extension.previous_deadline, first_deadline)
        self.assertEqual(extension.new_deadline, second_deadline)
        self.assertEqual(
            sha256_text(canonical_json(extension.canonical_snapshot)),
            extension.sha256,
        )
        current_revision = record.revisions.get(revision_number=record.version)
        self.assertIn(DEADLINE_EXTENSION_TEXT, current_revision.comment)

        record = confirm_resolution(
            record=record,
            actor=self.supervisor,
            responsible=self.supervisor,
            resolved_at=timezone.now() - timedelta(minutes=15),
            work_summary="Крепление восстановлено, результат проверен осмотром.",
        )
        self.assertEqual(record.status_code, STATUS_RESOLVED)
        with self.assertRaises(ValidationError):
            close_defect(record=record, actor=self.supervisor)

        record = acknowledge_resolution(record=record, actor=self.operator)
        self.assertTrue(
            record.participants.filter(
                role_code=ROLE_OPERATIONAL_ACKNOWLEDGER,
                employee=self.operator,
            ).exists()
        )
        record = close_defect(record=record, actor=self.supervisor)
        self.assertEqual(record.status_code, STATUS_CLOSED)
        self.assertTrue(record.status_is_terminal)
        self.assertIsNotNone(record.closed_at)

        with self.assertRaises(ValidationError):
            extend_deadline(
                record=record,
                actor=self.supervisor,
                new_deadline=second_deadline + timedelta(days=1),
                reason="Терминальную запись менять нельзя.",
            )
        with self.assertRaises(ValidationError):
            record.delete()
        with self.assertRaises(ValidationError):
            record.equipment_defect_context.delete()
        with self.assertRaises(ValidationError):
            extension.delete()

    def test_operational_log_link_keeps_snapshot_and_digest(self) -> None:
        record = self.register(link_to_log=True)
        link = EquipmentDefectOperationalLogLink.objects.get(record=record)

        self.assertEqual(link.operational_log_entry, self.operational_entry)
        self.assertEqual(link.entry_sequence_snapshot, self.operational_entry.sequence_number)
        self.assertEqual(link.entry_digest_snapshot, self.operational_entry.digest)
        self.assertIn("выявлено замечание", link.entry_content_snapshot)
        with self.assertRaises(ValidationError):
            link.delete()

    def test_cross_organization_operational_log_link_is_rejected(self) -> None:
        other_journal = OperationalJournal.objects.create(
            organization=self.other_fixture["organization"],
            workplace=self.other_fixture["workplace"],
            code="operational-other",
            title="Оперативный журнал другой организации",
        )
        other_entry = register_entry(
            journal=other_journal,
            actor=self.other_employee,
            event_at=timezone.now() - timedelta(hours=1),
            content="Запись другой организации.",
            equipment=[self.other_fixture["equipment"]],
        )
        with self.assertRaises(ValidationError):
            register_defect(
                actor=self.operator,
                workplace=self.fixture["workplace"],
                equipment=self.fixture["equipment"],
                discovered_by=self.discoverer,
                detected_at=timezone.now() - timedelta(minutes=45),
                defect_description="Попытка межорганизационной связи.",
                operational_log_entry=other_entry,
            )

