from __future__ import annotations

from datetime import datetime

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.authority_models import (
    AuthorityBasisStatus,
    AuthorityScopeKind,
    OperationalAuthorityGrant,
)
from apps.organizations.models import (
    Employee,
    OperationalRightDefinition,
    Organization,
    Workplace,
)

from ...models import (
    EntryForm,
    OperationalJournal,
    OperationalJournalSequence,
)
from ...services import (
    active_shift_for_journal,
    create_draft_entry,
    open_shift,
    register_entry,
)

OPJ_ACTION_CODES = (
    "OPJ.REGISTER",
    "OPJ.CORRECT",
    "OPJ.CANCEL",
    "OPJ.COMMUNICATION",
)


def ensure_demo_opj_authority(
    *,
    organization: Organization,
    actor: Employee,
    journal: OperationalJournal,
) -> None:
    right, _ = OperationalRightDefinition.objects.update_or_create(
        code="operational_journal_actions",
        defaults={
            "name": "Ведение оперативного журнала и оперативных переговоров",
            "category": "COMMUNICATIONS",
            "value_kind": "QUALIFIED",
            "description": (
                "Демонстрационное структурированное право на регистрацию, "
                "исправление и отмену записей ОЖ, а также фиксацию переговоров."
            ),
            "display_order": 35,
            "is_active": True,
        },
    )
    local_timezone = timezone.get_current_timezone()
    valid_from = timezone.make_aware(
        datetime(2026, 1, 1, 0, 0, 0),
        local_timezone,
    )
    valid_until = timezone.make_aware(
        datetime(2027, 12, 31, 23, 59, 0),
        local_timezone,
    )
    for action_code in OPJ_ACTION_CODES:
        OperationalAuthorityGrant.objects.update_or_create(
            employee=actor,
            action_code=action_code,
            scope_kind=AuthorityScopeKind.WORKPLACE,
            scope_reference=str(journal.workplace_id),
            valid_from=valid_from,
            basis_reference="DEMO-ONLY / OPJ-LIFECYCLE-001 / R1",
            defaults={
                "organization": organization,
                "right_definition": right,
                "scope_label": journal.workplace.name,
                "granting_organization": organization,
                "basis_status": AuthorityBasisStatus.CONFIRMED,
                "source_ids": ["DEMO-SYNTHETIC", "OPJ-LIFECYCLE-001"],
                "valid_until": valid_until,
                "is_active": True,
                "allow_substitution": False,
                "created_by": None,
            },
        )


class Command(BaseCommand):
    help = (
        "Создаёт безопасный демонстрационный оперативный журнал "
        "и открытую рабочую смену."
    )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        call_command("seed_demo_equipment", verbosity=0)
        call_command("seed_demo_documents", verbosity=0)
        organization = Organization.objects.get(code="DEMO")
        workplace = Workplace.objects.get(
            organization=organization,
            code="SHIFT_POOL",
        )
        actor = Employee.objects.select_related(
            "position",
            "workplace",
        ).get(
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
        ensure_demo_opj_authority(
            organization=organization,
            actor=actor,
            journal=journal,
        )

        local_timezone = timezone.get_current_timezone()

        def moment(
            year: int,
            month: int,
            day: int,
            hour: int,
            minute: int,
        ) -> datetime:
            return timezone.make_aware(
                datetime(year, month, day, hour, minute, 0),
                local_timezone,
            )

        if not journal.entries.exists():
            ktp = EquipmentAsset.objects.get(
                organization=organization,
                code="DEMO-KTP-01",
            )
            wtg = EquipmentAsset.objects.get(
                organization=organization,
                code="DEMO-WTG-01",
            )
            sdtu = EquipmentAsset.objects.get(
                organization=organization,
                code="DEMO-SDTU-01",
            )
            ru35 = EquipmentAsset.objects.get(
                organization=organization,
                code="DEMO-RU35",
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
                event_at=moment(2026, 7, 16, 8, 3),
                entry_form=EntryForm.TYPED,
                type_code="operational-information",
                type_title="Оперативная информация",
                content=(
                    "Демонстрационное дежурство начато. Проверены "
                    "доступность журнала и корректность серверного времени."
                ),
                typed_payload={
                    "demo": True,
                    "source": "local-presentation-profile",
                },
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(2026, 7, 16, 8, 17),
                entry_form=EntryForm.TYPED,
                type_code="equipment-state",
                type_title="Состояние оборудования",
                content=(
                    "По демонстрационному профилю КТП-01 и ВЭУ-01 "
                    "находятся в работе; замечаний по условной индикации нет."
                ),
                typed_payload={
                    "state": "ACTIVE",
                    "demo": True,
                },
                equipment=(ktp, wtg),
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(2026, 7, 16, 8, 42),
                content=(
                    "В демонстрационном контуре проверена доступность "
                    "средств передачи технологической информации."
                ),
                equipment=(sdtu,),
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(2026, 7, 16, 9, 5),
                entry_form=EntryForm.TYPED,
                type_code="document-reference",
                type_title="Ссылка на документ",
                content=(
                    "Для проверки типизированной связи просмотрен "
                    "демонстрационный порядок передачи информации."
                ),
                typed_payload={
                    "action": "reviewed",
                    "demo": True,
                },
                documents=(documents[0],),
            )
            register_entry(
                journal=journal,
                actor=actor,
                event_at=moment(2026, 7, 16, 9, 31),
                content=(
                    "Получена вымышленная информация о штатном состоянии "
                    "РУ 35 кВ; проверка выполнена только "
                    "в презентационном профиле."
                ),
                equipment=(ru35,),
                documents=(documents[1],),
            )

        shift = active_shift_for_journal(journal)
        if shift is None:
            shift = open_shift(
                journal=journal,
                actor=actor,
                planned_start_at=moment(2026, 7, 17, 8, 0),
                planned_end_at=moment(2026, 7, 17, 20, 15),
            )

        if not shift.draft_entries.exists():
            create_draft_entry(
                shift=shift,
                actor=actor,
                event_at=moment(2026, 7, 17, 10, 5),
                content=(
                    "Черновая демонстрационная запись: получены сведения "
                    "о штатном состоянии условного оборудования."
                ),
            )
            create_draft_entry(
                shift=shift,
                actor=actor,
                event_at=moment(2026, 7, 17, 11, 20),
                content=(
                    "Черновая демонстрационная запись: выполнена проверка "
                    "средств связи на рабочем месте."
                ),
            )
            create_draft_entry(
                shift=shift,
                actor=actor,
                event_at=moment(2026, 7, 17, 13, 40),
                content=(
                    "Черновая демонстрационная запись: подготовлены "
                    "сведения для последующей сдачи смены."
                ),
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Демонстрационный оперативный журнал и рабочая смена "
                "созданы или проверены."
            )
        )
        self.stdout.write(
            "Журналов: "
            f"{OperationalJournal.objects.filter(
                organization=organization
            ).count()}"
        )
        self.stdout.write(f"Записей: {journal.entries.count()}")
        self.stdout.write(
            "Связей с оборудованием: "
            f"{sum(
                entry.equipment_links.count()
                for entry in journal.entries.all()
            )}"
        )
        self.stdout.write(
            "Связей с документами: "
            f"{sum(
                entry.document_links.count()
                for entry in journal.entries.all()
            )}"
        )
        self.stdout.write(
            f"Открытых смен: {1 if active_shift_for_journal(journal) else 0}"
        )
        self.stdout.write(
            f"Черновых записей: {shift.draft_entries.count()}"
        )
