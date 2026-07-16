from datetime import date

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.equipment.models import EquipmentAsset
from apps.imports.models import ImportBatch
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
)


class ImportViewTests(TestCase):
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
        self.user = user_model.objects.create_user(username="import-view", password="test")
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            user=self.user,
            personnel_number="VIEW-1",
            last_name="Тестов",
            first_name="Просмотр",
            employment_start=date(2026, 1, 1),
        )

    def post_upload(self):
        return self.client.post(
            reverse("imports:upload"),
            {
                "target_registry": ImportBatch.TargetRegistry.EQUIPMENT,
                "source_file": SimpleUploadedFile(
                    "equipment.csv",
                    "Код;Наименование\nEQ-1;КТП\n".encode(),
                ),
            },
        )

    def test_import_list_requires_login(self):
        response = self.client.get(reverse("imports:list"))
        self.assertEqual(response.status_code, 302)

    def test_upload_creates_preview_without_changing_equipment(self):
        self.client.force_login(self.user)
        before = EquipmentAsset.objects.count()
        response = self.post_upload()
        self.assertEqual(response.status_code, 302)
        batch = ImportBatch.objects.get()
        self.assertEqual(batch.status, ImportBatch.Status.READY)
        self.assertEqual(EquipmentAsset.objects.count(), before)
        detail = self.client.get(reverse("imports:detail", args=[batch.public_id]))
        self.assertContains(detail, "Это только предварительный просмотр")
        self.assertContains(detail, "ИСХОДНЫЕ ЗНАЧЕНИЯ")
        self.assertContains(detail, "Нормализованные значения строки")
        self.assertContains(detail, "Технические реквизиты файла")
        self.assertContains(detail, "EQ-1")

    def test_batch_from_other_organization_is_hidden(self):
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
        other_employee = Employee.objects.create(
            organization=other,
            division=division,
            position=position,
            personnel_number="OTHER-1",
            last_name="Другой",
            first_name="Сотрудник",
            employment_start=date(2026, 1, 1),
        )
        batch = ImportBatch.objects.create(
            organization=other,
            created_by=other_employee,
            target_registry=ImportBatch.TargetRegistry.OTHER,
            original_filename="other.csv",
            source_format=ImportBatch.SourceFormat.CSV,
            file_size=1,
            file_sha256="d" * 64,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("imports:detail", args=[batch.public_id]))
        self.assertEqual(response.status_code, 404)

    def test_discard_endpoint_keeps_auditable_batch(self):
        self.client.force_login(self.user)
        self.post_upload()
        batch = ImportBatch.objects.get()
        response = self.client.post(reverse("imports:discard", args=[batch.public_id]))
        self.assertRedirects(
            response,
            reverse("imports:detail", args=[batch.public_id]),
        )
        batch.refresh_from_db()
        self.assertEqual(batch.status, ImportBatch.Status.DISCARDED)
        self.assertGreater(batch.rows.count(), 0)
