from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.imports.models import (
    DataProfile,
    PersonnelAuthorityCell,
    PersonnelSourceRevision,
    PersonnelSourceRow,
)
from apps.imports.personnel import (
    build_personnel_publication_preview,
    parse_personnel_workbook,
    publish_personnel_revision,
    stage_personnel_workbook,
)
from apps.organizations.models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    OperationalRightDefinition,
    Organization,
    Position,
    Role,
    RoleAssignment,
)
from tests.credential_fixtures import ephemeral_credential

from .personnel_workbook import synthetic_personnel_workbook


@override_settings(EOD_DATABASE_PROFILE="development")
class PersonnelOperationalAuthorityImporterTests(TestCase):
    def setUp(self):
        self.credential = ephemeral_credential("PersonnelAuthority")
        self.organization = Organization.objects.create(
            code="PERS-ORG",
            name="Синтетическая организация персонала",
        )
        division = Division.objects.create(
            organization=self.organization,
            code="PERS-ADMIN",
            name="Административное подразделение",
        )
        position = Position.objects.create(
            organization=self.organization,
            code="PERS-PUBLISHER",
            name="Администратор справочников",
        )
        self.user = get_user_model().objects.create_user(
            username="personnel-publisher",
            password=self.credential,
        )
        self.publisher = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            user=self.user,
            personnel_number="PERS-001",
            last_name="Тестов",
            first_name="Публикатор",
            employment_start=date(2026, 1, 1),
        )
        role, _created = Role.objects.get_or_create(
            code="organization_admin",
            defaults={
                "name": "Администратор справочников",
                "description": "Контролируемая публикация справочников.",
                "is_system": True,
            },
        )
        RoleAssignment.objects.create(
            employee=self.publisher,
            role=role,
            valid_from=date(2026, 1, 1),
        )
        DataProfile.ensure_for_organization(self.organization)
        self.local_profile = DataProfile.objects.get(
            organization=self.organization,
            code="local-validation",
        )

    def upload(self, name: str = "synthetic-personnel.xlsx") -> SimpleUploadedFile:
        return SimpleUploadedFile(
            name,
            synthetic_personnel_workbook(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    def stage(self):
        return stage_personnel_workbook(
            uploaded_file=self.upload(),
            employee=self.publisher,
            data_profile=self.local_profile,
            source_reference="Синтетическая матрица Patch 011.6.1",
            effective_from=date(2026, 7, 22),
        )

    def test_parser_preserves_marker_semantics_and_ambiguities(self):
        parsed = parse_personnel_workbook(synthetic_personnel_workbook())
        self.assertEqual(parsed.layout_version, PersonnelSourceRevision.LayoutVersion.CURRENT_28_COLUMNS)
        self.assertEqual(len(parsed.rows), 2)
        self.assertEqual(parsed.manifest["authority_definition_count"], 21)
        self.assertEqual(parsed.manifest["authority_cell_count"], 42)
        first = parsed.rows[0]
        by_code = {cell.right_code: cell for cell in first.authority_cells}
        self.assertEqual(
            by_code["dispatch_application_submit"].grant_state,
            PersonnelAuthorityCell.GrantState.GRANTED,
        )
        self.assertEqual(
            by_code["dispatch_application_approve"].grant_state,
            PersonnelAuthorityCell.GrantState.NOT_GRANTED,
        )
        self.assertEqual(
            by_code["operational_application_submit"].grant_state,
            PersonnelAuthorityCell.GrantState.QUALIFIED,
        )
        self.assertEqual(by_code["operational_application_submit"].footnote_numbers, (2,))
        self.assertEqual(
            by_code["operational_application_approve"].grant_state,
            PersonnelAuthorityCell.GrantState.AMBIGUOUS,
        )
        self.assertEqual(
            by_code["rza_maintenance_category"].grant_state,
            PersonnelAuthorityCell.GrantState.AMBIGUOUS,
        )

    def test_same_file_is_idempotent_and_source_bytes_are_not_stored(self):
        first = self.stage()
        second = self.stage()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(PersonnelSourceRevision.objects.count(), 1)
        self.assertEqual(first.total_people, 2)
        self.assertEqual(first.total_authority_cells, 42)
        field_names = {field.name for field in PersonnelSourceRevision._meta.fields}
        self.assertNotIn("source_file", field_names)
        self.assertNotIn("source_bytes", field_names)

    def test_presentation_database_blocks_real_personnel_staging(self):
        with override_settings(EOD_DATABASE_PROFILE="presentation"):
            with self.assertRaises(PermissionDenied):
                self.stage()
        self.assertEqual(PersonnelSourceRevision.objects.count(), 0)

    def test_publication_creates_only_positive_unambiguous_rights(self):
        revision = self.stage()
        preview = build_personnel_publication_preview(revision)
        publication = publish_personnel_revision(
            revision=revision,
            actor=self.publisher,
            user=self.user,
            password=self.credential,
            expected_digest=preview.digest,
        )
        revision.refresh_from_db()
        self.assertEqual(revision.status, PersonnelSourceRevision.Status.PARTIALLY_PUBLISHED)
        self.assertEqual(publication.digest, preview.digest)
        self.assertEqual(Employee.objects.filter(organization=self.organization).count(), 3)
        self.assertEqual(EmployeeQualification.objects.count(), 2)
        grants = EmployeeOperationalRight.objects.select_related("right_definition")
        self.assertGreater(grants.count(), 0)
        self.assertFalse(grants.filter(right_definition__code="rza_maintenance_category").exists())
        self.assertFalse(grants.filter(source_marker="–").exists())
        self.assertEqual(publication.result_summary["withdrawals_automatically_applied"], 0)
        self.assertGreater(publication.result_summary["ambiguous_cells_not_published"], 0)

    def test_unicode_matching_reuses_existing_cyrillic_employee(self):
        division = Division.objects.create(
            organization=self.organization,
            code="OPS-DIV",
            name="оперативная служба",
        )
        position = Position.objects.create(
            organization=self.organization,
            code="OPS-POS",
            name="начальник смены",
        )
        existing = Employee.objects.create(
            organization=self.organization,
            division=division,
            position=position,
            personnel_number="OPS-001",
            last_name="ИВАНОВ",
            first_name="Иван",
            middle_name="Иванович",
            employment_start=date(2026, 1, 1),
        )
        revision = self.stage()
        first_row = revision.person_rows.get(source_sequence=1)
        self.assertEqual(first_row.matched_employee, existing)
        preview = build_personnel_publication_preview(revision)
        publication = publish_personnel_revision(
            revision=revision,
            actor=self.publisher,
            user=self.user,
            password=self.credential,
            expected_digest=preview.digest,
        )
        self.assertEqual(publication.result_summary["reused_people"], 1)
        first_row.refresh_from_db()
        self.assertEqual(first_row.published_employee_id, existing.pk)
        self.assertEqual(Employee.objects.filter(organization=self.organization).count(), 3)

    def test_preview_excludes_unresolved_identity_and_missing_division(self):
        revision = self.stage()
        first = revision.person_rows.get(source_sequence=1)
        first.match_kind = PersonnelSourceRow.MatchKind.REVIEW_REQUIRED
        first.review_status = PersonnelSourceRow.ReviewStatus.REVIEW_REQUIRED
        first.save(update_fields=("match_kind", "review_status"))
        second = revision.person_rows.get(source_sequence=2)
        second.division_raw = ""
        second.review_status = PersonnelSourceRow.ReviewStatus.REVIEW_REQUIRED
        second.save(update_fields=("division_raw", "review_status"))

        preview = build_personnel_publication_preview(revision)

        self.assertEqual(preview.summary["selected_people"], 0)
        self.assertEqual(preview.rows, ())

    def test_views_show_staging_publication_and_searchable_employee_card(self):
        self.client.force_login(self.user)
        upload_response = self.client.post(
            reverse("imports:personnel_upload"),
            {
                "data_profile": self.local_profile.pk,
                "source_reference": "Синтетическая матрица UI",
                "effective_from": "2026-07-22",
                "source_file": self.upload("ui-personnel.xlsx"),
            },
        )
        self.assertEqual(upload_response.status_code, 302)
        revision = PersonnelSourceRevision.objects.get(original_filename="ui-personnel.xlsx")
        detail = self.client.get(reverse("imports:personnel_detail", args=[revision.public_id]))
        self.assertContains(detail, "Иванов Иван Иванович")
        self.assertContains(detail, "Неоднозначные значения — не публикуются")
        preview = build_personnel_publication_preview(revision)
        publish_response = self.client.post(
            reverse("imports:personnel_publication", args=[revision.public_id]),
            {
                "preview_digest": preview.digest,
                "password": self.credential,
                "confirm": "on",
            },
        )
        self.assertEqual(publish_response.status_code, 302)
        employee = Employee.objects.get(last_name="Иванов", first_name="Иван")
        search = self.client.get(reverse("organizations:directory"), {"q": "переключений"})
        self.assertContains(search, employee.full_name)
        card = self.client.get(reverse("organizations:employee_detail", args=[employee.public_id]))
        self.assertContains(card, "Только положительные действующие назначения")
        self.assertContains(card, "Производство переключений")

    def test_right_dictionary_contains_all_21_source_columns(self):
        self.assertEqual(OperationalRightDefinition.objects.filter(is_active=True).count(), 21)
