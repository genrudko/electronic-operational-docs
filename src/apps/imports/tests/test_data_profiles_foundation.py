from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.imports.domain_glossary import (
    glossary_by_code_name,
    validate_technical_english_glossary,
)
from apps.imports.models import (
    DataProfile,
    ImportBatch,
    ImportColumn,
    ImportMappingTemplate,
)
from apps.imports.services import create_import_batch, save_column_mapping
from apps.organizations.models import Division, Employee, Organization, Position
from tests.credential_fixtures import ephemeral_credential


class DataProfilesImportFoundationTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organization = Organization.objects.create(code="ORG-PROFILES", name="Организация")
        division = Division.objects.create(
            organization=self.organization,
            code="DIV-PROFILES",
            name="Подразделение",
        )
        position = Position.objects.create(
            organization=self.organization,
            code="POS-PROFILES",
            name="Специалист",
        )
        self.user = user_model.objects.create_user(
            username="profile-importer",
            password=ephemeral_credential("DataProfileImporter"),
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            user=self.user,
            personnel_number="PROFILE-1",
            last_name="Тестов",
            first_name="Профиль",
            employment_start=date(2026, 1, 1),
        )

    def _upload(self, filename: str = "equipment.csv", row: str = "EQ-1;КТП;КТП;КВЭС\n"):
        return SimpleUploadedFile(
            filename,
            ("Код;Наименование;Тип;Энергообъект\n" + row).encode("utf-8"),
        )

    def test_default_profiles_are_created_with_safe_policies(self):
        batch = ImportBatch.objects.create(
            organization=self.organization,
            created_by=self.employee,
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            original_filename="equipment.csv",
            source_format=ImportBatch.SourceFormat.CSV,
            file_size=10,
            file_sha256="a" * 64,
        )
        profiles = DataProfile.objects.filter(organization=self.organization)
        self.assertEqual(profiles.count(), 3)
        presentation = profiles.get(code="presentation-safe")
        local = profiles.get(code="local-validation")
        automated = profiles.get(code="automated-tests")
        self.assertEqual(batch.data_profile, presentation)
        self.assertTrue(presentation.is_default)
        self.assertEqual(presentation.export_policy, DataProfile.ExportPolicy.ALLOWED)
        self.assertFalse(presentation.allows_real_personal_data)
        self.assertEqual(local.export_policy, DataProfile.ExportPolicy.PROHIBITED)
        self.assertTrue(local.allows_real_personal_data)
        self.assertEqual(automated.sensitivity_level, DataProfile.SensitivityLevel.SYNTHETIC)

    def test_presentation_profile_rejects_real_personal_data(self):
        profile = DataProfile(
            organization=self.organization,
            code="unsafe-presentation",
            name="Небезопасная презентация",
            kind=DataProfile.Kind.PRESENTATION_SAFE,
            sensitivity_level=DataProfile.SensitivityLevel.PERSONAL_INTERNAL,
            export_policy=DataProfile.ExportPolicy.ALLOWED,
            allows_real_personal_data=True,
        )
        with self.assertRaises(ValidationError):
            profile.full_clean()

    def test_upload_records_local_profile_and_source_reference(self):
        profiles = DataProfile.ensure_for_organization(self.organization)
        local = next(profile for profile in profiles if profile.code == "local-validation")
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("imports:upload"),
            {
                "data_profile": local.pk,
                "target_registry": ImportBatch.TargetRegistry.EQUIPMENT,
                "source_reference": "Перечень объектов диспетчеризации Кочубеевской ВЭС",
                "source_file": self._upload(),
            },
        )
        self.assertEqual(response.status_code, 302)
        batch = ImportBatch.objects.get()
        self.assertEqual(batch.data_profile, local)
        self.assertEqual(
            batch.source_reference,
            "Перечень объектов диспетчеризации Кочубеевской ВЭС",
        )
        detail = self.client.get(reverse("imports:detail", args=[batch.public_id]))
        self.assertContains(detail, "Локальная проверочная база")
        self.assertContains(detail, "Обычный экспорт запрещён")
        self.assertContains(detail, batch.source_reference)

    def test_profile_page_explains_all_three_contours(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("imports:data_profiles"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Безопасная презентационная база")
        self.assertContains(response, "Локальная проверочная база")
        self.assertContains(response, "Автоматизированные тесты")
        self.assertContains(response, "Профиль является частью происхождения данных")

    def test_mapping_template_is_saved_and_reused_for_same_headers(self):
        first = create_import_batch(
            uploaded_file=self._upload(),
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            employee=self.employee,
        )
        mapping = {
            1: "code",
            2: "technical_name",
            3: "type",
            4: "site",
        }
        save_column_mapping(batch=first, employee=self.employee, mapping=mapping)
        template = ImportMappingTemplate.objects.get(organization=self.organization)
        self.assertEqual(template.mapping, {str(key): value for key, value in mapping.items()})
        self.assertEqual(template.header_signature, first.header_signature)

        second = create_import_batch(
            uploaded_file=self._upload(filename="equipment-next.csv", row="EQ-2;КТП-2;КТП;КВЭС\n"),
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            employee=self.employee,
        )
        second.refresh_from_db()
        template.refresh_from_db()
        self.assertEqual(second.applied_mapping_template, template)
        self.assertEqual(template.usage_count, 1)
        self.assertIsNotNone(template.last_used_at)
        self.assertEqual(
            {column.position: column.mapped_key for column in second.columns.all()},
            mapping,
        )
        self.assertTrue(
            all(
                column.mapping_origin == ImportColumn.MappingOrigin.TEMPLATE
                for column in second.columns.all()
            )
        )

    def test_technical_english_glossary_is_unique_and_power_system_specific(self):
        self.assertEqual(validate_technical_english_glossary(), ())
        glossary = glossary_by_code_name()
        self.assertEqual(glossary["circuit_breaker"].english_term, "circuit breaker")
        self.assertEqual(glossary["disconnector"].english_term, "disconnector")
        self.assertEqual(glossary["earthing_switch"].english_term, "earthing switch")
        self.assertEqual(
            glossary["operational_jurisdiction"].russian_term,
            "оперативное ведение",
        )
