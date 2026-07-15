from __future__ import annotations

from datetime import date

from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.normatives.models import (
    OrganizationConfigurationRevision,
)
from apps.normatives.models import (
    PublicationStatus as NormativePublicationStatus,
)
from apps.normatives.services import publish_configuration_revision
from apps.organizations.models import Employee, Organization

from ...models import (
    EnergySite,
    EquipmentAlias,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentRelation,
    EquipmentType,
    PublicationStatus,
)
from ...services import publish_equipment_name_revision


class Command(BaseCommand):
    help = "Создаёт обезличенный демонстрационный реестр оборудования."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        call_command("seed_demo_organization", verbosity=0)
        call_command("seed_demo_normatives", verbosity=0)

        organization = Organization.objects.get(code="DEMO")
        actor = Employee.objects.select_related("user").get(
            user__username="operator.demo"
        )

        equipment_types: dict[str, EquipmentType] = {}
        type_rows = (
            (
                "switchgear",
                "Распределительное устройство",
                EquipmentType.Category.SWITCHGEAR,
            ),
            (
                "cell",
                "Ячейка распределительного устройства",
                EquipmentType.Category.SWITCHGEAR,
            ),
            (
                "ktp",
                "Комплектная трансформаторная подстанция",
                EquipmentType.Category.KTP,
            ),
            (
                "wtg",
                "Ветроэнергетическая установка",
                EquipmentType.Category.WTG,
            ),
            (
                "cable-line",
                "Кабельная линия",
                EquipmentType.Category.LINE,
            ),
            (
                "rpa",
                "Комплект релейной защиты и автоматики",
                EquipmentType.Category.RPA,
            ),
            (
                "sdtu",
                "Комплекс СДТУ",
                EquipmentType.Category.SDTU,
            ),
            (
                "substation-bay",
                "Присоединение подстанции",
                EquipmentType.Category.SUBSTATION,
            ),
        )
        for code, name, category in type_rows:
            equipment_types[code], _ = EquipmentType.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "category": category,
                    "description": "Вымышленный демонстрационный вид оборудования.",
                    "is_active": True,
                },
            )

        wind_site, _ = EnergySite.objects.update_or_create(
            organization=organization,
            code="demo-wpp",
            defaults={
                "name": "Кочубеевская ВЭС — презентационный профиль",
                "short_name": "Кочубеевская ВЭС",
                "site_type": EnergySite.SiteType.WIND_POWER_PLANT,
                "is_external": False,
                "is_active": True,
            },
        )
        grid_site, _ = EnergySite.objects.update_or_create(
            organization=organization,
            code="demo-grid-substation",
            defaults={
                "name": "ПС 330 кВ Северная — презентационный смежный объект",
                "short_name": "ПС 330 кВ Северная",
                "site_type": EnergySite.SiteType.SUBSTATION,
                "is_external": True,
                "is_active": True,
            },
        )

        assets: dict[str, EquipmentAsset] = {}

        def asset(
            code: str,
            *,
            site: EnergySite,
            type_code: str,
            technical_name: str,
            parent_code: str | None = None,
            voltage: str = "",
            external: bool = False,
            attributes: dict | None = None,
        ) -> EquipmentAsset:
            parent = assets.get(parent_code) if parent_code else None
            item, _ = EquipmentAsset.objects.update_or_create(
                organization=organization,
                code=code,
                defaults={
                    "site": site,
                    "equipment_type": equipment_types[type_code],
                    "parent": parent,
                    "technical_name": technical_name,
                    "status": EquipmentAsset.Status.ACTIVE,
                    "voltage_level": voltage,
                    "commissioned_on": date(2024, 1, 1),
                    "decommissioned_on": None,
                    "attributes": attributes or {},
                    "is_external": external,
                },
            )
            assets[code] = item
            return item

        asset(
            "DEMO-RU35",
            site=wind_site,
            type_code="switchgear",
            technical_name="Распределительное устройство 35 кВ",
            voltage="35 кВ",
        )
        asset(
            "DEMO-RU35-S1",
            site=wind_site,
            type_code="switchgear",
            technical_name="Секция 1 распределительного устройства 35 кВ",
            parent_code="DEMO-RU35",
            voltage="35 кВ",
        )
        asset(
            "DEMO-CELL-01",
            site=wind_site,
            type_code="cell",
            technical_name="Ячейка 1 секции 1 распределительного устройства 35 кВ",
            parent_code="DEMO-RU35-S1",
            voltage="35 кВ",
        )
        asset(
            "DEMO-KTP-01",
            site=wind_site,
            type_code="ktp",
            technical_name="Комплектная трансформаторная подстанция установки 1",
            voltage="35/0,69 кВ",
            attributes={"transformer_count": 1, "rated_power_mva": 4.2},
        )
        asset(
            "DEMO-WTG-01",
            site=wind_site,
            type_code="wtg",
            technical_name="Ветроэнергетическая установка 1",
            voltage="0,69 кВ",
            attributes={"demo_nominal_power_mw": 4.0},
        )
        asset(
            "DEMO-KL35-01",
            site=wind_site,
            type_code="cable-line",
            technical_name="Кабельная линия 35 кВ присоединения 1",
            voltage="35 кВ",
        )
        asset(
            "DEMO-RZA-01",
            site=wind_site,
            type_code="rpa",
            technical_name="Комплект РЗА ячейки 1",
            parent_code="DEMO-CELL-01",
            voltage="35 кВ",
        )
        asset(
            "DEMO-SDTU-01",
            site=wind_site,
            type_code="sdtu",
            technical_name="Комплекс СДТУ демонстрационного объекта",
        )
        asset(
            "DEMO-GRID-BAY-01",
            site=grid_site,
            type_code="substation-bay",
            technical_name="Присоединение демонстрационной ВЭС на смежной ПС",
            voltage="330 кВ",
            external=True,
        )

        name_rows = {
            "DEMO-RU35": (
                (1, "РУ 35 кВ Демо-ВЭС", date(2024, 1, 1)),
                (2, "РУ 35 кВ Кочубеевской ВЭС", date(2026, 7, 16)),
            ),
            "DEMO-RU35-S1": (
                (1, "1 секция шин 35 кВ Демо-ВЭС", date(2024, 1, 1)),
                (2, "1 секция шин 35 кВ Кочубеевской ВЭС", date(2026, 7, 16)),
            ),
            "DEMO-CELL-01": (
                (1, "ячейка 1 КЛ-35 кВ Демо-ВЭС", date(2024, 1, 1)),
                (2, "ячейка № 1 КЛ 35 кВ КТП-01", date(2026, 7, 16)),
            ),
            "DEMO-KTP-01": (
                (1, "КТП-1 Демо-ВЭС", date(2024, 1, 1)),
                (2, "КТП-01 Демо-ВЭС", date(2026, 1, 1)),
                (3, "КТП-01 Кочубеевской ВЭС", date(2026, 7, 16)),
            ),
            "DEMO-WTG-01": (
                (1, "ВЭУ-01 Демо-ВЭС", date(2024, 1, 1)),
                (2, "ВЭУ-01 Кочубеевской ВЭС", date(2026, 7, 16)),
            ),
            "DEMO-KL35-01": (
                (1, "КЛ 35 кВ КТП-01 — ячейка 1", date(2024, 1, 1)),
                (2, "КЛ 35 кВ КТП-01 — ячейка № 1", date(2026, 7, 16)),
            ),
            "DEMO-RZA-01": (
                (1, "РЗА ячейки 1 КЛ-35 кВ", date(2024, 1, 1)),
                (2, "комплект РЗА ячейки № 1 КЛ 35 кВ", date(2026, 7, 16)),
            ),
            "DEMO-SDTU-01": (
                (1, "СДТУ Демо-ВЭС", date(2024, 1, 1)),
                (2, "СДТУ Кочубеевской ВЭС", date(2026, 7, 16)),
            ),
            "DEMO-GRID-BAY-01": (
                (1, "присоединение Демо-ВЭС на Демо-ПС 330 кВ", date(2024, 1, 1)),
                (2, "присоединение Кочубеевской ВЭС на ПС 330 кВ Северная", date(2026, 7, 16)),
            ),
        }
        for equipment_code, revisions in name_rows.items():
            for revision_number, dispatcher_name, effective_from in revisions:
                revision, _ = EquipmentNameRevision.objects.get_or_create(
                    equipment=assets[equipment_code],
                    revision_number=revision_number,
                    defaults={
                        "dispatcher_name": dispatcher_name,
                        "effective_from": effective_from,
                        "effective_until": None,
                        "basis_reference": (
                            "Безопасная презентационная редакция "
                            f"№ {revision_number}"
                        ),
                    },
                )
                if revision.status == PublicationStatus.DRAFT:
                    publish_equipment_name_revision(
                        revision=revision,
                        actor=actor,
                    )

        alias_rows = (
            (
                "DEMO-KTP-01",
                "КТП 1",
                EquipmentAlias.AliasType.LEGACY,
                date(2024, 1, 1),
            ),
            (
                "DEMO-KTP-01",
                "Блочная КТП №1",
                EquipmentAlias.AliasType.LOCAL,
                date(2024, 1, 1),
            ),
            (
                "DEMO-WTG-01",
                "ВЭУ 1",
                EquipmentAlias.AliasType.SEARCH,
                date(2024, 1, 1),
            ),
            (
                "DEMO-KL35-01",
                "КЛ КТП-1",
                EquipmentAlias.AliasType.LEGACY,
                date(2024, 1, 1),
            ),
        )
        for equipment_code, alias_value, alias_type, valid_from in alias_rows:
            normalized = " ".join(alias_value.split()).casefold()
            if not EquipmentAlias.objects.filter(
                organization=organization,
                normalized_alias=normalized,
                valid_from=valid_from,
            ).exists():
                EquipmentAlias.objects.create(
                    organization=organization,
                    equipment=assets[equipment_code],
                    alias=alias_value,
                    alias_type=alias_type,
                    valid_from=valid_from,
                    valid_until=None,
                    basis_reference="Вымышленный демонстрационный алиас.",
                    created_by=actor,
                )

        relation_rows = (
            (
                "DEMO-KTP-01",
                "DEMO-WTG-01",
                EquipmentRelation.RelationType.FEEDS,
                "КТП питает установку на стороне 0,69 кВ.",
            ),
            (
                "DEMO-KL35-01",
                "DEMO-KTP-01",
                EquipmentRelation.RelationType.CONNECTS,
                "Кабельная линия соединена с КТП.",
            ),
            (
                "DEMO-KL35-01",
                "DEMO-CELL-01",
                EquipmentRelation.RelationType.CONNECTS,
                "Кабельная линия подключена к ячейке РУ 35 кВ.",
            ),
            (
                "DEMO-RZA-01",
                "DEMO-CELL-01",
                EquipmentRelation.RelationType.PROTECTS,
                "Комплект РЗА защищает присоединение.",
            ),
            (
                "DEMO-SDTU-01",
                "DEMO-WTG-01",
                EquipmentRelation.RelationType.MONITORS,
                "СДТУ получает телеметрию установки.",
            ),
            (
                "DEMO-CELL-01",
                "DEMO-GRID-BAY-01",
                EquipmentRelation.RelationType.RELATED,
                "Смежные точки выдачи мощности демонстрационного объекта.",
            ),
        )
        for source_code, target_code, relation_type, description in relation_rows:
            EquipmentRelation.objects.get_or_create(
                source_equipment=assets[source_code],
                target_equipment=assets[target_code],
                relation_type=relation_type,
                valid_from=date(2024, 1, 1),
                defaults={
                    "valid_until": None,
                    "description": description,
                    "basis_reference": "Вымышленная демонстрационная схема.",
                    "created_by": actor,
                },
            )

        configuration, _ = OrganizationConfigurationRevision.objects.get_or_create(
            organization=organization,
            revision_number=2,
            defaults={
                "effective_from": date(2026, 7, 15),
                "effective_until": None,
                "configuration": {
                    "profile": "демонстрационная ВЭС",
                    "modules": {
                        "documents": True,
                        "normatives": True,
                        "equipment": True,
                    },
                    "equipment_registry": {
                        "dispatcher_names_are_versioned": True,
                        "real_data_allowed_in_repository": False,
                    },
                    "language": "ru",
                },
                "change_summary": (
                    "Подключён демонстрационный реестр оборудования "
                    "и версионируемые диспетчерские наименования."
                ),
                "created_by": actor,
            },
        )
        if configuration.status == NormativePublicationStatus.DRAFT:
            publish_configuration_revision(
                revision=configuration,
                actor=actor,
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Демонстрационный реестр оборудования создан или проверен."
            )
        )
        self.stdout.write(f"Энергообъектов: {EnergySite.objects.count()}")
        self.stdout.write(f"Видов оборудования: {EquipmentType.objects.count()}")
        self.stdout.write(f"Единиц оборудования: {EquipmentAsset.objects.count()}")
        self.stdout.write(
            "Опубликованных диспетчерских наименований: "
            f"{EquipmentNameRevision.objects.filter(status='PUBLISHED').count()}"
        )
        self.stdout.write(f"Алиасов: {EquipmentAlias.objects.count()}")
        self.stdout.write(f"Связей оборудования: {EquipmentRelation.objects.count()}")
