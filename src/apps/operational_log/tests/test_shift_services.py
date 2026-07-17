from django.core.exceptions import ValidationError

from ..models import (
    DraftRevisionAction,
    OperationalJournalSequence,
)
from ..services import (
    DraftConflictError,
    active_shift_for_journal,
    create_draft_entry,
    move_draft_entry,
    open_shift,
    remove_draft_entry,
    restore_draft_entry,
    update_draft_entry,
)
from .base import OperationalLogTestCase


class OperationalShiftServiceTests(OperationalLogTestCase):
    def test_open_shift_rejects_second_active_shift(self) -> None:
        start_at, end_at = self.planned_period()
        with self.assertRaises(ValidationError):
            open_shift(
                journal=self.journal,
                actor=self.actor,
                planned_start_at=start_at,
                planned_end_at=end_at,
            )

    def test_create_draft_appends_initial_revision(self) -> None:
        entry = create_draft_entry(
            shift=self.shift,
            actor=self.actor,
            event_at=self.event_time(),
            content="Новая черновая запись",
        )
        revision = entry.revisions.get()
        self.assertEqual(
            revision.action,
            DraftRevisionAction.CREATED,
        )
        self.assertEqual(revision.revision_number, 1)
        self.assertEqual(
            revision.snapshot["draft"]["content"],
            "Новая черновая запись",
        )

    def test_update_draft_increments_version_and_revision(self) -> None:
        entry = create_draft_entry(
            shift=self.shift,
            actor=self.actor,
            event_at=self.event_time(5),
            content="Исходный текст",
        )
        updated = update_draft_entry(
            entry=entry,
            actor=self.actor,
            expected_version=1,
            event_at=self.event_time(4),
            content="Исправленный текст",
        )
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.content, "Исправленный текст")
        self.assertEqual(updated.revisions.count(), 2)
        self.assertEqual(
            updated.revisions.order_by("revision_number").last().action,
            DraftRevisionAction.UPDATED,
        )

    def test_stale_version_does_not_overwrite_draft(self) -> None:
        entry = create_draft_entry(
            shift=self.shift,
            actor=self.actor,
            event_at=self.event_time(5),
            content="Первая редакция",
        )
        update_draft_entry(
            entry=entry,
            actor=self.actor,
            expected_version=1,
            event_at=self.event_time(4),
            content="Вторая редакция",
        )
        entry.refresh_from_db()
        with self.assertRaises(DraftConflictError):
            update_draft_entry(
                entry=entry,
                actor=self.actor,
                expected_version=1,
                event_at=self.event_time(3),
                content="Устаревшая перезапись",
            )
        entry.refresh_from_db()
        self.assertEqual(entry.content, "Вторая редакция")
        self.assertEqual(entry.version, 2)

    def test_move_draft_swaps_positions_and_records_revisions(self) -> None:
        entries = list(
            self.shift.draft_entries.filter(
                is_removed=False
            ).order_by("position", "pk")
        )
        first, second = entries[:2]
        first_position = first.position
        second_position = second.position
        moved = move_draft_entry(
            entry=second,
            actor=self.actor,
            direction="up",
        )
        first.refresh_from_db()
        moved.refresh_from_db()
        self.assertEqual(moved.position, first_position)
        self.assertEqual(first.position, second_position)
        self.assertEqual(
            moved.revisions.order_by("revision_number").last().action,
            DraftRevisionAction.REORDERED,
        )

    def test_remove_and_restore_preserve_history(self) -> None:
        entry = self.shift.draft_entries.filter(
            is_removed=False
        ).first()
        removed = remove_draft_entry(
            entry=entry,
            actor=self.actor,
        )
        self.assertTrue(removed.is_removed)
        self.assertEqual(
            removed.revisions.order_by("revision_number").last().action,
            DraftRevisionAction.REMOVED,
        )
        restored = restore_draft_entry(
            entry=removed,
            actor=self.actor,
        )
        self.assertFalse(restored.is_removed)
        self.assertEqual(
            restored.revisions.order_by("revision_number").last().action,
            DraftRevisionAction.RESTORED,
        )

    def test_active_shift_lookup_returns_current_shift(self) -> None:
        shift = active_shift_for_journal(self.journal)
        self.assertIsNotNone(shift)
        self.assertEqual(shift.pk, self.shift.pk)

    def test_draft_does_not_consume_official_sequence_number(self) -> None:
        before = OperationalJournalSequence.objects.get(
            journal=self.journal
        ).last_value
        create_draft_entry(
            shift=self.shift,
            actor=self.actor,
            event_at=self.event_time(),
            content="Черновик без официального номера",
        )
        after = OperationalJournalSequence.objects.get(
            journal=self.journal
        ).last_value
        self.assertEqual(before, after)
