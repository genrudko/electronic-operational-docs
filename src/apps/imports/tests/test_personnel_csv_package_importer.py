from __future__ import annotations

import io
import zipfile
from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.imports.forms import PersonnelWorkbookUploadForm
from apps.imports.models import DataProfile, PersonnelAuthorityCell, PersonnelSourceRevision
from apps.imports.personnel import (
    PersonnelWorkbookError,
    parse_personnel_csv_package,
    stage_personnel_workbook,
)
from apps.imports.tests.personnel_csv_package import (
    synthetic_personnel_csv_files,
    synthetic_personnel_csv_package,
)
from apps.organizations.models import Division, Employee, Organization, Position


@override_settings(EOD_DATABASE_PROFILE="development")
class PersonnelCsvPackageImporterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        organization = Organization.objects.create(
            code="CSV-PACKAGE-TEST",
            name="Синтетическая организация CSV-пакета",
        )
        division = Division.objects.create(
            organization=organization,
            code="CSV-IMPORT",
            name="Подразделение синтетического импорта",
        )
        position = Position.objects.create(
            organization=organization,
            code="CSV-IMPORTER",
            name="Оператор синтетического импорта",
        )
        cls.user = get_user_model().objects.create_user(
            username="csv-package-importer",
            password="CsvPackage-0116a-Test!",
        )
        cls.employee = Employee.objects.create(
            organization=organization,
            division=division,
            position=position,
            user=cls.user,
            personnel_number="CSV-001",
            last_name="Тестов",
            first_name="Импортёр",
            employment_start=date(2026, 1, 1),
        )
        DataProfile.ensure_for_organization(organization)
        cls.profile = DataProfile.objects.get(
            organization=organization,
            code="local-validation",
        )

    def upload(self, data: bytes | None = None, name: str = "personnel-normalized.zip"):
        return SimpleUploadedFile(
            name,
            data or synthetic_personnel_csv_package(),
            content_type="application/zip",
        )

    def stage(self, data: bytes | None = None, name: str = "personnel-normalized.zip"):
        return stage_personnel_workbook(
            uploaded_file=self.upload(data, name),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетический нормализованный CSV-пакет",
            effective_from=date(2026, 7, 23),
        )

    def test_parser_accepts_required_package_and_maps_all_21_authorities(self):
        files = synthetic_personnel_csv_files()
        for name, content in files.items():
            self.assertNotEqual(content.splitlines()[0].split(b",")[0], b"index", name)
        parsed = parse_personnel_csv_package(synthetic_personnel_csv_package(files=files))
        self.assertEqual(parsed.manifest["source_format"], "NORMALIZED_CSV_PACKAGE")
        self.assertEqual(parsed.manifest["person_count"], 2)
        self.assertEqual(parsed.manifest["position_count"], 2)
        self.assertEqual(parsed.manifest["authority_definition_count"], 21)
        self.assertEqual(parsed.manifest["authority_cell_count"], 42)
        self.assertEqual(len(parsed.rows[0].authority_cells), 21)

    def test_parser_preserves_dash_qualifier_unknown_reference_and_rza_quarantine(self):
        parsed = parse_personnel_csv_package(synthetic_personnel_csv_package())
        cells = {cell.right_code: cell for cell in parsed.rows[0].authority_cells}
        self.assertEqual(
            cells["dispatch_application_approve"].grant_state,
            PersonnelAuthorityCell.GrantState.NOT_GRANTED,
        )
        self.assertEqual(
            cells["operational_application_submit"].grant_state,
            PersonnelAuthorityCell.GrantState.QUALIFIED,
        )
        self.assertEqual(cells["operational_application_submit"].footnote_numbers, (2,))
        self.assertEqual(
            cells["operational_application_approve"].grant_state,
            PersonnelAuthorityCell.GrantState.AMBIGUOUS,
        )
        self.assertEqual(
            cells["rza_maintenance_category"].grant_state,
            PersonnelAuthorityCell.GrantState.AMBIGUOUS,
        )
        self.assertFalse(cells["rza_maintenance_category"].is_publishable)

    def test_package_may_be_inside_one_common_directory_and_workplace_csv_is_ignored(self):
        files = synthetic_personnel_csv_files()
        files["eod_workplace_document_register.csv"] = b"placeholder\n"
        parsed = parse_personnel_csv_package(
            synthetic_personnel_csv_package(files=files, prefix="chat-2/")
        )
        self.assertEqual(
            parsed.manifest["ignored_components"], ["eod_workplace_document_register.csv"]
        )

    def test_missing_required_component_is_rejected(self):
        files = synthetic_personnel_csv_files()
        files.pop("eod_people.csv")
        with self.assertRaisesMessage(PersonnelWorkbookError, "отсутствуют обязательные файлы"):
            parse_personnel_csv_package(synthetic_personnel_csv_package(files=files))

    def test_path_traversal_and_unknown_files_are_rejected(self):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            archive.writestr("../eod_people.csv", b"x")
        with self.assertRaisesMessage(PersonnelWorkbookError, "недопустимый путь"):
            parse_personnel_csv_package(buffer.getvalue())
        files = synthetic_personnel_csv_files()
        files["unexpected.csv"] = b"x\n"
        with self.assertRaisesMessage(PersonnelWorkbookError, "Неожиданный файл"):
            parse_personnel_csv_package(synthetic_personnel_csv_package(files=files))

    def test_wrong_header_and_non_utf8_are_rejected(self):
        files = synthetic_personnel_csv_files()
        files["eod_positions.csv"] = b"wrong,header\n1,2\n"
        with self.assertRaisesMessage(PersonnelWorkbookError, "CSV-контракту"):
            parse_personnel_csv_package(synthetic_personnel_csv_package(files=files))
        files = synthetic_personnel_csv_files()
        files["eod_people.csv"] = "ФИО".encode("cp1251")
        with self.assertRaisesMessage(PersonnelWorkbookError, "кодировка UTF-8"):
            parse_personnel_csv_package(synthetic_personnel_csv_package(files=files))

    def test_duplicate_assignment_and_mismatched_source_cell_are_rejected(self):
        files = synthetic_personnel_csv_files()
        text = files["eod_person_authority_assignments.csv"].decode("utf-8")
        files["eod_person_authority_assignments.csv"] = (text + text.splitlines()[1] + "\n").encode()
        with self.assertRaisesMessage(PersonnelWorkbookError, "повторяется назначение"):
            parse_personnel_csv_package(synthetic_personnel_csv_package(files=files))
        files = synthetic_personnel_csv_files()
        text = files["eod_person_authority_assignments.csv"].decode("utf-8")
        files["eod_person_authority_assignments.csv"] = text.replace("G9", "H9", 1).encode()
        with self.assertRaisesMessage(PersonnelWorkbookError, "не соответствует ожидаемой ячейке"):
            parse_personnel_csv_package(synthetic_personnel_csv_package(files=files))

    def test_form_accepts_zip_and_xlsx_but_rejects_loose_csv(self):
        zip_form = PersonnelWorkbookUploadForm(
            data={
                "data_profile": self.profile.pk,
                "source_reference": "ZIP",
                "effective_from": "2026-07-23",
            },
            files={"source_file": self.upload()},
            organization=self.employee.organization,
        )
        self.assertTrue(zip_form.is_valid(), zip_form.errors)
        csv_form = PersonnelWorkbookUploadForm(
            data={
                "data_profile": self.profile.pk,
                "source_reference": "CSV",
                "effective_from": "2026-07-23",
            },
            files={
                "source_file": SimpleUploadedFile(
                    "eod_people.csv", b"x\n", content_type="text/csv"
                )
            },
            organization=self.employee.organization,
        )
        self.assertFalse(csv_form.is_valid())
        self.assertIn("ZIP-пакет", str(csv_form.errors))

    def test_staging_is_idempotent_and_does_not_store_archive_bytes(self):
        first = self.stage()
        second = self.stage()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.manifest["source_format"], "NORMALIZED_CSV_PACKAGE")
        self.assertEqual(first.total_people, 2)
        self.assertEqual(first.total_authority_cells, 42)
        self.assertEqual(first.manifest["source_issue_count"], 1)
        self.assertEqual(first.manifest["source_issue_severity_counts"], {"HIGH": 1})
        self.assertFalse(hasattr(first, "source_bytes"))

    def test_presentation_profile_blocks_csv_package(self):
        with override_settings(EOD_DATABASE_PROFILE="presentation"):
            with self.assertRaises(PermissionDenied):
                self.stage()
        self.assertFalse(PersonnelSourceRevision.objects.exists())

    def test_upload_view_accepts_zip_and_shows_package_provenance(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("imports:personnel_upload"),
            {
                "data_profile": self.profile.pk,
                "source_reference": "CSV package UI",
                "effective_from": "2026-07-23",
                "source_file": self.upload(name="chat-2-personnel.zip"),
            },
        )
        self.assertEqual(response.status_code, 302)
        revision = PersonnelSourceRevision.objects.get(original_filename="chat-2-personnel.zip")
        detail = self.client.get(reverse("imports:personnel_detail", args=[revision.public_id]))
        self.assertContains(detail, "нормализованный ZIP-пакет CSV")
        self.assertContains(detail, "eod_people.csv")
        self.assertContains(detail, "Проблем источника: 1")
