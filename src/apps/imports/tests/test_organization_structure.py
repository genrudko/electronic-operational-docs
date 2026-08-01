from __future__ import annotations

from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from apps.equipment.models import EnergySite
from apps.imports.models import ImportBatch, ImportPublication, ImportRow
from apps.imports.services import (
    build_import_publication_preview,
    create_import_batch,
    decide_import_row,
    publish_import_batch,
    save_column_mapping,
    save_row_correction,
)
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    ResponsibilityScope,
    Role,
    RoleAssignment,
    Workplace,
)


class OrganizationStructureImportTests(TestCase):
    password = "Structure-Test-2026!"
    headers = (
        "Вид структуры;Код;Наименование;Родительский код;"
        "Код подразделения;Краткое наименование;Тип энергообъекта;"
        "Внешний объект;Действующая запись"
    )

    def setUp(self):
        user_model = get_user_model()
        self.organization = Organization.objects.create(
            code="STRUCT-ORG",
            name="Организация структуры",
        )
        self.base_division = Division.objects.create(
            organization=self.organization,
            code="BASE",
            name="Базовое подразделение",
        )
        self.position = Position.objects.create(
            organization=self.organization,
            code="STRUCT-POS",
            name="Администратор справочников",
        )
        self.scope = ResponsibilityScope.objects.create(
            organization=self.organization,
            code="ALL",
            name="Вся организация",
        )
        self.user = user_model.objects.create_user(
            username="structure-publisher",
            password=self.password,
        )
        self.employee = Employee.objects.create(
            organization=self.organization,
            division=self.base_division,
            position=self.position,
            user=self.user,
            personnel_number="STRUCT-001",
            last_name="Администратор",
            first_name="Структуры",
            employment_start=date(2026, 1, 1),
        )
        role, _created = Role.objects.get_or_create(
            code="organization_admin",
            defaults={
                "name": "Администратор справочников",
                "description": "Публикация справочников.",
                "is_system": True,
                "is_active": True,
            },
        )
        RoleAssignment.objects.create(
            employee=self.employee,
            role=role,
            scope=self.scope,
            valid_from=date(2026, 1, 1),
            is_active=True,
        )

    def upload(self, *rows: str, name: str = "structure.csv") -> ImportBatch:
        body = self.headers + "\n" + "\n".join(rows) + "\n"
        return create_import_batch(
            uploaded_file=SimpleUploadedFile(name, body.encode("utf-8")),
            target_registry=ImportBatch.TargetRegistry.ORGANIZATION_STRUCTURE,
            employee=self.employee,
        )

    def confirm(self, batch: ImportBatch) -> ImportBatch:
        mapping = {
            column.position: column.mapped_key
            for column in batch.columns.order_by("position")
        }
        return save_column_mapping(
            batch=batch,
            employee=self.employee,
            mapping=mapping,
        )

    def accept_all(self, batch: ImportBatch) -> ImportBatch:
        for row in batch.rows.order_by("row_number"):
            decide_import_row(
                row=row,
                employee=self.employee,
                action="ACCEPT",
            )
        batch.refresh_from_db()
        return batch

    def publish(self, batch: ImportBatch):
        preview = build_import_publication_preview(batch)
        return publish_import_batch(
            batch=batch,
            actor=self.employee,
            user=self.user,
            password=self.password,
            expected_digest=preview.digest,
        )

    def test_same_batch_dependencies_publish_in_deterministic_order(self):
        batch = self.confirm(
            self.upload(
                "DIVISION;CHILD;Оперативный участок;ROOT;;;;Нет;Да",
                "WORKPLACE;SHIFT;Рабочее место смены;;CHILD;;;Нет;Да",
                "DIVISION;ROOT;Производственное подразделение;;;;;Нет;Да",
                "ENERGY_SITE;SITE-1;Кочубеевская ВЭС;;;КВЭС;"
                "Ветроэлектростанция;Нет;Да",
            )
        )
        self.assertEqual(
            set(batch.rows.values_list("review_status", flat=True)),
            {ImportRow.ReviewStatus.VALID},
        )
        self.accept_all(batch)

        first = build_import_publication_preview(batch)
        second = build_import_publication_preview(batch)
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(
            [effect["target_model"] for effect in first.effects],
            [
                "organizations.Division",
                "organizations.Division",
                "organizations.Workplace",
                "equipment.EnergySite",
            ],
        )
        self.assertEqual(
            [row.effective_values["code"] for row in first.accepted_rows],
            ["ROOT", "CHILD", "SHIFT", "SITE-1"],
        )

        publication = self.publish(batch)
        root = Division.objects.get(organization=self.organization, code="ROOT")
        child = Division.objects.get(organization=self.organization, code="CHILD")
        workplace = Workplace.objects.get(
            organization=self.organization,
            code="SHIFT",
        )
        site = EnergySite.objects.get(
            organization=self.organization,
            code="site-1",
        )
        self.assertEqual(child.parent, root)
        self.assertEqual(workplace.division, child)
        self.assertEqual(site.site_type, EnergySite.SiteType.WIND_POWER_PLANT)
        self.assertEqual(publication.published_rows.count(), 4)

    def test_division_cycle_blocks_every_cycle_row(self):
        batch = self.confirm(
            self.upload(
                "DIVISION;A;Подразделение А;B;;;;Нет;Да",
                "DIVISION;B;Подразделение Б;A;;;;Нет;Да",
            )
        )
        rows = list(batch.rows.order_by("row_number"))
        self.assertTrue(
            all(row.review_status == ImportRow.ReviewStatus.INVALID for row in rows)
        )
        self.assertTrue(
            all("цикл" in " ".join(row.validation_issues).casefold() for row in rows)
        )
        with self.assertRaisesMessage(ValidationError, "нельзя принять"):
            decide_import_row(
                row=rows[0],
                employee=self.employee,
                action="ACCEPT",
            )

    def test_duplicate_kind_code_and_ambiguous_name_are_conflicts(self):
        batch = self.confirm(
            self.upload(
                "DIVISION;DUP;Первое имя;;;;;Нет;Да",
                "DIVISION;DUP;Второе имя;;;;;Нет;Да",
                "WORKPLACE;WP-1;Одинаковое имя;;;;;Нет;Да",
                "WORKPLACE;WP-2;Одинаковое имя;;;;;Нет;Да",
            )
        )
        rows = list(batch.rows.order_by("row_number"))
        self.assertEqual(rows[0].review_status, ImportRow.ReviewStatus.CONFLICT)
        self.assertEqual(rows[1].review_status, ImportRow.ReviewStatus.CONFLICT)
        self.assertIn("вид структуры + код", " ".join(rows[0].registry_conflicts))
        self.assertEqual(rows[2].review_status, ImportRow.ReviewStatus.CONFLICT)
        self.assertEqual(rows[3].review_status, ImportRow.ReviewStatus.CONFLICT)
        self.assertIn("наименования", " ".join(rows[2].registry_conflicts))

    def test_unresolved_dependency_is_blocked(self):
        batch = self.confirm(
            self.upload(
                "WORKPLACE;SHIFT-2;Рабочее место;;MISSING;;;Нет;Да",
            )
        )
        row = batch.rows.get()
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.INVALID)
        self.assertIn("не найдено", " ".join(row.validation_issues))

    def test_correction_recalculates_effective_dependency_values(self):
        batch = self.confirm(
            self.upload(
                "WORKPLACE;SHIFT-CORRECTED;Исправляемое место;;MISSING;;;Нет;Да",
            )
        )
        row = batch.rows.get()
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.INVALID)
        corrected = dict(row.effective_values)
        corrected["division_code"] = self.base_division.code
        row = save_row_correction(
            row=row,
            employee=self.employee,
            values=corrected,
            note="Исправлен код подразделения.",
        )
        self.assertEqual(row.decision, ImportRow.Decision.ACCEPTED)
        self.assertEqual(row.review_status, ImportRow.ReviewStatus.VALID)
        batch.refresh_from_db()
        self.assertTrue(batch.review_counts["ready"])
        self.publish(batch)
        workplace = Workplace.objects.get(
            organization=self.organization,
            code="SHIFT-CORRECTED",
        )
        self.assertEqual(workplace.division, self.base_division)

    def test_existing_code_and_active_name_are_conflicts(self):
        Division.objects.create(
            organization=self.organization,
            code="EXISTING",
            name="Действующее имя",
        )
        batch = self.confirm(
            self.upload(
                "DIVISION;EXISTING;Новое имя;;;;;Нет;Да",
                "DIVISION;NEW-CODE;Действующее имя;;;;;Нет;Да",
            )
        )
        rows = list(batch.rows.order_by("row_number"))
        self.assertIn("точным кодом", " ".join(rows[0].registry_conflicts))
        self.assertIn("действующей записью", " ".join(rows[1].registry_conflicts))

    def test_rejecting_dependency_recalculates_dependent_row(self):
        batch = self.confirm(
            self.upload(
                "DIVISION;PARENT;Родитель;;;;;Нет;Да",
                "WORKPLACE;DEPENDENT;Зависимое место;;PARENT;;;Нет;Да",
            )
        )
        parent, dependent = list(batch.rows.order_by("row_number"))
        decide_import_row(
            row=dependent,
            employee=self.employee,
            action="ACCEPT",
        )
        decide_import_row(
            row=parent,
            employee=self.employee,
            action="REJECT",
        )
        dependent.refresh_from_db()
        batch.refresh_from_db()
        self.assertEqual(dependent.review_status, ImportRow.ReviewStatus.INVALID)
        self.assertFalse(batch.review_counts["ready"])
        self.assertEqual(batch.review_counts["blocked"], 1)

    def test_publication_failure_rolls_back_earlier_created_structure(self):
        batch = self.accept_all(
            self.confirm(
                self.upload(
                    "DIVISION;ROLLBACK-ROOT;Временный корень;;;;;Нет;Да",
                    "WORKPLACE;ROLLBACK-WP;Временное место;;ROLLBACK-ROOT;;;Нет;Да",
                )
            )
        )
        preview = build_import_publication_preview(batch)
        with patch(
            "apps.imports.organization_structure.Workplace.save",
            side_effect=ValidationError("Принудительная ошибка публикации."),
        ):
            with self.assertRaisesMessage(ValidationError, "Принудительная"):
                publish_import_batch(
                    batch=batch,
                    actor=self.employee,
                    user=self.user,
                    password=self.password,
                    expected_digest=preview.digest,
                )
        self.assertFalse(
            Division.objects.filter(
                organization=self.organization,
                code="ROLLBACK-ROOT",
            ).exists()
        )
        self.assertFalse(ImportPublication.objects.filter(batch=batch).exists())
        batch.refresh_from_db()
        self.assertEqual(batch.status, ImportBatch.Status.READY)

    def test_legacy_organization_target_still_publishes_employee(self):
        body = (
            "Табельный номер;Фамилия;Имя;Отчество;Подразделение;"
            "Должность;Дата начала работы;Действующий сотрудник\n"
            "LEGACY-001;Иванов;Иван;Иванович;Базовое подразделение;"
            "Администратор справочников;01.02.2026;Да\n"
        )
        batch = create_import_batch(
            uploaded_file=SimpleUploadedFile(
                "legacy-organization.csv",
                body.encode("utf-8"),
            ),
            target_registry=ImportBatch.TargetRegistry.ORGANIZATION,
            employee=self.employee,
        )
        self.confirm(batch)
        self.accept_all(batch)
        self.publish(batch)
        self.assertTrue(
            Employee.objects.filter(
                organization=self.organization,
                personnel_number="LEGACY-001",
            ).exists()
        )
