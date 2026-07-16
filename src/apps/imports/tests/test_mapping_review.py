from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.equipment.models import EnergySite, EquipmentAsset, EquipmentType
from apps.imports.models import ImportBatch, ImportEvent, ImportRow
from apps.imports.services import (
    bulk_decide_import_rows,
    create_import_batch,
    decide_import_row,
    save_column_mapping,
    save_row_correction,
)
from apps.organizations.models import Division, Employee, Organization, Position


class ImportMappingReviewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.organization = Organization.objects.create(
            code="MAP-ORG",
            name="Организация сопоставления",
        )
        self.division = Division.objects.create(
            organization=self.organization,
            code="MAP-DIV",
            name="Оперативное подразделение",
        )
        self.position = Position.objects.create(
            organization=self.organization,
            code="MAP-POS",
            name="Оперативный работник",
        )
        self.user = user_model.objects.create_user(
            username="mapping-review",
            password="test",
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=self.division,
            position=self.position,
            user=self.user,
            personnel_number="MAP-001",
            last_name="Проверяющий",
            first_name="Импорт",
            employment_start=date(2026, 1, 1),
        )
        self.site = EnergySite.objects.create(
            organization=self.organization,
            code="map-site",
            name="Тестовая ВЭС",
            short_name="Тестовая ВЭС",
            site_type=EnergySite.SiteType.WIND_POWER_PLANT,
        )
        self.equipment_type = EquipmentType.objects.create(
            code="map-transformer",
            name="Трансформатор",
            category=EquipmentType.Category.SUBSTATION,
        )

    def equipment_batch(self, rows: list[str]) -> ImportBatch:
        body = (
            "Код;Наименование;Вид оборудования;Энергообъект;Состояние\n"
            + "\n".join(rows)
            + "\n"
        )
        return create_import_batch(
            uploaded_file=SimpleUploadedFile(
                "equipment-review.csv",
                body.encode("utf-8"),
            ),
            target_registry=ImportBatch.TargetRegistry.EQUIPMENT,
            employee=self.employee,
        )

    def confirm_mapping(self, batch: ImportBatch, **changes: str) -> ImportBatch:
        mapping = {
            column.position: changes.get(column.source_name, column.mapped_key)
            for column in batch.columns.order_by("position")
        }
        return save_column_mapping(
            batch=batch,
            employee=self.employee,
            mapping=mapping,
        )

    def valid_row_text(self, code: str = "EQ-MAP-1") -> str:
        return f"{code};Трансформатор собственных нужд;Трансформатор;Тестовая ВЭС;В работе"

    def test_auto_mapping_suggests_equipment_fields(self):
        batch = self.equipment_batch([self.valid_row_text()])
        mapped = {
            column.source_name: column.mapped_key
            for column in batch.columns.order_by("position")
        }
        self.assertEqual(mapped["Код"], "code")
        self.assertEqual(mapped["Наименование"], "technical_name")
        self.assertEqual(mapped["Вид оборудования"], "type")
        self.assertEqual(mapped["Энергообъект"], "site")
        self.assertEqual(mapped["Состояние"], "status")
        self.assertIsNone(batch.mapping_completed_at)

    def test_mapping_requires_all_required_fields(self):
        batch = self.equipment_batch([self.valid_row_text()])
        mapping = {column.position: "" for column in batch.columns.all()}
        with self.assertRaisesMessage(ValidationError, "Не сопоставлены обязательные поля"):
            save_column_mapping(
                batch=batch,
                employee=self.employee,
                mapping=mapping,
            )

    def test_mapping_rejects_duplicate_target_field(self):
        batch = self.equipment_batch([self.valid_row_text()])
        columns = list(batch.columns.order_by("position"))
        mapping = {column.position: column.mapped_key for column in columns}
        mapping[columns[1].position] = "code"
        with self.assertRaisesMessage(ValidationError, "назначено колонкам"):
            save_column_mapping(
                batch=batch,
                employee=self.employee,
                mapping=mapping,
            )

    def test_mapping_recalculates_valid_row_and_audits(self):
        batch = self.confirm_mapping(self.equipment_batch([self.valid_row_text()]))
        row = batch.rows.get()
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.VALID)
        self.assertEqual(row.mapped_values["code"], "EQ-MAP-1")
        self.assertEqual(row.mapped_values["status"], "ACTIVE")
        self.assertEqual(batch.mapping_revision, 1)
        self.assertTrue(
            batch.events.filter(event_type=ImportEvent.EventType.MAPPING_UPDATED).exists()
        )
        self.assertTrue(
            batch.events.filter(
                event_type=ImportEvent.EventType.REVIEW_RECALCULATED
            ).exists()
        )

    def test_duplicate_rows_are_conflicts_after_mapping(self):
        batch = self.confirm_mapping(
            self.equipment_batch(
                [self.valid_row_text("EQ-DUP"), self.valid_row_text("EQ-DUP")]
            )
        )
        self.assertEqual(
            batch.rows.filter(review_status=ImportRow.ReviewStatus.CONFLICT).count(),
            2,
        )
        for row in batch.rows.all():
            self.assertIn("Дублирующая запись", " ".join(row.registry_conflicts))

    def test_existing_equipment_code_is_registry_conflict(self):
        EquipmentAsset.objects.create(
            organization=self.organization,
            site=self.site,
            equipment_type=self.equipment_type,
            code="EQ-EXISTS",
            technical_name="Существующее оборудование",
        )
        batch = self.confirm_mapping(
            self.equipment_batch([self.valid_row_text("EQ-EXISTS")])
        )
        row = batch.rows.get()
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.CONFLICT)
        self.assertIn("уже существует", " ".join(row.registry_conflicts))

    def test_invalid_choice_is_invalid(self):
        invalid = "EQ-BAD;Трансформатор;Трансформатор;Тестовая ВЭС;Неизвестное состояние"
        batch = self.confirm_mapping(self.equipment_batch([invalid]))
        row = batch.rows.get()
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.INVALID)
        self.assertIn("допускает значения", " ".join(row.validation_issues))

    def test_accept_valid_row_is_audited(self):
        batch = self.confirm_mapping(self.equipment_batch([self.valid_row_text()]))
        row = batch.rows.get()
        decide_import_row(row=row, employee=self.employee, action="ACCEPT")
        row.refresh_from_db()
        batch.refresh_from_db()
        self.assertEqual(row.decision, ImportRow.Decision.ACCEPTED)
        self.assertEqual(batch.review_counts["accepted"], 1)
        self.assertTrue(
            batch.events.filter(event_type=ImportEvent.EventType.ROW_DECISION).exists()
        )

    def test_conflict_cannot_be_accepted(self):
        batch = self.confirm_mapping(
            self.equipment_batch(
                [self.valid_row_text("EQ-DUP-2"), self.valid_row_text("EQ-DUP-2")]
            )
        )
        with self.assertRaisesMessage(ValidationError, "нельзя принять"):
            decide_import_row(
                row=batch.rows.first(),
                employee=self.employee,
                action="ACCEPT",
            )

    def test_correction_can_replace_code_and_accept(self):
        EquipmentAsset.objects.create(
            organization=self.organization,
            site=self.site,
            equipment_type=self.equipment_type,
            code="EQ-CONFLICT",
            technical_name="Существующее оборудование",
        )
        batch = self.confirm_mapping(
            self.equipment_batch([self.valid_row_text("EQ-CONFLICT")])
        )
        row = batch.rows.get()
        values = dict(row.mapped_values)
        values["code"] = "EQ-CORRECTED"
        save_row_correction(
            row=row,
            employee=self.employee,
            values=values,
            note="Исправлен стабильный код.",
        )
        row.refresh_from_db()
        self.assertEqual(row.decision, ImportRow.Decision.ACCEPTED)
        self.assertEqual(row.decision_values["code"], "EQ-CORRECTED")
        event = batch.events.filter(event_type=ImportEvent.EventType.ROW_DECISION).latest(
            "created_at"
        )
        self.assertIn("code", event.details["changed_fields"])

    def test_reject_and_reset_row(self):
        batch = self.confirm_mapping(self.equipment_batch([self.valid_row_text()]))
        row = batch.rows.get()
        decide_import_row(
            row=row,
            employee=self.employee,
            action="REJECT",
            note="Не относится к выбранному справочнику.",
        )
        row.refresh_from_db()
        self.assertEqual(row.decision, ImportRow.Decision.REJECTED)
        decide_import_row(row=row, employee=self.employee, action="RESET")
        row.refresh_from_db()
        self.assertEqual(row.decision, ImportRow.Decision.PENDING)
        self.assertEqual(row.decision_note, "")

    def test_bulk_decisions_create_individual_and_bulk_audit(self):
        batch = self.confirm_mapping(
            self.equipment_batch(
                [self.valid_row_text("EQ-BULK-1"), self.valid_row_text("EQ-BULK-2")]
            )
        )
        result = bulk_decide_import_rows(
            batch=batch,
            employee=self.employee,
            row_ids=list(batch.rows.values_list("pk", flat=True)),
            action="ACCEPT",
        )
        self.assertEqual(result, {"processed": 2, "skipped": 0})
        self.assertEqual(
            batch.events.filter(event_type=ImportEvent.EventType.ROW_DECISION).count(),
            2,
        )
        self.assertEqual(
            batch.events.filter(event_type=ImportEvent.EventType.BULK_DECISION).count(),
            1,
        )

    def test_mapping_change_resets_decisions(self):
        batch = self.confirm_mapping(self.equipment_batch([self.valid_row_text()]))
        row = batch.rows.get()
        decide_import_row(row=row, employee=self.employee, action="ACCEPT")
        self.confirm_mapping(batch)
        row.refresh_from_db()
        batch.refresh_from_db()
        self.assertEqual(row.decision, ImportRow.Decision.PENDING)
        self.assertEqual(batch.mapping_revision, 2)

    def test_mapping_and_row_views_render_without_publish_action(self):
        batch = self.equipment_batch([self.valid_row_text()])
        self.client.force_login(self.user)
        mapping_page = self.client.get(reverse("imports:mapping", args=[batch.public_id]))
        self.assertContains(mapping_page, "Сопоставление не публикует данные")
        self.assertContains(mapping_page, "Подтвердить сопоставление")
        self.assertNotContains(mapping_page, 'name="publish"')

        self.confirm_mapping(batch)
        detail = self.client.get(reverse("imports:detail", args=[batch.public_id]))
        self.assertContains(detail, "Массовое решение для отмеченных строк")
        self.assertContains(detail, "Приняты предварительно")
        self.assertContains(detail, "Убрать из рабочего списка")
        self.assertNotContains(detail, "/publish/")

        row = batch.rows.get()
        edit = self.client.get(
            reverse("imports:row_edit", args=[batch.public_id, row.pk])
        )
        self.assertContains(edit, "Исправление останется только в промежуточной зоне")

    def test_cross_organization_row_action_is_hidden(self):
        other = Organization.objects.create(code="OTHER-MAP", name="Другая организация")
        other_division = Division.objects.create(
            organization=other,
            code="OTHER-DIV",
            name="Другое подразделение",
        )
        other_position = Position.objects.create(
            organization=other,
            code="OTHER-POS",
            name="Другая должность",
        )
        other_employee = Employee.objects.create(
            organization=other,
            division=other_division,
            position=other_position,
            personnel_number="OTHER-001",
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
            file_sha256="e" * 64,
            status=ImportBatch.Status.READY,
        )
        row = ImportRow.objects.create(
            batch=batch,
            row_number=2,
            source_values=["X"],
            normalized_values=["X"],
            status=ImportRow.Status.NEW,
            fingerprint="f" * 64,
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("imports:row_decide", args=[batch.public_id, row.pk]),
            {"action": "REJECT"},
        )
        self.assertEqual(response.status_code, 404)

    def test_organization_personnel_number_conflict(self):
        body = (
            "Табельный номер;Фамилия;Имя;Подразделение;Должность\n"
            "MAP-001;Новый;Сотрудник;Оперативное подразделение;Оперативный работник\n"
        )
        batch = create_import_batch(
            uploaded_file=SimpleUploadedFile("employees.csv", body.encode("utf-8")),
            target_registry=ImportBatch.TargetRegistry.ORGANIZATION,
            employee=self.employee,
        )
        mapping = {column.position: column.mapped_key for column in batch.columns.all()}
        save_column_mapping(batch=batch, employee=self.employee, mapping=mapping)
        row = batch.rows.get()
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.CONFLICT)
        self.assertIn("табельным номером", " ".join(row.registry_conflicts))
