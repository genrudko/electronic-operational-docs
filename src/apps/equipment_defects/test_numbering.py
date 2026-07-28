from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from django.db import close_old_connections
from django.test import TestCase, TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone

from apps.equipment.models import EquipmentAsset
from apps.operational_documents.models import (
    FieldType,
    OperationalDocumentNumberSequence,
    OperationalDocumentRecord,
    OperationalDocumentTypeRevision,
)
from apps.operational_documents.services import (
    create_and_publish_type,
    create_record,
    current_published_revision,
)
from apps.organizations.models import Employee, Workplace

from .constants import DOCUMENT_TYPE_CODE, NUMBER_PREFIX, NUMBER_WIDTH
from .services import ensure_defect_document_type, register_defect
from .test_support import DefectFixtureMixin

MOSCOW_TIME_ZONE = ZoneInfo("Europe/Moscow")
FIXED_EVENT_AT = datetime(2025, 6, 1, 12, 0, tzinfo=MOSCOW_TIME_ZONE)
GENERIC_FIELD_DEFINITIONS = [
    {
        "code": "NOTE",
        "label": "Примечание",
        "type": FieldType.TEXT,
        "required": True,
        "show_in_list": True,
        "searchable": True,
        "help_text": "",
        "choices": [],
    }
]


def create_same_prefix_revision(
    *,
    actor: Employee,
    code: str,
) -> OperationalDocumentTypeRevision:
    document_type = create_and_publish_type(
        actor=actor,
        code=code,
        name=f"Тестовый тип {code}",
        short_name=f"Тип {code}",
        description="Проверка организационно уникальной нумерации.",
        number_prefix=NUMBER_PREFIX,
        number_width=NUMBER_WIDTH,
        requires_workplace=True,
        field_definitions=GENERIC_FIELD_DEFINITIONS,
    )
    revision = current_published_revision(document_type)
    if revision is None:
        raise AssertionError("Тестовая редакция типа не опубликована.")
    return revision


def create_generic_record(
    *,
    revision: OperationalDocumentTypeRevision,
    actor: Employee,
    workplace: Workplace,
    event_at: datetime,
    note: str,
) -> OperationalDocumentRecord:
    return create_record(
        revision=revision,
        actor=actor,
        title=note,
        summary=note,
        event_at=event_at,
        workplace=workplace,
        field_values={"NOTE": note},
        participant_map={},
    )


class EquipmentDefectNumberCollisionTests(DefectFixtureMixin, TestCase):
    def setUp(self) -> None:
        self.fixture = self.create_organization_fixture("collision")
        self.operator = self.create_employee(
            fixture=self.fixture,
            username="collision.operator",
            personnel_number="COL-001",
            last_name="Коллизионный",
            position_key="operational_position",
        )
        self.discoverer = self.create_employee(
            fixture=self.fixture,
            username="collision.discoverer",
            personnel_number="COL-002",
            last_name="Обнаруживший",
            position_key="responsible_position",
        )

    def test_defect_skips_number_occupied_by_other_type_with_same_prefix(self) -> None:
        other_revision = create_same_prefix_revision(
            actor=self.operator,
            code="same-prefix-existing",
        )
        occupied = create_generic_record(
            revision=other_revision,
            actor=self.operator,
            workplace=self.fixture["workplace"],
            event_at=FIXED_EVENT_AT,
            note="Занимает первый кандидат регистрационного номера.",
        )

        defect = register_defect(
            actor=self.operator,
            workplace=self.fixture["workplace"],
            equipment=self.fixture["equipment"],
            discovered_by=self.discoverer,
            detected_at=FIXED_EVENT_AT + timedelta(minutes=1),
            defect_description="Дефект после организационной коллизии номера.",
        )

        self.assertNotEqual(occupied.document_type_id, defect.document_type_id)
        self.assertEqual(occupied.registration_number, "ДЕФ-2025-0001")
        self.assertEqual(defect.registration_number, "ДЕФ-2025-0002")
        self.assertEqual(defect.sequence_value, 2)
        self.assertEqual(
            OperationalDocumentNumberSequence.objects.get(
                document_type=defect.document_type,
                year=2025,
            ).last_value,
            2,
        )
        self.assertEqual(
            OperationalDocumentRecord.objects.filter(
                organization=self.fixture["organization"],
                registration_number__in={
                    occupied.registration_number,
                    defect.registration_number,
                },
            ).count(),
            2,
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

    @skipUnlessDBFeature("has_select_for_update")
    def test_same_prefix_types_are_serialized_within_organization(self) -> None:
        first_revision = create_same_prefix_revision(
            actor=self.operator,
            code="parallel-prefix-a",
        )
        second_revision = create_same_prefix_revision(
            actor=self.operator,
            code="parallel-prefix-b",
        )
        revision_ids = (first_revision.pk, second_revision.pk)
        organization_id = self.fixture["organization"].pk
        workplace_id = self.fixture["workplace"].pk
        operator_id = self.operator.pk

        def create_one(index: int) -> tuple[int, int, str]:
            close_old_connections()
            try:
                revision = OperationalDocumentTypeRevision.objects.get(
                    pk=revision_ids[index % 2]
                )
                record = create_generic_record(
                    revision=revision,
                    actor=Employee.objects.get(pk=operator_id),
                    workplace=Workplace.objects.get(pk=workplace_id),
                    event_at=FIXED_EVENT_AT + timedelta(minutes=index),
                    note=f"Параллельная запись общего allocator {index}.",
                )
                return record.document_type_id, record.sequence_value, record.registration_number
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=6) as executor:
            results = list(executor.map(create_one, range(6)))

        registration_numbers = {number for _type_id, _value, number in results}
        self.assertEqual(len(registration_numbers), 6)
        self.assertEqual(
            {int(number.rsplit("-", maxsplit=1)[1]) for number in registration_numbers},
            set(range(1, 7)),
        )
        self.assertEqual(
            OperationalDocumentRecord.objects.filter(
                organization_id=organization_id,
                document_type_id__in={
                    first_revision.document_type_id,
                    second_revision.document_type_id,
                },
            ).count(),
            6,
        )
        for document_type_id in {
            first_revision.document_type_id,
            second_revision.document_type_id,
        }:
            issued_values = [
                value
                for result_type_id, value, _number in results
                if result_type_id == document_type_id
            ]
            sequence = OperationalDocumentNumberSequence.objects.get(
                document_type_id=document_type_id,
                year=2025,
            )
            self.assertEqual(sequence.last_value, max(issued_values))
