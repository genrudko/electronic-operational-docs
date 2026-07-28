from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.equipment.models import EquipmentAsset
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee

from ...models import EquipmentDefectContext
from ...services import (
    acknowledge_resolution,
    close_defect,
    confirm_deadline,
    confirm_resolution,
    ensure_defect_document_type,
    extend_deadline,
    register_defect,
)

PRESENTATION_RECORDS = (
    {
        "key": "defect-registered",
        "description": "При осмотре выявлено ослабление крепления защитного кожуха привода.",
        "state": "REGISTERED",
    },
    {
        "key": "defect-in-progress",
        "description": "Обнаружено периодическое дребезжание вспомогательного контакта выключателя.",
        "state": "IN_PROGRESS",
    },
    {
        "key": "defect-extended",
        "description": "Выявлено снижение яркости световой индикации шкафа управления.",
        "state": "EXTENDED",
    },
    {
        "key": "defect-resolved",
        "description": "Зафиксировано повреждение маркировочной таблички кабельной линии.",
        "state": "RESOLVED",
    },
    {
        "key": "defect-closed",
        "description": "Обнаружено загрязнение вентиляционной решётки шкафа автоматики.",
        "state": "CLOSED",
    },
)


class Command(BaseCommand):
    help = "Идемпотентно создаёт source-bound презентационный набор журнала дефектов."

    @transaction.atomic
    def handle(self, *args, **options):
        operator = (
            Employee.objects.filter(user__username="operator.demo", is_active=True)
            .select_related(
                "organization",
                "division",
                "position",
                "workplace",
            )
            .first()
        )
        if operator is None:
            self.stdout.write(
                self.style.WARNING(
                    "operator.demo отсутствует: презентационные дефекты не создавались."
                )
            )
            return
        if operator.workplace_id is None:
            raise CommandError("У operator.demo отсутствует основное рабочее место.")

        supervisor = (
            Employee.objects.filter(
                user__username="supervisor.demo",
                organization=operator.organization,
                is_active=True,
            )
            .select_related("division", "position", "workplace")
            .first()
            or operator
        )
        acknowledger = (
            Employee.objects.filter(
                organization=operator.organization,
                position__is_operational=True,
                is_active=True,
            )
            .select_related("division", "position", "workplace")
            .order_by("pk")
            .first()
        )
        if acknowledger is None:
            raise CommandError(
                "Для презентационного закрытия дефекта нужен действующий оперативный работник."
            )

        equipment = list(
            EquipmentAsset.objects.filter(
                organization=operator.organization,
                site__is_active=True,
            )
            .select_related("site", "equipment_type")
            .order_by("site__name", "code")[:5]
        )
        if not equipment:
            raise CommandError(
                "Нельзя создать презентационный журнал дефектов без оборудования."
            )

        ensure_defect_document_type(operator)
        source_entry = (
            OperationalLogEntry.objects.filter(
                journal__organization=operator.organization,
                journal__workplace=operator.workplace,
            )
            .select_related("journal", "journal__workplace")
            .order_by("-registered_at", "-pk")
            .first()
        )
        now = timezone.now().replace(second=0, microsecond=0)
        created = 0
        skipped = 0

        for index, specification in enumerate(PRESENTATION_RECORDS):
            if EquipmentDefectContext.objects.filter(
                presentation_key=specification["key"]
            ).exists():
                skipped += 1
                continue

            detected_at = now - timedelta(days=8 - index, hours=2)
            record = register_defect(
                actor=operator,
                workplace=operator.workplace,
                equipment=equipment[index % len(equipment)],
                discovered_by=supervisor if index == 0 else operator,
                detected_at=detected_at,
                defect_description=specification["description"],
                operational_log_entry=(source_entry if index == 0 else None),
                presentation_key=specification["key"],
            )
            state = specification["state"]
            if state == "REGISTERED":
                created += 1
                continue

            first_deadline = detected_at + timedelta(days=4)
            record = confirm_deadline(
                record=record,
                actor=supervisor,
                responsible=supervisor,
                deadline=first_deadline,
            )
            if state == "IN_PROGRESS":
                created += 1
                continue

            if state == "EXTENDED":
                extend_deadline(
                    record=record,
                    actor=supervisor,
                    new_deadline=first_deadline + timedelta(days=3),
                    reason="Ожидается безопасное демонстрационное окно для выполнения работ.",
                )
                created += 1
                continue

            resolved_at = min(now - timedelta(hours=4), detected_at + timedelta(days=2))
            record = confirm_resolution(
                record=record,
                actor=supervisor,
                responsible=supervisor,
                resolved_at=resolved_at,
                work_summary=(
                    "Дефект устранён: выполнена проверка, восстановлено исправное "
                    "состояние и подтверждён результат осмотром."
                ),
            )
            if state == "RESOLVED":
                created += 1
                continue

            record = acknowledge_resolution(record=record, actor=acknowledger)
            close_defect(record=record, actor=supervisor)
            created += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Презентационный журнал дефектов: создано {created}, уже было {skipped}."
            )
        )
