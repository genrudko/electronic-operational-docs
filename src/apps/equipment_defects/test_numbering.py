from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from django.db import close_old_connections
from django.test import TransactionTestCase, skipUnlessDBFeature
from django.utils import timezone

from apps.equipment.models import EquipmentAsset
from apps.operational_documents.models import OperationalDocumentRecord
from apps.organizations.models import Employee, Workplace

from .constants import DOCUMENT_TYPE_CODE
from .services import ensure_defect_document_type, register_defect
from .test_support import DefectFixtureMixin


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
