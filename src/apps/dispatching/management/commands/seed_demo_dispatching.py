from __future__ import annotations

from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Organization

from ...models import (
    AdjacentSubjectRelation,
    AdjacentSubjectRelationRevision,
    DispatchLevel,
    DispatchSubject,
    ManagementObject,
    ManagementRevision,
    PublicationStatus,
    SupervisionObject,
    SupervisionRevision,
)
from ...services import (
    publish_adjacent_relation_revision,
    publish_management_revision,
    publish_supervision_revision,
)


class Command(BaseCommand):
    help = "Создаёт обезличенный демонстрационный реестр управления и ведения."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        call_command("seed_demo_equipment", verbosity=0)
        organization = Organization.objects.get(code="DEMO")
        actor = Employee.objects.select_related("user").get(user__username="operator.demo")

        regional, _ = DispatchLevel.objects.get_or_create(
            organization=organization,
            code="regional-dispatch",
            defaults={
                "name": "Региональный диспетчерский уровень",
                "level_type": DispatchLevel.LevelType.DISPATCH,
                "rank": 10,
                "description": "Вымышленный вышестоящий диспетчерский уровень.",
                "is_active": True,
            },
        )
        station, _ = DispatchLevel.objects.get_or_create(
            organization=organization,
            code="station-operational",
            defaults={
                "name": "Оперативно-технологический уровень ЦОТУиЭ ВЭС Невинномысск",
                "level_type": DispatchLevel.LevelType.TECHNOLOGICAL,
                "rank": 20,
                "description": "Технологический уровень оперативного персонала трёх энергообъектов.",
                "is_active": True,
            },
        )

        station_shift, _ = DispatchSubject.objects.get_or_create(
            organization=organization,
            code="demo-station-shift",
            defaults={
                "name": "Оперативный персонал ЦОТУиЭ ВЭС Невинномысск",
                "short_name": "Оперативный персонал ЦОТУиЭ ВЭС Невинномысск",
                "subject_type": DispatchSubject.SubjectType.INTERNAL,
                "is_external": False,
                "description": "Вымышленный общий оперативный персонал обслуживаемых энергообъектов.",
                "is_active": True,
            },
        )
        regional_center, _ = DispatchSubject.objects.get_or_create(
            organization=organization,
            code="demo-regional-center",
            defaults={
                "name": "Демонстрационный региональный диспетчерский центр",
                "short_name": "Демо-РДЦ",
                "subject_type": DispatchSubject.SubjectType.HIGHER,
                "is_external": True,
                "description": "Вымышленный вышестоящий субъект.",
                "is_active": True,
            },
        )
        adjacent_center, _ = DispatchSubject.objects.get_or_create(
            organization=organization,
            code="demo-adjacent-center",
            defaults={
                "name": "Смежный диспетчерский центр — презентационный профиль",
                "short_name": "Смежный диспетчерский центр",
                "subject_type": DispatchSubject.SubjectType.ADJACENT,
                "is_external": True,
                "description": "Вымышленный смежный субъект.",
                "is_active": True,
            },
        )

        assets = {
            item.code: item
            for item in EquipmentAsset.objects.filter(
                organization=organization,
                code__in=(
                    "DEMO-RU35",
                    "DEMO-KL35-01",
                    "DEMO-WTG-01",
                    "DEMO-GRID-BAY-01",
                ),
            )
        }

        management_rows = (
            ("DEMO-RU35", regional, regional_center),
            ("DEMO-KL35-01", regional, regional_center),
            ("DEMO-WTG-01", station, station_shift),
        )
        for equipment_code, level, subject in management_rows:
            management_object, _ = ManagementObject.objects.get_or_create(
                organization=organization,
                equipment=assets[equipment_code],
                defaults={"notes": "Вымышленный демонстрационный объект управления."},
            )
            revision, _ = ManagementRevision.objects.get_or_create(
                management_object=management_object,
                revision_number=1,
                defaults={
                    "level": level,
                    "subject": subject,
                    "effective_from": date(2024, 1, 1),
                    "effective_until": None,
                    "basis_reference": "Презентационный перечень объектов управления № 1",
                    "change_summary": "Первичная демонстрационная редакция.",
                },
            )
            if revision.status == PublicationStatus.DRAFT:
                publish_management_revision(revision=revision, actor=actor)

        supervision_rows = (
            ("DEMO-RU35", station, station_shift, False),
            ("DEMO-KL35-01", station, station_shift, False),
            ("DEMO-WTG-01", station, station_shift, False),
            ("DEMO-GRID-BAY-01", regional, adjacent_center, True),
        )
        for equipment_code, level, subject, information_only in supervision_rows:
            supervision_object, _ = SupervisionObject.objects.get_or_create(
                organization=organization,
                equipment=assets[equipment_code],
                defaults={"notes": "Вымышленный демонстрационный объект ведения."},
            )
            revision, _ = SupervisionRevision.objects.get_or_create(
                supervision_object=supervision_object,
                revision_number=1,
                defaults={
                    "level": level,
                    "subject": subject,
                    "is_information_only": information_only,
                    "effective_from": date(2024, 1, 1),
                    "effective_until": None,
                    "basis_reference": "Презентационный перечень объектов ведения № 1",
                    "change_summary": "Первичная демонстрационная редакция.",
                },
            )
            if revision.status == PublicationStatus.DRAFT:
                publish_supervision_revision(revision=revision, actor=actor)

        adjacent_rows = (
            (
                "station-regional",
                station_shift,
                regional_center,
                "Передача команд, разрешений и оперативной информации.",
                "Взаимодействие ведётся по вымышленным демонстрационным каналам связи.",
            ),
            (
                "regional-adjacent",
                regional_center,
                adjacent_center,
                "Координация режима на смежной точке выдачи мощности.",
                "Стороны явно подтверждают получение демонстрационной информации.",
            ),
        )
        for code, source, target, scope, rules in adjacent_rows:
            relation, _ = AdjacentSubjectRelation.objects.get_or_create(
                organization=organization,
                code=code,
                defaults={
                    "source_subject": source,
                    "target_subject": target,
                    "is_active": True,
                },
            )
            revision, _ = AdjacentSubjectRelationRevision.objects.get_or_create(
                relation=relation,
                revision_number=1,
                defaults={
                    "effective_from": date(2024, 1, 1),
                    "effective_until": None,
                    "interaction_scope": scope,
                    "communication_rules": rules,
                    "basis_reference": "Презентационный регламент взаимодействия № 1",
                    "change_summary": "Первичная демонстрационная редакция.",
                },
            )
            if revision.status == PublicationStatus.DRAFT:
                publish_adjacent_relation_revision(revision=revision, actor=actor)

        self.stdout.write("Демонстрационный реестр управления и ведения создан или проверен.")
        self.stdout.write(f"Уровней: {DispatchLevel.objects.filter(organization=organization).count()}")
        self.stdout.write(f"Субъектов: {DispatchSubject.objects.filter(organization=organization).count()}")
        self.stdout.write(
            "Опубликованных управлений: "
            f"{ManagementRevision.objects.filter(status=PublicationStatus.PUBLISHED).count()}"
        )
        self.stdout.write(
            "Опубликованных ведений: "
            f"{SupervisionRevision.objects.filter(status=PublicationStatus.PUBLISHED).count()}"
        )
        self.stdout.write(
            "Взаимодействий смежных субъектов: "
            f"{AdjacentSubjectRelation.objects.filter(organization=organization).count()}"
        )
