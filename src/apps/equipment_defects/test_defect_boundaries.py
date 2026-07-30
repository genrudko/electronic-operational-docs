from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.operational_documents.services import create_record

from .constants import (
    FIELD_DEFECT_DESCRIPTION,
    FIELD_DETECTED_AT,
    FIELD_ELIMINATION_DEADLINE,
    FIELD_RESOLUTION_WORK_SUMMARY,
    FIELD_RESOLVED_AT,
    ROLE_DISCOVERED_BY,
)
from .models import EquipmentDefectContext, EquipmentDefectVolume
from .services import (
    acknowledge_resolution,
    close_defect,
    confirm_deadline,
    confirm_resolution,
    current_defect_volume,
    ensure_defect_document_type,
    open_new_defect_volume,
    register_defect,
)
from .services.helpers import stored_datetime
from .tests import DefectFixtureMixin

MOSCOW_TIME_ZONE = ZoneInfo("Europe/Moscow")


class EquipmentDefectBoundaryTests(DefectFixtureMixin, TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.fixture = cls.create_organization_fixture("boundaries")
        cls.operator = cls.create_employee(
            fixture=cls.fixture,
            username="boundary.operator",
            personnel_number="BOUND-001",
            last_name="Операторов",
            position_key="operational_position",
        )
        cls.responsible = cls.create_employee(
            fixture=cls.fixture,
            username="boundary.responsible",
            personnel_number="BOUND-002",
            last_name="Ответственный",
            position_key="responsible_position",
        )
        cls.revision = ensure_defect_document_type(cls.operator)

    def register(self):
        detected_at = timezone.now() - timedelta(hours=3)
        record = register_defect(
            actor=self.operator,
            workplace=self.fixture["workplace"],
            equipment=self.fixture["equipment"],
            discovered_by=self.responsible,
            detected_at=detected_at,
            defect_description="Тестовый дефект для проверки предметных границ.",
        )
        return record, detected_at

    def close_registered_record(self):
        record, detected_at = self.register()
        record = confirm_deadline(
            record=record,
            actor=self.responsible,
            responsible=self.responsible,
            deadline=detected_at + timedelta(days=2),
        )
        resolved_at = detected_at + timedelta(hours=2)
        record = confirm_resolution(
            record=record,
            actor=self.responsible,
            responsible=self.responsible,
            resolved_at=resolved_at,
            work_summary="Восстановлено исправное состояние, выполнена проверка.",
        )
        record = acknowledge_resolution(record=record, actor=self.operator)
        record = close_defect(record=record, actor=self.responsible)
        return record, resolved_at

    def test_generic_create_edit_detail_and_transition_redirect_to_dedicated_ui(self) -> None:
        record, _detected_at = self.register()
        self.client.force_login(self.operator.user)

        create_response = self.client.get(
            reverse(
                "operational_documents:record_create",
                args=[self.revision.document_type.public_id],
            )
        )
        self.assertRedirects(
            create_response,
            reverse("equipment_defects:create"),
            fetch_redirect_response=False,
        )

        dedicated_detail = reverse("equipment_defects:detail", args=[record.public_id])
        for route_name in ("record_detail", "record_edit", "record_transition"):
            response = self.client.get(
                reverse(f"operational_documents:{route_name}", args=[record.public_id])
            )
            self.assertRedirects(
                response,
                dedicated_detail,
                fetch_redirect_response=False,
            )

    def test_source_bound_context_rejects_record_without_equipment(self) -> None:
        event_at = timezone.now() - timedelta(hours=1)
        record = create_record(
            revision=self.revision,
            actor=self.operator,
            title="Недопустимая запись без оборудования",
            summary="Эта запись не должна получить source-bound контекст.",
            event_at=event_at,
            workplace=self.fixture["workplace"],
            field_values={
                FIELD_DETECTED_AT: event_at,
                FIELD_DEFECT_DESCRIPTION: "Дефект без структурированной связи.",
                FIELD_ELIMINATION_DEADLINE: None,
                FIELD_RESOLVED_AT: None,
                FIELD_RESOLUTION_WORK_SUMMARY: "",
            },
            participant_map={ROLE_DISCOVERED_BY: [self.responsible]},
            equipment_assets=[],
        )
        volume = current_defect_volume(
            workplace=self.fixture["workplace"],
            actor=self.operator,
        )

        with self.assertRaisesMessage(
            ValidationError,
            "обязательную структурированную связь с оборудованием",
        ):
            EquipmentDefectContext.objects.create(record=record, volume=volume)

    def test_opening_new_volume_does_not_clone_or_move_records(self) -> None:
        record, resolved_at = self.close_registered_record()
        original_volume = record.equipment_defect_context.volume
        original_context_id = record.equipment_defect_context.pk

        new_volume = open_new_defect_volume(
            workplace=self.fixture["workplace"],
            actor=self.operator,
        )
        original_volume.refresh_from_db()
        record.refresh_from_db()

        self.assertNotEqual(new_volume.pk, original_volume.pk)
        self.assertEqual(new_volume.sequence_number, original_volume.sequence_number + 1)
        self.assertTrue(new_volume.accepts_new_records)
        self.assertFalse(original_volume.accepts_new_records)
        self.assertEqual(
            original_volume.closed_on,
            timezone.localdate(resolved_at, timezone=MOSCOW_TIME_ZONE),
        )
        self.assertEqual(record.equipment_defect_context.pk, original_context_id)
        self.assertEqual(record.equipment_defect_context.volume_id, original_volume.pk)
        self.assertEqual(original_volume.defect_contexts.count(), 1)
        self.assertEqual(new_volume.defect_contexts.count(), 0)
        self.assertEqual(
            EquipmentDefectVolume.objects.filter(
                organization=self.fixture["organization"],
                workplace=self.fixture["workplace"],
            ).count(),
            2,
        )

    def test_volume_close_date_does_not_precede_start_at_moscow_midnight(self) -> None:
        fixed_utc_now = datetime(2026, 7, 26, 21, 30, tzinfo=UTC)
        resolved_at = fixed_utc_now - timedelta(hours=1)
        expected_started_on = date(2026, 7, 27)
        expected_resolved_on = date(2026, 7, 26)

        self.assertEqual(
            timezone.localdate(fixed_utc_now, timezone=MOSCOW_TIME_ZONE),
            expected_started_on,
        )
        self.assertEqual(
            timezone.localdate(resolved_at, timezone=MOSCOW_TIME_ZONE),
            expected_resolved_on,
        )

        with patch(
            "apps.equipment_defects.services.volumes.timezone.now",
            return_value=fixed_utc_now,
        ):
            detected_at = resolved_at - timedelta(hours=1)
            record = register_defect(
                actor=self.operator,
                workplace=self.fixture["workplace"],
                equipment=self.fixture["equipment"],
                discovered_by=self.responsible,
                detected_at=detected_at,
                defect_description="Проверка закрытия тома на границе московской даты.",
            )
            record = confirm_deadline(
                record=record,
                actor=self.responsible,
                responsible=self.responsible,
                deadline=fixed_utc_now + timedelta(days=1),
            )
            record = confirm_resolution(
                record=record,
                actor=self.responsible,
                responsible=self.responsible,
                resolved_at=resolved_at,
                work_summary="Историческое время устранения сохранено без изменения.",
            )
            record = acknowledge_resolution(record=record, actor=self.operator)
            record = close_defect(record=record, actor=self.responsible)
            original_volume = record.equipment_defect_context.volume
            original_context_id = record.equipment_defect_context.pk

            new_volume = open_new_defect_volume(
                workplace=self.fixture["workplace"],
                actor=self.operator,
            )

        original_volume.refresh_from_db()
        record.refresh_from_db()
        self.assertEqual(original_volume.started_on, expected_started_on)
        self.assertEqual(original_volume.closed_on, expected_started_on)
        self.assertGreaterEqual(original_volume.closed_on, original_volume.started_on)
        self.assertEqual(stored_datetime(record, FIELD_RESOLVED_AT), resolved_at)
        self.assertEqual(new_volume.sequence_number, original_volume.sequence_number + 1)
        self.assertEqual(record.equipment_defect_context.pk, original_context_id)
        self.assertEqual(record.equipment_defect_context.volume_id, original_volume.pk)
        self.assertEqual(original_volume.defect_contexts.count(), 1)
        self.assertEqual(new_volume.defect_contexts.count(), 0)

    def test_volume_dates_use_moscow_day_across_utc_midnight(self) -> None:
        fixed_utc_now = datetime(2026, 7, 26, 21, 30, tzinfo=UTC)
        expected_moscow_date = date(2026, 7, 27)

        self.assertEqual(fixed_utc_now.date(), date(2026, 7, 26))
        self.assertEqual(
            timezone.localdate(fixed_utc_now, timezone=MOSCOW_TIME_ZONE),
            expected_moscow_date,
        )

        with patch(
            "apps.equipment_defects.services.volumes.timezone.now",
            return_value=fixed_utc_now,
        ):
            detected_at = fixed_utc_now - timedelta(hours=1)
            record = register_defect(
                actor=self.operator,
                workplace=self.fixture["workplace"],
                equipment=self.fixture["equipment"],
                discovered_by=self.responsible,
                detected_at=detected_at,
                defect_description="Проверка московской даты при переходе через полночь.",
            )
            record = confirm_deadline(
                record=record,
                actor=self.responsible,
                responsible=self.responsible,
                deadline=fixed_utc_now + timedelta(days=1),
            )
            record = confirm_resolution(
                record=record,
                actor=self.responsible,
                responsible=self.responsible,
                resolved_at=fixed_utc_now,
                work_summary="Проверено единое преобразование даты для тома.",
            )
            record = acknowledge_resolution(record=record, actor=self.operator)
            record = close_defect(record=record, actor=self.responsible)
            original_volume = record.equipment_defect_context.volume

            new_volume = open_new_defect_volume(
                workplace=self.fixture["workplace"],
                actor=self.operator,
            )

        original_volume.refresh_from_db()
        self.assertEqual(original_volume.started_on, expected_moscow_date)
        self.assertEqual(original_volume.closed_on, expected_moscow_date)
        self.assertEqual(new_volume.started_on, expected_moscow_date)

    def test_unresolved_record_keeps_old_volume_unclosed_after_new_volume_opens(self) -> None:
        record, _detected_at = self.register()
        original_volume = record.equipment_defect_context.volume

        new_volume = open_new_defect_volume(
            workplace=self.fixture["workplace"],
            actor=self.operator,
        )
        original_volume.refresh_from_db()

        self.assertFalse(original_volume.accepts_new_records)
        self.assertIsNone(original_volume.closed_on)
        self.assertTrue(new_volume.accepts_new_records)
        self.assertEqual(record.equipment_defect_context.volume_id, original_volume.pk)
