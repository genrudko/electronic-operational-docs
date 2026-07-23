from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.imports.forms import WorkplaceDocumentRegisterUploadForm
from apps.imports.models import (
    DataProfile,
    WorkplaceDocumentSourceRevision,
    WorkplaceDocumentSourceRow,
)
from apps.imports.tests.workplace_document_register_csv import (
    synthetic_workplace_document_csv,
    synthetic_workplace_document_rows,
)
from apps.imports.workplace_documents import (
    WORKPLACE_DOCUMENT_HEADER,
    WorkplaceDocumentRegisterError,
    build_workplace_document_publication_preview,
    decide_workplace_document_source_row,
    discard_workplace_document_revision,
    parse_workplace_document_register,
    publish_workplace_document_register,
    stage_workplace_document_register,
)
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Role,
    RoleAssignment,
    Workplace,
)
from apps.workplace_docs.models import (
    ElectronicStorageInterpretation,
    RevisionStatus,
    StorageForm,
    WorkplaceDocumentEntry,
)


@override_settings(EOD_DATABASE_PROFILE="development")
class WorkplaceDocumentRegisterImporterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.organization = Organization.objects.create(
            code="WORKDOC-IMPORT-TEST",
            name="Синтетическая организация реестра документации",
        )
        cls.division = Division.objects.create(
            organization=cls.organization,
            code="OPS",
            name="Оперативное подразделение",
        )
        cls.workplace = Workplace.objects.create(
            organization=cls.organization,
            division=cls.division,
            code="KOCH_CONTROL_ROOM",
            name="Главный щит управления Кочубеевской ВЭС",
        )
        cls.position = Position.objects.create(
            organization=cls.organization,
            code="SHIFT-SUPERVISOR",
            name="Начальник смены",
            is_operational=True,
        )
        cls.user = get_user_model().objects.create_user(
            username="workdoc-importer",
            password="Workdoc-01162-Test!",
        )
        cls.employee = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            workplace=cls.workplace,
            user=cls.user,
            personnel_number="WD-001",
            last_name="Тестов",
            first_name="Импортёр",
            employment_start=date(2026, 1, 1),
        )
        cls.role = Role.objects.create(
            code="organization_admin",
            name="Администратор справочников",
            is_system=True,
        )
        RoleAssignment.objects.create(
            employee=cls.employee,
            role=cls.role,
            valid_from=date(2026, 1, 1),
            is_active=True,
        )
        DataProfile.ensure_for_organization(cls.organization)
        cls.profile = DataProfile.objects.get(
            organization=cls.organization,
            code="local-validation",
        )

    def upload(self, data: bytes | None = None, name: str = "eod_workplace_document_register.csv"):
        return SimpleUploadedFile(
            name,
            data or synthetic_workplace_document_csv(),
            content_type="text/csv",
        )

    def stage(self, data: bytes | None = None):
        return stage_workplace_document_register(
            uploaded_file=self.upload(data),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетический перечень документации от 07.08.2024",
            effective_from=date(2026, 7, 23),
            list_review_period_months=12,
        )

    def test_parser_accepts_exact_header_utf8_bom_and_counts_sections(self):
        parsed = parse_workplace_document_register(synthetic_workplace_document_csv())
        self.assertEqual(len(parsed.rows), 2)
        self.assertEqual(parsed.manifest["section_count"], 1)
        self.assertEqual(parsed.manifest["electronic_indicated_count"], 1)
        self.assertEqual(parsed.encoding, "utf-8-sig")
        self.assertEqual(WORKPLACE_DOCUMENT_HEADER[0], "register_entry_no")
        self.assertNotIn("index", WORKPLACE_DOCUMENT_HEADER)
        self.assertEqual([row.source_index for row in parsed.rows], [0, 1])
        self.assertTrue(all(row.review_status == "READY" for row in parsed.rows))

    def test_electronic_marker_is_preserved_without_paper_waiver(self):
        parsed = parse_workplace_document_register(synthetic_workplace_document_csv())
        first, second = parsed.rows
        self.assertEqual(first.electronic_storage_mark, "+")
        self.assertEqual(first.electronic_storage_interpretation, "INDICATED")
        self.assertEqual(second.electronic_storage_interpretation, "NOT_INDICATED")
        self.assertNotEqual(second.electronic_storage_interpretation, "PROHIBITED")

    def test_wrong_header_non_utf8_and_marker_mismatch_are_rejected(self):
        with self.assertRaisesMessage(WorkplaceDocumentRegisterError, "Заголовок"):
            parse_workplace_document_register(b"wrong,header\n1,2\n")
        with self.assertRaisesMessage(WorkplaceDocumentRegisterError, "UTF-8"):
            parse_workplace_document_register("Перечень".encode("cp1251"))
        rows = synthetic_workplace_document_rows()
        rows[0]["electronic_storage_interpretation"] = "NOT_INDICATED"
        parsed = parse_workplace_document_register(
            synthetic_workplace_document_csv(rows=rows)
        )
        self.assertEqual(parsed.rows[0].review_status, "BLOCKED")

    def test_source_notes_duplicate_numbers_and_numbering_gaps_require_review(self):
        rows = synthetic_workplace_document_rows()
        rows[1]["source_document_no"] = "1"
        rows[1]["source_notes"] = "Проверить исходную нумерацию."
        parsed = parse_workplace_document_register(
            synthetic_workplace_document_csv(rows=rows)
        )
        self.assertTrue(
            all(row.review_status == "REVIEW_REQUIRED" for row in parsed.rows)
        )
        rows = synthetic_workplace_document_rows()
        rows[1]["source_document_no"] = "3"
        parsed = parse_workplace_document_register(
            synthetic_workplace_document_csv(rows=rows)
        )
        self.assertTrue(
            all(row.review_status == "REVIEW_REQUIRED" for row in parsed.rows)
        )

    def test_form_accepts_single_csv_and_rejects_zip(self):
        form = WorkplaceDocumentRegisterUploadForm(
            data={
                "data_profile": self.profile.pk,
                "target_workplace": self.workplace.pk,
                "source_reference": "Синтетический перечень",
                "effective_from": "2026-07-23",
                "list_review_period_months": 12,
            },
            files={"source_file": self.upload()},
            organization=self.organization,
        )
        self.assertTrue(form.is_valid(), form.errors)
        missing_workplace_form = WorkplaceDocumentRegisterUploadForm(
            data={
                "data_profile": self.profile.pk,
                "source_reference": "Без рабочего места",
                "effective_from": "2026-07-23",
                "list_review_period_months": 12,
            },
            files={"source_file": self.upload()},
            organization=self.organization,
        )
        self.assertFalse(missing_workplace_form.is_valid())
        self.assertIn("target_workplace", missing_workplace_form.errors)
        zip_form = WorkplaceDocumentRegisterUploadForm(
            data={
                "data_profile": self.profile.pk,
                "target_workplace": self.workplace.pk,
                "source_reference": "ZIP",
                "effective_from": "2026-07-23",
                "list_review_period_months": 12,
            },
            files={"source_file": self.upload(name="register.zip")},
            organization=self.organization,
        )
        self.assertFalse(zip_form.is_valid())

    def test_staging_matches_controlled_workplace_alias_and_does_not_store_source_bytes(self):
        revision = self.stage()
        self.assertEqual(revision.total_rows, 2)
        self.assertEqual(revision.ready_rows, 2)
        self.assertEqual(revision.review_rows, 0)
        self.assertEqual(revision.blocked_rows, 0)
        self.assertEqual(revision.matched_workplace, self.workplace)
        self.assertEqual(revision.manifest["workplace_match_kind"], "CONTROLLED_ALIAS")
        self.assertFalse(revision.manifest["source_bytes_persisted"])
        self.assertFalse(hasattr(revision, "source_bytes"))

    def test_explicit_workplace_selection_resolves_unknown_source_scope(self):
        rows = synthetic_workplace_document_rows()
        for row in rows:
            row["workplace_scope"] = "Общее рабочее место оперативного персонала"
        revision = stage_workplace_document_register(
            uploaded_file=self.upload(synthetic_workplace_document_csv(rows=rows)),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Синтетический перечень с ручным сопоставлением",
            effective_from=date(2026, 7, 23),
            list_review_period_months=12,
            target_workplace=self.workplace,
        )
        self.assertEqual(revision.matched_workplace, self.workplace)
        self.assertEqual(revision.manifest["workplace_match_kind"], "MANUAL_SELECTION")
        self.assertEqual(revision.manifest["automatic_workplace_match_kind"], "NOT_FOUND")
        self.assertEqual(revision.manifest["selected_workplace_code"], self.workplace.code)
        self.assertEqual(revision.ready_rows, 2)
        self.assertEqual(revision.blocked_rows, 0)

    def test_explicit_workplace_must_not_conflict_with_unambiguous_source_match(self):
        second_workplace = Workplace.objects.create(
            organization=self.organization,
            division=self.division,
            code="SECOND_CONTROL_ROOM",
            name="Резервное рабочее место",
        )
        with self.assertRaisesMessage(ValidationError, "противоречит"):
            stage_workplace_document_register(
                uploaded_file=self.upload(),
                employee=self.employee,
                data_profile=self.profile,
                source_reference="Конфликт ручного выбора",
                effective_from=date(2026, 7, 23),
                list_review_period_months=12,
                target_workplace=second_workplace,
            )

    def test_same_source_context_may_be_reloaded_for_another_explicit_workplace(self):
        rows = synthetic_workplace_document_rows()
        for row in rows:
            row["workplace_scope"] = "Общее рабочее место оперативного персонала"
        data = synthetic_workplace_document_csv(rows=rows)
        second_workplace = Workplace.objects.create(
            organization=self.organization,
            division=self.division,
            code="SECOND_CONTROL_ROOM",
            name="Резервное рабочее место",
        )
        first = stage_workplace_document_register(
            uploaded_file=self.upload(data),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Один источник для двух рабочих мест",
            effective_from=date(2026, 7, 23),
            list_review_period_months=12,
            target_workplace=self.workplace,
        )
        second = stage_workplace_document_register(
            uploaded_file=self.upload(data),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Один источник для двух рабочих мест",
            effective_from=date(2026, 7, 23),
            list_review_period_months=12,
            target_workplace=second_workplace,
        )
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(WorkplaceDocumentSourceRevision.objects.count(), 2)

    def test_staging_source_metadata_and_raw_row_values_are_immutable(self):
        revision = self.stage()
        revision.source_reference = "Попытка изменить основание"
        with self.assertRaisesMessage(ValidationError, "неизменяемы"):
            revision.save()
        row = revision.source_rows.get(register_entry_no=1)
        row.document_title_raw = "Попытка изменить исходное название"
        with self.assertRaisesMessage(ValidationError, "неизменяемы"):
            row.save()

    def test_staging_is_idempotent_by_organization_and_source_sha(self):
        first = self.stage()
        second = self.stage()
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(WorkplaceDocumentSourceRevision.objects.count(), 1)

    def test_same_file_with_corrected_metadata_creates_new_immutable_revision(self):
        first = self.stage()
        second = stage_workplace_document_register(
            uploaded_file=self.upload(),
            employee=self.employee,
            data_profile=self.profile,
            source_reference="Исправленное основание перечня",
            effective_from=date(2026, 7, 24),
            list_review_period_months=24,
        )
        self.assertNotEqual(first.pk, second.pk)
        self.assertEqual(WorkplaceDocumentSourceRevision.objects.count(), 2)
        self.assertEqual(first.source_reference, "Синтетический перечень документации от 07.08.2024")

    def test_presentation_database_blocks_real_register(self):
        with override_settings(EOD_DATABASE_PROFILE="presentation"):
            with self.assertRaises(PermissionDenied):
                self.stage()
        self.assertFalse(WorkplaceDocumentSourceRevision.objects.exists())

    def test_preview_excludes_review_and_blocked_rows(self):
        rows = synthetic_workplace_document_rows()
        rows[1]["source_notes"] = "Требуется проверка."
        revision = self.stage(synthetic_workplace_document_csv(rows=rows))
        preview = build_workplace_document_publication_preview(revision)
        self.assertEqual(preview["summary"]["publishable_rows"], 1)
        self.assertEqual(preview["summary"]["review_rows"], 1)
        self.assertEqual(len(preview["payload"]["excluded"]), 1)

    def test_review_rows_require_audited_decision_before_publication(self):
        rows = synthetic_workplace_document_rows()
        rows[1]["source_notes"] = "Проверить исходное наименование."
        revision = self.stage(synthetic_workplace_document_csv(rows=rows))
        preview = build_workplace_document_publication_preview(revision)
        with self.assertRaisesMessage(ValidationError, "примите решение"):
            publish_workplace_document_register(
                source_revision=revision,
                actor=self.employee,
                expected_digest=preview["digest"],
            )
        review_row = revision.source_rows.get(register_entry_no=2)
        decide_workplace_document_source_row(
            source_revision=revision,
            row_id=review_row.pk,
            actor=self.employee,
            action=WorkplaceDocumentSourceRow.ReviewDecision.ACCEPT_AS_IS,
            note="Исходное наименование подтверждено для прототипа.",
        )
        revision.refresh_from_db()
        review_row.refresh_from_db()
        self.assertEqual(revision.review_rows, 0)
        self.assertEqual(revision.ready_rows, 2)
        self.assertEqual(review_row.review_status, WorkplaceDocumentSourceRow.ReviewStatus.READY)
        self.assertEqual(
            review_row.review_decision,
            WorkplaceDocumentSourceRow.ReviewDecision.ACCEPT_AS_IS,
        )
        self.assertEqual(review_row.reviewed_by, self.employee)

    def test_review_row_may_be_excluded_and_reset_without_physical_deletion(self):
        rows = synthetic_workplace_document_rows()
        rows[1]["source_notes"] = "Проверить исходную позицию."
        revision = self.stage(synthetic_workplace_document_csv(rows=rows))
        ready_row = revision.source_rows.get(register_entry_no=1)
        with self.assertRaisesMessage(ValidationError, "изначально требующую проверки"):
            decide_workplace_document_source_row(
                source_revision=revision,
                row_id=ready_row.pk,
                actor=self.employee,
                action=WorkplaceDocumentSourceRow.ReviewDecision.EXCLUDE,
                note="Готовая строка не должна исключаться через контур неоднозначностей.",
            )
        row = revision.source_rows.get(register_entry_no=2)
        decide_workplace_document_source_row(
            source_revision=revision,
            row_id=row.pk,
            actor=self.employee,
            action=WorkplaceDocumentSourceRow.ReviewDecision.EXCLUDE,
            note="Позиция временно исключена до уточнения источника.",
        )
        revision.refresh_from_db()
        row.refresh_from_db()
        self.assertEqual(revision.excluded_rows, 1)
        self.assertEqual(row.review_status, WorkplaceDocumentSourceRow.ReviewStatus.EXCLUDED)
        decide_workplace_document_source_row(
            source_revision=revision,
            row_id=row.pk,
            actor=self.employee,
            action="RESET",
            note="",
        )
        revision.refresh_from_db()
        row.refresh_from_db()
        self.assertEqual(revision.excluded_rows, 0)
        self.assertEqual(revision.review_rows, 1)
        self.assertEqual(row.review_decision, WorkplaceDocumentSourceRow.ReviewDecision.NONE)

    def test_controlled_publication_creates_approved_revision_and_preserves_source_metadata(self):
        revision = self.stage()
        preview = build_workplace_document_publication_preview(revision)
        publication = publish_workplace_document_register(
            source_revision=revision,
            actor=self.employee,
            expected_digest=preview["digest"],
        )
        revision.refresh_from_db()
        self.assertEqual(revision.status, WorkplaceDocumentSourceRevision.Status.PUBLISHED)
        self.assertEqual(revision.ready_rows, 0)
        self.assertEqual(
            revision.source_rows.filter(
                review_status=WorkplaceDocumentSourceRow.ReviewStatus.PUBLISHED
            ).count(),
            2,
        )
        self.assertEqual(revision.target_revision.status, RevisionStatus.APPROVED)
        self.assertEqual(publication.result_summary["created_entries"], 2)
        self.assertEqual(publication.result_summary["paper_storage_waivers_created"], 0)
        first = WorkplaceDocumentEntry.objects.get(source_register_entry_no=1)
        second = WorkplaceDocumentEntry.objects.get(source_register_entry_no=2)
        self.assertEqual(first.storage_form, StorageForm.UNKNOWN)
        self.assertEqual(
            first.electronic_storage_interpretation,
            ElectronicStorageInterpretation.INDICATED,
        )
        self.assertIn("не отменяет", first.notes)
        self.assertEqual(second.storage_form, StorageForm.UNKNOWN)
        self.assertEqual(first.section_name, "Пожарная безопасность")
        self.assertEqual(first.review_interval_months, 36)

    def test_publication_requires_direct_role_and_matching_digest(self):
        revision = self.stage()
        preview = build_workplace_document_publication_preview(revision)
        RoleAssignment.objects.filter(employee=self.employee).update(is_active=False)
        with self.assertRaises(PermissionDenied):
            publish_workplace_document_register(
                source_revision=revision,
                actor=self.employee,
                expected_digest=preview["digest"],
            )
        RoleAssignment.objects.filter(employee=self.employee).update(is_active=True)
        with self.assertRaisesMessage(ValidationError, "Состав staging изменился"):
            publish_workplace_document_register(
                source_revision=revision,
                actor=self.employee,
                expected_digest="0" * 64,
            )

    def test_discard_keeps_rows_and_prevents_publication(self):
        revision = self.stage()
        discard_workplace_document_revision(
            source_revision=revision,
            actor=self.employee,
        )
        revision.refresh_from_db()
        self.assertEqual(revision.status, WorkplaceDocumentSourceRevision.Status.DISCARDED)
        self.assertEqual(revision.source_rows.count(), 2)
        with self.assertRaises(ValidationError):
            publish_workplace_document_register(
                source_revision=revision,
                actor=self.employee,
                expected_digest="0" * 64,
            )

    def test_review_decision_view_records_actor_note_and_refreshes_counters(self):
        rows = synthetic_workplace_document_rows()
        rows[1]["source_notes"] = "Проверить нумерацию."
        revision = self.stage(synthetic_workplace_document_csv(rows=rows))
        row = revision.source_rows.get(register_entry_no=2)
        self.client.force_login(self.user)
        response = self.client.post(
            reverse(
                "imports:workplace_document_row_decide",
                args=[revision.public_id, row.pk],
            ),
            {
                "action": "ACCEPT_AS_IS",
                "note": "Нумерация подтверждена по исходному перечню.",
            },
        )
        self.assertEqual(response.status_code, 302)
        revision.refresh_from_db()
        row.refresh_from_db()
        self.assertEqual(revision.review_rows, 0)
        self.assertEqual(row.reviewed_by, self.employee)
        detail = self.client.get(
            reverse("imports:workplace_document_detail", args=[revision.public_id])
        )
        self.assertContains(detail, "Нумерация подтверждена")

    def test_upload_detail_preview_and_published_registry_are_visible(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("imports:workplace_document_upload"),
            {
                "data_profile": self.profile.pk,
                "target_workplace": self.workplace.pk,
                "source_reference": "Перечень документации, утверждён 07.08.2024",
                "effective_from": "2026-07-23",
                "list_review_period_months": 12,
                "source_file": self.upload(),
            },
        )
        self.assertEqual(response.status_code, 302)
        revision = WorkplaceDocumentSourceRevision.objects.get()
        detail = self.client.get(
            reverse("imports:workplace_document_detail", args=[revision.public_id])
        )
        self.assertContains(detail, "Знак «+» — не разрешение отказаться от бумаги")
        self.assertContains(detail, "Сопоставлено")
        preview = self.client.get(
            reverse("imports:workplace_document_publication", args=[revision.public_id])
        )
        self.assertContains(preview, "Отказов от бумаги")
        publication_response = self.client.post(
            reverse("imports:workplace_document_publication", args=[revision.public_id]),
            {
                "preview_digest": build_workplace_document_publication_preview(revision)[
                    "digest"
                ],
                "password": "Workdoc-01162-Test!",
                "confirm": "on",
            },
        )
        self.assertEqual(publication_response.status_code, 302)
        revision.refresh_from_db()
        published_detail = self.client.get(
            reverse("imports:workplace_document_detail", args=[revision.public_id])
        )
        self.assertContains(published_detail, "Опубликовано")
        self.assertContains(published_detail, "<strong>2</strong>", html=True)
        registry = self.client.get(
            reverse("workplace_docs:detail", args=[revision.target_document_list_id])
        )
        self.assertContains(registry, "Пожарная безопасность")
        self.assertContains(registry, "Исходная отметка: +")
        search = self.client.get(
            reverse("workplace_docs:detail", args=[revision.target_document_list_id]),
            {"q": "Инструкция"},
        )
        self.assertContains(search, "Инструкция действий")
        self.assertNotContains(search, "Перечень безопасного")
