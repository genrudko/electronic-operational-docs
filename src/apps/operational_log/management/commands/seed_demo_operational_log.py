from __future__ import annotations

from datetime import datetime

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Organization, Workplace

from ...models import EntryForm, OperationalJournal, OperationalJournalSequence
from ...services import register_entry


class Command(BaseCommand):
    help = "Создаёт безопасный демонстрационный оперативный журнал."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        call_command("seed_demo_equipment", verbosity=0)
        call_command("seed_demo_documents", verbosity=0)
        organization = Organization.objects.get(code="DEMO")
        workplace = Workplace.objects.get(organization=organization, code="SHIFT_POOL")
        actor = Employee.objects.select_related("position", "workplace").get(
            organization=organization,
            user__username="operator.demo",
        )
        journal, _ = OperationalJournal.objects.update_or_create(
            organization=organization,
            code="shift-operational-log",
            defaults={
                "workplace": workplace,
                "title": "Оперативный журнал сменного персонала",
                "is_active": True,
            },
        )
        OperationalJournalSequence.objects.get_or_create(journal=journal)

        if not journal.entries.exists():
            local_timezone = timezone.get_current_timezone()

            def moment(hour: int, minute: int) -> datetime:
                return timezone.make_aware(
                    datetime(2026, 7, 16, hour, minute, 0),
                    local_timezone,
                )

            ktp = EquipmentAsset.objects.get(
                organization=organization, code="DEMO-KTP-01"
            )
            wtg = EquipmentAsset.objects.get(
                organization=organization, code="DEMO-WTG-01"
            )
            sdtu = EquipmentAsset.objects.get(
                organization=organization, code="DEMO-SDTU-01"
            )
            ru35 = EquipmentAsset.objects.get(
                organization=organization, code="DEMO-RU35"
            )
            documents = list(
                Document.objects.filter(
                    organization=organization,
                    status=Document.Status.REGISTERED,
                ).order_by("sequence_number")
            )

            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(8, 3),
                entry_form=EntryForm.TYPED,
                type_code="operational-information",
                type_title="Оперативная информация",
                content=(
                    "Демонстрационное дежурство начато. Проверены доступность журнала "
                    "и корректность серверного времени."
                ),
                typed_payload={"demo": True, "source": "local-presentation-profile"},
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(8, 17),
                entry_form=EntryForm.TYPED,
                type_code="equipment-state",
                type_title="Состояние оборудования",
                content=(
                    "По демонстрационному профилю КТП-01 и ВЭУ-01 находятся в работе; "
                    "замечаний по условной индикации нет."
                ),
                typed_payload={"state": "ACTIVE", "demo": True},
                equipment=(ktp, wtg),
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(8, 42),
                content=(
                    "В демонстрационном контуре проверена доступность средств передачи "
                    "технологической информации."
                ),
                equipment=(sdtu,),
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(9, 5),
                entry_form=EntryForm.TYPED,
                type_code="document-reference",
                type_title="Ссылка на документ",
                content=(
                    "Для проверки типизированной связи просмотрен демонстрационный "
                    "порядок передачи информации."
                ),
                typed_payload={"action": "reviewed", "demo": True},
                documents=(documents[0],),
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(9, 31),
                content=(
                    "Получена вымышленная информация о штатном состоянии РУ 35 кВ; "
                    "проверка выполнена только в презентационном профиле."
                ),
                equipment=(ru35,),
                documents=(documents[1],),
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Демонстрационный оперативный журнал создан или проверен."
            )
        )
        self.stdout.write(
            f"Журналов: {OperationalJournal.objects.filter(organization=organization).count()}"
        )
        self.stdout.write(f"Записей: {journal.entries.count()}")
        self.stdout.write(
            f"Связей с оборудованием: {sum(entry.equipment_links.count() for entry in journal.entries.all())}"
        )
        self.stdout.write(
            f"Связей с документами: {sum(entry.document_links.count() for entry in journal.entries.all())}"
        )
