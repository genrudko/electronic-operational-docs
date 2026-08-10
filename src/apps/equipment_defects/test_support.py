from __future__ import annotations

import hashlib
from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.equipment.models import EnergySite, EquipmentAsset, EquipmentType
from apps.operational_documents.models import OperationalDocumentRecord
from apps.operational_log.models import OperationalJournal
from apps.operational_log.services import register_entry
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Workplace,
)
from apps.system.models import ModuleLifecycleState, ModuleScopeType
from apps.system.module_registry import normalize_context, transition_module_state
from tests.credential_fixtures import ephemeral_credential

from .services import register_defect

User = get_user_model()


class DefectFixtureMixin:
    @classmethod
    def create_organization_fixture(cls, suffix: str = "") -> dict[str, Any]:
        label = suffix or "основная"
        raw_identifier = suffix.casefold() or "main"
        normalized = (
            raw_identifier
            if raw_identifier.isascii() and raw_identifier.replace("-", "").isalnum()
            else f"fx{hashlib.sha256(raw_identifier.encode('utf-8')).hexdigest()[:6]}"
        )
        organization = Organization.objects.create(
            code=f"ORG-{normalized.upper()}",
            name=f"Демонстрационная организация {label}",
            short_name=f"Демо {label}",
        )
        division = Division.objects.create(
            organization=organization,
            code=f"DIV-{normalized.upper()}",
            name="ЦОТУиЭ ВЭС",
        )
        workplace = Workplace.objects.create(
            organization=organization,
            division=division,
            code=f"WP-{normalized.upper()}",
            name=f"Демонстрационная ВЭС {label}",
        )
        operational_position = Position.objects.create(
            organization=organization,
            code=f"OP-{normalized.upper()}",
            name="Начальник смены ВЭС",
            is_operational=True,
        )
        responsible_position = Position.objects.create(
            organization=organization,
            code=f"RESP-{normalized.upper()}",
            name="Ответственный за эксплуатацию оборудования",
        )
        site = EnergySite.objects.create(
            organization=organization,
            code=f"site-{normalized}",
            name=f"Демонстрационная ВЭС {label}",
            short_name=f"Демо ВЭС {label}",
            site_type=EnergySite.SiteType.WIND_POWER_PLANT,
        )
        equipment_type, _created = EquipmentType.objects.get_or_create(
            code=f"test-switch-{normalized}",
            defaults={
                "name": f"Демонстрационный выключатель {label}",
                "category": EquipmentType.Category.SWITCHGEAR,
            },
        )
        equipment = EquipmentAsset.objects.create(
            organization=organization,
            site=site,
            equipment_type=equipment_type,
            code=f"QF-{normalized.upper()}-01",
            technical_name=f"Выключатель демонстрационный {label}",
        )
        return {
            "organization": organization,
            "division": division,
            "workplace": workplace,
            "operational_position": operational_position,
            "responsible_position": responsible_position,
            "equipment": equipment,
        }

    @classmethod
    def create_employee(
        cls,
        *,
        fixture: dict[str, Any],
        username: str,
        personnel_number: str,
        last_name: str,
        position_key: str,
    ) -> Employee:
        user = User.objects.create_user(
            username=username,
            password=ephemeral_credential(personnel_number),
        )
        return Employee.objects.create(
            organization=fixture["organization"],
            division=fixture["division"],
            position=fixture[position_key],
            workplace=fixture["workplace"],
            user=user,
            personnel_number=personnel_number,
            last_name=last_name,
            first_name="Тест",
            middle_name="Тестович",
        )


class EquipmentDefectSourceBoundBase(DefectFixtureMixin):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.fixture = cls.create_organization_fixture()
        cls.other_fixture = cls.create_organization_fixture("другая")
        cls.operator = cls.create_employee(
            fixture=cls.fixture,
            username="operator.demo",
            personnel_number="OP-001",
            last_name="Операторов",
            position_key="operational_position",
        )
        cls.supervisor = cls.create_employee(
            fixture=cls.fixture,
            username="supervisor.demo",
            personnel_number="SUP-001",
            last_name="Ответственный",
            position_key="responsible_position",
        )
        cls.discoverer = cls.create_employee(
            fixture=cls.fixture,
            username="discoverer.demo",
            personnel_number="DISC-001",
            last_name="Обнаруживший",
            position_key="responsible_position",
        )
        cls.other_employee = cls.create_employee(
            fixture=cls.other_fixture,
            username="other.demo",
            personnel_number="OTHER-001",
            last_name="Другой",
            position_key="operational_position",
        )
        cls.journal = OperationalJournal.objects.create(
            organization=cls.fixture["organization"],
            workplace=cls.fixture["workplace"],
            code="operational-main",
            title="Оперативный журнал",
        )
        cls.operational_entry = register_entry(
            journal=cls.journal,
            actor=cls.operator,
            event_at=timezone.now() - timedelta(hours=3),
            content="При осмотре выявлено замечание по демонстрационному выключателю.",
            equipment=[cls.fixture["equipment"]],
        )

        # Module state is test data, not a migration default. Existing defect tests
        # explicitly activate the representative module instead of relying on an
        # upgrade-time auto-activation shortcut.
        context = normalize_context(
            organization=cls.fixture["organization"],
            workplace=cls.fixture["workplace"],
        )
        transition_module_state(
            module_id="DEFECT",
            context=context,
            scope_type=ModuleScopeType.ORGANIZATION,
            new_state=ModuleLifecycleState.CONFIGURED,
            actor_identity="tests/equipment-defects",
            reason="configure defect module for defect fixture",
            configuration_ready=True,
        )
        transition_module_state(
            module_id="DEFECT",
            context=context,
            scope_type=ModuleScopeType.ORGANIZATION,
            new_state=ModuleLifecycleState.ACTIVE,
            actor_identity="tests/equipment-defects",
            reason="activate defect module for defect fixture",
        )

    def register(self, *, link_to_log: bool = False) -> OperationalDocumentRecord:
        return register_defect(
            actor=self.operator,
            workplace=self.fixture["workplace"],
            equipment=self.fixture["equipment"],
            discovered_by=self.discoverer,
            detected_at=timezone.now() - timedelta(hours=2),
            defect_description="Ослаблено крепление защитного кожуха привода.",
            operational_log_entry=self.operational_entry if link_to_log else None,
        )
