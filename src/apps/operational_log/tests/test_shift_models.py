from django.core.exceptions import ValidationError

from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Workplace,
)

from ..models import (
    OperationalDraftEntry,
    OperationalDraftRevision,
    OperationalShift,
    ShiftStatus,
)
from ..services import create_draft_entry
from .base import OperationalLogTestCase


class OperationalShiftModelTests(OperationalLogTestCase):
    def test_shift_rejects_invalid_planned_period(self) -> None:
        shift = OperationalShift(
            journal=self.journal,
            status=ShiftStatus.OPEN,
            planned_start_at=self.event_time(1),
            planned_end_at=self.event_time(2),
            opened_by=self.actor,
            opened_by_full_name_snapshot=self.actor.full_name,
            opened_by_position_snapshot=self.actor.position.name,
        )
        with self.assertRaises(ValidationError):
            shift.full_clean()

    def test_shift_member_snapshot_is_immutable(self) -> None:
        member = self.shift.members.get(employee=self.actor)
        member.employee_position_snapshot = "Подменённая должность"
        with self.assertRaises(ValidationError):
            member.save()
        with self.assertRaises(ValidationError):
            member.delete()

    def test_draft_entry_starts_with_version_and_cannot_be_deleted(
        self,
    ) -> None:
        entry = create_draft_entry(
            shift=self.shift,
            actor=self.actor,
            event_at=self.event_time(),
            content="Проверка модели черновика",
        )
        self.assertEqual(entry.version, 1)
        self.assertFalse(entry.is_removed)
        with self.assertRaises(ValidationError):
            entry.delete()

    def test_draft_revision_is_immutable(self) -> None:
        revision = OperationalDraftRevision.objects.filter(
            entry__shift=self.shift
        ).first()
        revision.digest = "0" * 64
        with self.assertRaises(ValidationError):
            revision.save()
        with self.assertRaises(ValidationError):
            revision.delete()

    def test_draft_rejects_employee_from_other_organization(self) -> None:
        organization = Organization.objects.create(
            code="SHIFT-OTHER",
            name="Другая организация",
        )
        division = Division.objects.create(
            organization=organization,
            code="DIV",
            name="Подразделение",
        )
        position = Position.objects.create(
            organization=organization,
            code="POS",
            name="Должность",
        )
        workplace = Workplace.objects.create(
            organization=organization,
            code="WP",
            name="Рабочее место",
        )
        other_employee = Employee.objects.create(
            organization=organization,
            division=division,
            position=position,
            workplace=workplace,
            personnel_number="SHIFT-OTHER-1",
            last_name="Тестов",
            first_name="Иван",
        )
        entry = OperationalDraftEntry(
            shift=self.shift,
            position=999,
            event_at=self.event_time(),
            content="Недопустимый автор",
            created_by=other_employee,
            updated_by=other_employee,
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_closed_shift_rejects_new_draft(self) -> None:
        OperationalShift.objects.filter(pk=self.shift.pk).update(
            status=ShiftStatus.CLOSED,
            closed_at=self.event_time(0),
        )
        self.shift.refresh_from_db()
        entry = OperationalDraftEntry(
            shift=self.shift,
            position=999,
            event_at=self.event_time(),
            content="Запись после закрытия",
            created_by=self.actor,
            updated_by=self.actor,
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()
