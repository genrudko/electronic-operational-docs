from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.imports.models import ImportBatch, ImportRow
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
)


class ImportModelTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organization = Organization.objects.create(code="ORG-A", name="Организация А")
        division = Division.objects.create(
            organization=self.organization,
            code="DIV-A",
            name="Подразделение А",
        )
        position = Position.objects.create(
            organization=self.organization,
            code="POS-A",
            name="Специалист",
        )
        self.user = user_model.objects.create_user(username="importer-a")
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            user=self.user,
            personnel_number="A-1",
            last_name="Тестов",
            first_name="Импорт",
            employment_start=date(2026, 1, 1),
        )

    def _batch(self):
        return ImportBatch.objects.create(
            organization=self.organization,
            created_by=self.employee,
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            original_filename="equipment.csv",
            source_format=ImportBatch.SourceFormat.CSV,
            file_size=10,
            file_sha256="a" * 64,
        )

    def test_batch_rejects_employee_from_other_organization(self):
        other = Organization.objects.create(code="ORG-B", name="Организация Б")
        division = Division.objects.create(
            organization=other,
            code="DIV-B",
            name="Подразделение Б",
        )
        position = Position.objects.create(
            organization=other,
            code="POS-B",
            name="Специалист",
        )
        employee = Employee.objects.create(
            organization=other,
            division=division,
            position=position,
            personnel_number="B-1",
            last_name="Другой",
            first_name="Сотрудник",
            employment_start=date(2026, 1, 1),
        )
        batch = ImportBatch(
            organization=self.organization,
            created_by=employee,
            target_registry=ImportBatch.TargetRegistry.OTHER,
            original_filename="other.csv",
            source_format=ImportBatch.SourceFormat.CSV,
            file_size=1,
            file_sha256="b" * 64,
        )
        with self.assertRaises(ValidationError):
            batch.full_clean()

    def test_batch_physical_delete_is_blocked(self):
        batch = self._batch()
        with self.assertRaises(ValidationError):
            batch.delete()

    def test_import_row_requires_list_payloads(self):
        batch = self._batch()
        row = ImportRow(
            batch=batch,
            row_number=2,
            source_values={"bad": "shape"},
            normalized_values=[],
            status=ImportRow.Status.NEW,
            fingerprint="c" * 64,
        )
        with self.assertRaises(ValidationError):
            row.full_clean()
