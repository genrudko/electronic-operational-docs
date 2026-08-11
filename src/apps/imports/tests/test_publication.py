from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from apps.dispatching.models import (
    DispatchLevel,
    DispatchSubject,
    ManagementRevision,
    SupervisionRevision,
)
from apps.dispatching.models import (
    PublicationStatus as DispatchPublicationStatus,
)
from apps.equipment.models import (
    EnergySite,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentType,
)
from apps.equipment.models import (
    PublicationStatus as EquipmentPublicationStatus,
)
from apps.imports.models import (
    ImportBatch,
    ImportEvent,
    ImportPublication,
    ImportPublicationRow,
)
from apps.imports.services import (
    build_import_publication_preview,
    can_publish_import,
    create_import_batch,
    decide_import_row,
    discard_import_batch,
    publish_import_batch,
    save_column_mapping,
)
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    ResponsibilityScope,
    Role,
    RoleAssignment,
)
from tests.credential_fixtures import ephemeral_credential


class ControlledImportPublicationTests(TestCase):
    def setUp(self):
        self.credential = ephemeral_credential("ImportPublication")
        user_model = get_user_model()
        self.organization = Organization.objects.create(
            code="PUB-ORG",
            name="Организация публикации",
        )
        self.division = Division.objects.create(
            organization=self.organization,
            code="PUB-DIV",
            name="Оперативное подразделение",
        )
        self.position = Position.objects.create(
            organization=self.organization,
            code="PUB-POS",
            name="Оперативный работник",
        )
        self.scope = ResponsibilityScope.objects.create(
            organization=self.organization,
            code="ALL",
            name="Вся организация",
        )
        self.publisher_user = user_model.objects.create_user(
            username="publisher",
            password=self.credential,
        )
        self.publisher = Employee.objects.create(
            organization=self.organization,
            division=self.division,
            position=self.position,
            user=self.publisher_user,
            personnel_number="PUB-001",
            last_name="Администратор",
            first_name="Справочников",
            employment_start=date(2026, 1, 1),
        )
        role, _ = Role.objects.get_or_create(
            code="organization_admin",
            defaults={
                "name": "Администратор справочников",
                "description": "Публикация справочников.",
                "is_system": True,
                "is_active": True,
            },
        )
        RoleAssignment.objects.create(
            employee=self.publisher,
            role=role,
            scope=self.scope,
            valid_from=date(2026, 1, 1),
            is_active=True,
        )

        self.viewer_user = user_model.objects.create_user(
            username="viewer",
            password=ephemeral_credential("ImportViewer"),
        )
        self.viewer = Employee.objects.create(
            organization=self.organization,
            division=self.division,
            position=self.position,
            user=self.viewer_user,
            personnel_number="PUB-002",
            last_name="Проверяющий",
            first_name="БезПрава",
            employment_start=date(2026, 1, 1),
        )
        self.site = EnergySite.objects.create(
            organization=self.organization,
            code="pub-site",
            name="Тестовая ВЭС",
            short_name="Тестовая ВЭС",
            site_type=EnergySite.SiteType.WIND_POWER_PLANT,
        )
        self.equipment_type = EquipmentType.objects.create(
            code="pub-transformer",
            name="Трансформатор",
            category=EquipmentType.Category.SUBSTATION,
        )
        self.level = DispatchLevel.objects.create(
            organization=self.organization,
            code="pub-level",
            name="Оперативный уровень",
            level_type=DispatchLevel.LevelType.TECHNOLOGICAL,
            rank=10,
        )
        self.subject = DispatchSubject.objects.create(
            organization=self.organization,
            code="pub-subject",
            name="Оперативный персонал",
            short_name="Оперативный персонал",
            subject_type=DispatchSubject.SubjectType.INTERNAL,
        )

    def upload(self, *, target: str, name: str, body: str) -> ImportBatch:
        return create_import_batch(
            uploaded_file=SimpleUploadedFile(name, body.encode("utf-8")),
            target_registry=target,
            employee=self.publisher,
        )

    def confirm(self, batch: ImportBatch) -> ImportBatch:
        mapping = {
            column.position: column.mapped_key
            for column in batch.columns.order_by("position")
        }
        return save_column_mapping(
            batch=batch,
            employee=self.publisher,
            mapping=mapping,
        )

    def accept_all(self, batch: ImportBatch) -> ImportBatch:
        for row in batch.rows.order_by("row_number"):
            decide_import_row(
                row=row,
                employee=self.publisher,
                action="ACCEPT",
            )
        batch.refresh_from_db()
        return batch

    def organization_batch(
        self,
        *numbers: str,
        reject_last: bool = False,
    ) -> ImportBatch:
        rows = [
            (
                f"{number};Иванов;Иван;Иванович;"
                "Оперативное подразделение;Оперативный работник;01.02.2026;Да"
            )
            for number in numbers
        ]
        body = (
            "Табельный номер;Фамилия;Имя;Отчество;Подразделение;"
            "Должность;Дата начала работы;Действующий сотрудник\n"
            + "\n".join(rows)
            + "\n"
        )
        batch = self.confirm(
            self.upload(
                target=ImportBatch.TargetRegistry.ORGANIZATION,
                name="employees.csv",
                body=body,
            )
        )
        for index, row in enumerate(batch.rows.order_by("row_number")):
            decide_import_row(
                row=row,
                employee=self.publisher,
                action=(
                    "REJECT"
                    if reject_last and index == len(rows) - 1
                    else "ACCEPT"
                ),
            )
        batch.refresh_from_db()
        return batch

    def equipment_batch(self, code: str = "PUB-EQ-1") -> ImportBatch:
        body = (
            "Стабильный код;Техническое наименование;Диспетчерское наименование;"
            "Вид оборудования;Энергообъект;Состояние;Класс напряжения;Дата ввода\n"
            f"{code};Трансформатор {code};Т-{code};Трансформатор;"
            "Тестовая ВЭС;В работе;35 кВ;01.03.2026\n"
        )
        return self.accept_all(
            self.confirm(
                self.upload(
                    target=ImportBatch.TargetRegistry.EQUIPMENT,
                    name="equipment.csv",
                    body=body,
                )
            )
        )

    def dispatching_batch(
        self,
        *,
        equipment_code: str,
        relation: str,
        information_only: str = "Нет",
    ) -> ImportBatch:
        body = (
            "Код оборудования;Управление или ведение;Субъект;Уровень;"
            "Действует с;Действует по;Информационное ведение;Основание\n"
            f"{equipment_code};{relation};Оперативный персонал;Оперативный уровень;"
            f"01.04.2026;;{information_only};Программа испытаний\n"
        )
        return self.accept_all(
            self.confirm(
                self.upload(
                    target=ImportBatch.TargetRegistry.DISPATCHING,
                    name="dispatching.csv",
                    body=body,
                )
            )
        )

    def publish(self, batch: ImportBatch) -> ImportPublication:
        preview = build_import_publication_preview(batch)
        return publish_import_batch(
            batch=batch,
            actor=self.publisher,
            user=self.publisher_user,
            password=self.credential,
            expected_digest=preview.digest,
        )

    def test_direct_administrator_role_is_required(self):
        self.assertTrue(can_publish_import(self.publisher_user))
        self.assertFalse(can_publish_import(self.viewer_user))
        batch = self.organization_batch("PUB-NEW-001")
        preview = build_import_publication_preview(batch)
        with self.assertRaises(PermissionDenied):
            publish_import_batch(
                batch=batch,
                actor=self.viewer,
                user=self.viewer_user,
                password=self.credential,
                expected_digest=preview.digest,
            )

    def test_preview_requires_all_rows_to_have_decisions(self):
        batch = self.confirm(
            self.upload(
                target=ImportBatch.TargetRegistry.ORGANIZATION,
                name="pending.csv",
                body=(
                    "Табельный номер;Фамилия;Имя;Подразделение;Должность\n"
                    "PUB-PENDING;Иванов;Иван;Оперативное подразделение;"
                    "Оперативный работник\n"
                ),
            )
        )
        with self.assertRaisesMessage(ValidationError, "каждой строке"):
            build_import_publication_preview(batch)

    def test_preview_digest_is_deterministic(self):
        batch = self.organization_batch("PUB-NEW-002")
        first = build_import_publication_preview(batch)
        second = build_import_publication_preview(batch)
        self.assertEqual(first.digest, second.digest)
        self.assertEqual(first.canonical_json, second.canonical_json)

    def test_other_registry_cannot_be_published(self):
        batch = self.confirm(
            self.upload(
                target=ImportBatch.TargetRegistry.OTHER,
                name="other.csv",
                body="Ключ;Наименование\nKEY-1;Запись\n",
            )
        )
        self.accept_all(batch)
        with self.assertRaisesMessage(ValidationError, "не имеет рабочего реестра"):
            build_import_publication_preview(batch)

    def test_wrong_password_creates_no_registry_records(self):
        batch = self.organization_batch("PUB-NEW-003")
        preview = build_import_publication_preview(batch)
        before = Employee.objects.count()
        invalid_credential = ephemeral_credential("InvalidImportPublication")
        with self.assertRaisesMessage(ValidationError, "Неверный"):
            publish_import_batch(
                batch=batch,
                actor=self.publisher,
                user=self.publisher_user,
                password=invalid_credential,
                expected_digest=preview.digest,
            )
        self.assertEqual(Employee.objects.count(), before)
        self.assertFalse(ImportPublication.objects.exists())

    def test_stale_digest_is_rejected_before_writes(self):
        batch = self.organization_batch("PUB-NEW-004")
        preview = build_import_publication_preview(batch)
        row = batch.rows.get()
        decide_import_row(row=row, employee=self.publisher, action="RESET")
        decide_import_row(row=row, employee=self.publisher, action="ACCEPT", note="Изменено")
        before = Employee.objects.count()
        with self.assertRaisesMessage(ValidationError, "Состав публикации изменился"):
            publish_import_batch(
                batch=batch,
                actor=self.publisher,
                user=self.publisher_user,
                password=self.credential,
                expected_digest=preview.digest,
            )
        self.assertEqual(Employee.objects.count(), before)

    def test_organization_publication_creates_only_accepted_employees(self):
        batch = self.organization_batch(
            "PUB-NEW-005",
            "PUB-NEW-006",
            reject_last=True,
        )
        publication = self.publish(batch)
        self.assertTrue(
            Employee.objects.filter(
                organization=self.organization,
                personnel_number="PUB-NEW-005",
            ).exists()
        )
        self.assertFalse(
            Employee.objects.filter(
                organization=self.organization,
                personnel_number="PUB-NEW-006",
            ).exists()
        )
        self.assertEqual(publication.result_summary["accepted"], 1)
        self.assertEqual(publication.result_summary["rejected"], 1)

    def test_publication_marks_batch_and_creates_immutable_snapshot(self):
        batch = self.organization_batch("PUB-NEW-007")
        publication = self.publish(batch)
        batch.refresh_from_db()
        self.assertEqual(batch.status, ImportBatch.Status.PUBLISHED)
        self.assertEqual(batch.publication_digest, publication.digest)
        self.assertEqual(batch.published_by, self.publisher)
        self.assertEqual(publication.published_rows.count(), 1)
        self.assertEqual(publication.schema_version, "eod.import.publication.v2")
        self.assertIn('"data_profile"', publication.canonical_json)
        self.assertEqual(
            publication.result_summary["data_profile"]["code"],
            batch.data_profile.code,
        )
        self.assertEqual(
            batch.events.filter(event_type=ImportEvent.EventType.PUBLISHED).count(),
            1,
        )
        with self.assertRaisesMessage(ValidationError, "неизменяем"):
            publication.save()
        with self.assertRaisesMessage(ValidationError, "запрещено"):
            publication.delete()
        result = publication.published_rows.get()
        with self.assertRaisesMessage(ValidationError, "неизменяем"):
            result.save()

    def test_second_publication_is_rejected_without_duplicates(self):
        batch = self.organization_batch("PUB-NEW-008")
        self.publish(batch)
        before = Employee.objects.filter(personnel_number="PUB-NEW-008").count()
        with self.assertRaisesMessage(ValidationError, "уже опубликована"):
            build_import_publication_preview(batch)
        self.assertEqual(
            Employee.objects.filter(personnel_number="PUB-NEW-008").count(),
            before,
        )

    def test_registry_drift_aborts_entire_publication(self):
        batch = self.organization_batch("PUB-NEW-009", "PUB-NEW-010")
        preview = build_import_publication_preview(batch)
        Employee.objects.create(
            organization=self.organization,
            division=self.division,
            position=self.position,
            personnel_number="PUB-NEW-010",
            last_name="Конфликт",
            first_name="Реестра",
            employment_start=date(2026, 1, 1),
        )
        before = Employee.objects.count()
        with self.assertRaisesMessage(ValidationError, "больше не готова"):
            publish_import_batch(
                batch=batch,
                actor=self.publisher,
                user=self.publisher_user,
                password=self.credential,
                expected_digest=preview.digest,
            )
        self.assertEqual(Employee.objects.count(), before)
        self.assertFalse(
            Employee.objects.filter(personnel_number="PUB-NEW-009").exists()
        )

    def test_equipment_publication_creates_asset_and_published_name(self):
        batch = self.equipment_batch("PUB-EQ-2")
        publication = self.publish(batch)
        asset = EquipmentAsset.objects.get(
            organization=self.organization,
            code="PUB-EQ-2",
        )
        revision = EquipmentNameRevision.objects.get(equipment=asset)
        self.assertEqual(revision.status, EquipmentPublicationStatus.PUBLISHED)
        self.assertEqual(len(revision.digest), 64)
        result = publication.published_rows.get()
        self.assertEqual(result.target_model, "equipment.EquipmentAsset")
        self.assertEqual(result.result["dispatcher_name_revision_id"], revision.pk)

    def test_management_publication_creates_published_revision(self):
        equipment = EquipmentAsset.objects.create(
            organization=self.organization,
            site=self.site,
            equipment_type=self.equipment_type,
            code="PUB-MGMT-EQ",
            technical_name="Оборудование управления",
        )
        batch = self.dispatching_batch(
            equipment_code=equipment.code,
            relation="Оперативное управление",
        )
        publication = self.publish(batch)
        revision = ManagementRevision.objects.get(
            management_object__equipment=equipment
        )
        self.assertEqual(revision.status, DispatchPublicationStatus.PUBLISHED)
        self.assertEqual(len(revision.digest), 64)
        self.assertEqual(
            publication.published_rows.get().target_model,
            "dispatching.ManagementRevision",
        )

    def test_supervision_publication_preserves_information_flag(self):
        equipment = EquipmentAsset.objects.create(
            organization=self.organization,
            site=self.site,
            equipment_type=self.equipment_type,
            code="PUB-SUP-EQ",
            technical_name="Оборудование ведения",
        )
        batch = self.dispatching_batch(
            equipment_code=equipment.code,
            relation="Оперативное ведение",
            information_only="Да",
        )
        self.publish(batch)
        revision = SupervisionRevision.objects.get(
            supervision_object__equipment=equipment
        )
        self.assertEqual(revision.status, DispatchPublicationStatus.PUBLISHED)
        self.assertTrue(revision.is_information_only)

    def test_published_batch_cannot_be_discarded(self):
        batch = self.organization_batch("PUB-NEW-011")
        self.publish(batch)
        batch.refresh_from_db()
        with self.assertRaisesMessage(ValidationError, "нельзя убрать"):
            discard_import_batch(batch=batch, employee=self.publisher)

    def test_published_batch_cannot_change_mapping_or_decisions(self):
        batch = self.organization_batch("PUB-NEW-012")
        self.publish(batch)
        batch.refresh_from_db()
        mapping = {
            column.position: column.mapped_key
            for column in batch.columns.order_by("position")
        }
        with self.assertRaisesMessage(ValidationError, "разобранной загрузки"):
            save_column_mapping(
                batch=batch,
                employee=self.publisher,
                mapping=mapping,
            )
        with self.assertRaisesMessage(ValidationError, "после разбора"):
            decide_import_row(
                row=batch.rows.get(),
                employee=self.publisher,
                action="RESET",
            )

    def test_preview_page_is_visible_but_confirmation_requires_role(self):
        batch = self.organization_batch("PUB-NEW-013")
        self.client.force_login(self.viewer_user)
        response = self.client.get(
            reverse("imports:publication", args=[batch.public_id])
        )
        self.assertContains(response, "Недостаточно полномочий")
        self.assertNotContains(response, 'name="password"')
        post = self.client.post(
            reverse("imports:publication", args=[batch.public_id]),
            {
                "preview_digest": build_import_publication_preview(batch).digest,
                "password": self.credential,
                "confirm": "on",
            },
        )
        self.assertEqual(post.status_code, 403)

    def test_publisher_view_reauthenticates_and_redirects_to_result(self):
        batch = self.organization_batch("PUB-NEW-014")
        preview = build_import_publication_preview(batch)
        self.client.force_login(self.publisher_user)
        response = self.client.get(
            reverse("imports:publication", args=[batch.public_id])
        )
        self.assertContains(response, "Опубликовать 1 принятых строк")
        response = self.client.post(
            reverse("imports:publication", args=[batch.public_id]),
            {
                "preview_digest": preview.digest,
                "password": self.credential,
                "confirm": "on",
            },
        )
        self.assertRedirects(
            response,
            reverse("imports:publication_result", args=[batch.public_id]),
        )
        result = self.client.get(
            reverse("imports:publication_result", args=[batch.public_id])
        )
        self.assertContains(result, "Неизменяемый итог публикации")
        self.assertContains(result, "PUB-NEW-014")

    def test_cross_organization_publication_is_hidden(self):
        other = Organization.objects.create(code="PUB-OTHER", name="Другая организация")
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
            file_sha256="a" * 64,
            status=ImportBatch.Status.READY,
        )
        self.client.force_login(self.publisher_user)
        response = self.client.get(
            reverse("imports:publication", args=[batch.public_id])
        )
        self.assertEqual(response.status_code, 404)

    def test_detail_and_list_show_publication_state(self):
        batch = self.organization_batch("PUB-NEW-015")
        self.publish(batch)
        self.client.force_login(self.publisher_user)
        detail = self.client.get(reverse("imports:detail", args=[batch.public_id]))
        self.assertContains(detail, "Принятые строки опубликованы транзакционно")
        self.assertContains(detail, "Итог публикации")
        listing = self.client.get(reverse("imports:list"))
        self.assertContains(listing, "Опубликованы")
        self.assertContains(listing, "Всего загрузок:")

    def test_publication_result_digest_is_bound_to_row(self):
        batch = self.organization_batch("PUB-NEW-016")
        publication = self.publish(batch)
        result = ImportPublicationRow.objects.get(publication=publication)
        self.assertEqual(len(result.digest), 64)
        self.assertEqual(result.row.batch, batch)
        self.assertEqual(result.target_model, "organizations.Employee")
