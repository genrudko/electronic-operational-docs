from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Any

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.urls import reverse
from django.utils import timezone

from apps.equipment.models import EnergySite, EquipmentAsset, EquipmentType
from apps.operational_documents.models import OperationalDocumentRecord
from apps.operational_documents.services import canonical_json, sha256_text
from apps.operational_log.models import OperationalJournal
from apps.operational_log.services import register_entry
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Workplace,
)

from .constants import (
    APPROVED_PRINT_COLUMNS,
    DEADLINE_EXTENSION_TEXT,
    DOCUMENT_TYPE_CODE,
    DOCUMENT_TYPE_NAME,
    FIELD_DEFINITIONS,
    NUMBER_PREFIX,
    PARTICIPANT_ROLE_DEFINITIONS,
    ROLE_DISCOVERED_BY,
    ROLE_OPERATIONAL_ACKNOWLEDGER,
    SOURCE_APPENDIX,
    SOURCE_DOCUMENT,
    SOURCE_SECTION,
    STATUS_CLOSED,
    STATUS_DEFINITIONS,
    STATUS_IN_PROGRESS,
    STATUS_REGISTERED,
    STATUS_RESOLVED,
    TRANSITION_DEFINITIONS,
)
from .models import (
    DefectActionCode,
    EquipmentDefectActionEvidence,
    EquipmentDefectContext,
    EquipmentDefectOperationalLogLink,
)
from .services import (
    acknowledge_resolution,
    close_defect,
    confirm_deadline,
    confirm_resolution,
    ensure_defect_document_type,
    extend_deadline,
    register_defect,
)


User = get_user_model()


class DefectFixtureMixin:
    @classmethod
    def create_organization_fixture(cls, suffix: str = "") -> dict[str, Any]:
        normalized = suffix.lower() or "main"
        organization = Organization.objects.create(
            code=f"ORG-{normalized.upper()}",
            name=f"Демонстрационная организация {suffix or 'основная'}",
            short_name=f"Демо {suffix or 'основная'}",
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
            name=f"Демонстрационная ВЭС {suffix or 'основная'}",
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
            name=f"Демонстрационная ВЭС {suffix or 'основная'}",
            short_name=f"Демо ВЭС {suffix or 'основная'}",
            site_type=EnergySite.SiteType.WIND_POWER_PLANT,
        )
        equipment_type, _created = EquipmentType.objects.get_or_create(
            code=f"test-switch-{normalized}",
            defaults={
                "name": f"Демонстрационный выключатель {suffix or 'основной'}",
                "category": EquipmentType.Category.SWITCHGEAR,
            },
        )
        equipment = EquipmentAsset.objects.create(
            organization=organization,
            site=site,
            equipment_type=equipment_type,
            code=f"QF-{normalized.upper()}-01",
            technical_name=f"Выключатель демонстрационный {suffix or 'основной'}",
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
        user = User.objects.create_user(username=username, password="TestOnly!2026")
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


class EquipmentDefectSourceBoundTests(DefectFixtureMixin, TestCase):
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

    def test_exact_source_contract_is_published_idempotently_and_immutable(self) -> None:
        revision = ensure_defect_document_type(self.operator)
        second = ensure_defect_document_type(self.operator)

        self.assertEqual(revision.pk, second.pk)
        self.assertEqual(revision.document_type.code, DOCUMENT_TYPE_CODE)
        self.assertEqual(revision.document_type.name, DOCUMENT_TYPE_NAME)
        self.assertEqual(revision.number_prefix, NUMBER_PREFIX)
        self.assertEqual(revision.field_definitions, FIELD_DEFINITIONS)
        self.assertEqual(revision.status_definitions, STATUS_DEFINITIONS)
        self.assertEqual(revision.transition_definitions, TRANSITION_DEFINITIONS)
        self.assertEqual(
            revision.participant_role_definitions,
            PARTICIPANT_ROLE_DEFINITIONS,
        )
        self.assertEqual(len(revision.sha256), 64)
        self.assertEqual(SOURCE_DOCUMENT, "И-00-007-ОР-2025 версия 2")
        self.assertEqual(SOURCE_SECTION, "11")
        self.assertEqual(SOURCE_APPENDIX, "8")

        revision.number_prefix = "ИЗМ"
        with self.assertRaises(ValidationError):
            revision.save()

    def test_registration_requires_equipment_and_separates_created_and_discovered(self) -> None:
        record = self.register()
        discovered = record.participants.get(role_code=ROLE_DISCOVERED_BY)

        self.assertEqual(record.status_code, STATUS_REGISTERED)
        self.assertEqual(record.created_by, self.operator)
        self.assertEqual(discovered.employee, self.discoverer)
        self.assertNotEqual(record.created_by_id, discovered.employee_id)
        self.assertEqual(record.equipment_links.count(), 1)
        self.assertTrue(record.equipment_links.get().dispatcher_name_snapshot)

        with self.assertRaises(ValidationError):
            register_defect(
                actor=self.operator,
                workplace=self.fixture["workplace"],
                equipment=self.other_fixture["equipment"],
                discovered_by=self.discoverer,
                detected_at=timezone.now() - timedelta(hours=1),
                defect_description="Недопустимая межорганизационная связь.",
            )

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

    def test_dedicated_routes_and_exact_six_column_print_contract(self) -> None:
        record = self.register(link_to_log=True)
        self.client.force_login(self.operator.user)

        registry_response = self.client.get(reverse("equipment_defects:registry"))
        self.assertEqual(registry_response.status_code, 200)
        registry_html = registry_response.content.decode("utf-8")
        registry_markers = (
            "Дата обнаружения дефекта",
            "Наименование ЛЭП, оборудования, устройства",
            "Срок устранения",
            "Дата устранения дефекта",
            "Содержание выполненных работ",
            "Ф.И.О., подписи оперативного персонала",
        )
        positions = [registry_html.index(marker) for marker in registry_markers]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("Конструктор формы", registry_html)
        self.assertNotIn("JSON schema", registry_html)

        detail_response = self.client.get(
            reverse("equipment_defects:detail", args=[record.public_id])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Подтвердить срок")
        self.assertContains(detail_response, "authenticated user")
        self.assertContains(detail_response, "не УКЭП")

        source_response = self.client.get(
            reverse(
                "equipment_defects:create_from_operational_log",
                args=[self.operational_entry.pk],
            )
        )
        self.assertEqual(source_response.status_code, 200)
        self.assertContains(
            source_response,
            f"Запись № {self.operational_entry.sequence_number}",
        )

        print_response = self.client.get(
            reverse("equipment_defects:print"),
            {"volume": record.equipment_defect_context.volume.public_id},
        )
        self.assertEqual(print_response.status_code, 200)
        print_html = print_response.content.decode("utf-8")
        print_positions = [print_html.index(column) for column in APPROVED_PRINT_COLUMNS]
        self.assertEqual(print_positions, sorted(print_positions))
        self.assertNotIn("SHA-256 формы", print_html)
        self.assertNotIn(record.registration_number, print_html)
        self.assertIn("print-signature-line", print_html)

    def test_presentation_seed_is_idempotent_and_has_all_five_examples(self) -> None:
        call_command("seed_equipment_defects", verbosity=0)
        first_ids = set(
            EquipmentDefectContext.objects.exclude(presentation_key__isnull=True)
            .values_list("record_id", flat=True)
        )
        call_command("seed_equipment_defects", verbosity=0)
        second_ids = set(
            EquipmentDefectContext.objects.exclude(presentation_key__isnull=True)
            .values_list("record_id", flat=True)
        )

        self.assertEqual(first_ids, second_ids)
        self.assertEqual(len(first_ids), 5)
        states = set(
            OperationalDocumentRecord.objects.filter(pk__in=first_ids).values_list(
                "status_code",
                flat=True,
            )
        )
        self.assertEqual(
            states,
            {STATUS_REGISTERED, STATUS_IN_PROGRESS, STATUS_RESOLVED, STATUS_CLOSED},
        )
        self.assertTrue(
            EquipmentDefectActionEvidence.objects.filter(
                record_id__in=first_ids,
                action_code=DefectActionCode.DEADLINE_EXTENDED,
            ).exists()
        )


class EquipmentDefectNumberingConcurrencyTests(
    DefectFixtureMixin,
    TransactionTestCase,
):
    reset_sequences = True

    def setUp(self) -> None:
        self.fixture = self.create_organization_fixture("concurrency")
        self.operator = self.create_employee(
            fixture=self.fixture,
            username="concurrent.operator",
            personnel_number="CON-001",
            last_name="Параллельный",
            position_key="operational_position",
        )
        self.discoverer = self.create_employee(
            fixture=self.fixture,
            username="concurrent.discoverer",
            personnel_number="CON-002",
            last_name="Обнаруживший",
            position_key="responsible_position",
        )
        ensure_defect_document_type(self.operator)

    @skipUnlessDBFeature("has_select_for_update")
    def test_numbering_is_unique_under_concurrent_registration(self) -> None:
        organization_id = self.fixture["organization"].pk
        workplace_id = self.fixture["workplace"].pk
        equipment_id = self.fixture["equipment"].pk
        operator_id = self.operator.pk
        discoverer_id = self.discoverer.pk

        def create_one(index: int) -> tuple[int, str]:
            close_old_connections()
            try:
                record = register_defect(
                    actor=Employee.objects.get(pk=operator_id),
                    workplace=Workplace.objects.get(pk=workplace_id),
                    equipment=EquipmentAsset.objects.get(pk=equipment_id),
                    discovered_by=Employee.objects.get(pk=discoverer_id),
                    detected_at=timezone.now() - timedelta(minutes=index + 1),
                    defect_description=f"Параллельно зарегистрированный дефект {index}.",
                )
                return record.sequence_value, record.registration_number
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=4) as executor:
            results = list(executor.map(create_one, range(4)))

        self.assertEqual(len({value for value, _number in results}), 4)
        self.assertEqual(len({number for _value, number in results}), 4)
        self.assertEqual(
            OperationalDocumentRecord.objects.filter(
                organization_id=organization_id,
                document_type__code=DOCUMENT_TYPE_CODE,
            ).count(),
            4,
        )
