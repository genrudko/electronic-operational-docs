from __future__ import annotations

from datetime import date, datetime

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.documents.models import Document, DocumentType
from apps.equipment.models import EnergySite, EquipmentAsset, EquipmentType
from apps.organizations.models import (
    Division,
    Employee,
    Organization,
    Position,
    Role,
    RoleAssignment,
    Workplace,
)

from ..forms import OperationalFieldDefinitionFormSet, field_definitions_from_formset
from ..models import (
    OperationalDocumentAuditEvent,
    OperationalDocumentRecord,
    OperationalDocumentRecordRevision,
    OperationalDocumentTypeRevision,
    SchemaPublicationStatus,
)
from ..services import (
    create_and_publish_type,
    create_record,
    current_published_revision,
    transition_record,
    update_record,
)


class OperationalDocumentCoreTests(TestCase):
    password = "StrongPass!2026"

    @classmethod
    def setUpTestData(cls) -> None:
        cls.organization = Organization.objects.create(code="ORG", name="Тестовая ВЭС")
        cls.division = Division.objects.create(
            organization=cls.organization,
            code="OPS",
            name="Оперативная служба",
        )
        cls.workplace = Workplace.objects.create(
            organization=cls.organization,
            division=cls.division,
            code="CONTROL_ROOM",
            name="Главный щит управления",
        )
        cls.position = Position.objects.create(
            organization=cls.organization,
            code="SHIFT_SUPERVISOR",
            name="Начальник смены",
            is_operational=True,
        )
        cls.user = get_user_model().objects.create_user(
            username="shift.supervisor",
            password=cls.password,
            is_superuser=True,
            is_staff=True,
        )
        cls.employee = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            workplace=cls.workplace,
            user=cls.user,
            personnel_number="ORG-001",
            last_name="Орлов",
            first_name="Алексей",
            middle_name="Игоревич",
            employment_start=date(2026, 1, 1),
        )
        cls.performer_user = get_user_model().objects.create_user(
            username="operator",
            password=cls.password,
        )
        cls.performer = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            workplace=cls.workplace,
            user=cls.performer_user,
            personnel_number="ORG-002",
            last_name="Петров",
            first_name="Пётр",
            middle_name="Сергеевич",
            employment_start=date(2026, 1, 1),
        )
        role = Role.objects.create(
            code="shift_supervisor",
            name="Начальник смены",
            is_system=True,
        )
        RoleAssignment.objects.create(
            employee=cls.employee,
            role=role,
            valid_from=date(2026, 1, 1),
        )

        cls.site = EnergySite.objects.create(
            organization=cls.organization,
            code="kves",
            name="Кочубеевская ВЭС",
            short_name="КВЭС",
            site_type=EnergySite.SiteType.WIND_POWER_PLANT,
        )
        cls.equipment_type = EquipmentType.objects.create(
            code="test-switchgear-opdoc",
            name="Испытательное распределительное устройство",
            category=EquipmentType.Category.SWITCHGEAR,
        )
        cls.equipment = EquipmentAsset.objects.create(
            organization=cls.organization,
            site=cls.site,
            equipment_type=cls.equipment_type,
            code="РУ-35",
            technical_name="Распределительное устройство 35 кВ",
        )
        cls.document_type = DocumentType.objects.create(
            organization=cls.organization,
            code="basis-opdoc",
            name="Документ-основание",
            number_prefix="ОСН",
            number_width=4,
        )
        cls.document = Document.objects.create(
            organization=cls.organization,
            document_type=cls.document_type,
            title="Основание для выполнения работы",
            status=Document.Status.REGISTERED,
            created_by=cls.employee,
            registration_year=2026,
            sequence_number=1,
            registration_number="ОСН-2026-0001",
            registered_at=timezone.now(),
            registered_by=cls.employee,
        )

        cls.foreign_organization = Organization.objects.create(code="OTHER", name="Другая организация")
        cls.foreign_division = Division.objects.create(
            organization=cls.foreign_organization,
            code="OPS",
            name="Другое подразделение",
        )
        cls.foreign_position = Position.objects.create(
            organization=cls.foreign_organization,
            code="OPERATOR",
            name="Оператор",
            is_operational=True,
        )
        cls.foreign_workplace = Workplace.objects.create(
            organization=cls.foreign_organization,
            division=cls.foreign_division,
            code="ROOM",
            name="Чужое рабочее место",
        )
        cls.foreign_user = get_user_model().objects.create_user(
            username="foreign.operator",
            password=cls.password,
        )
        cls.foreign_employee = Employee.objects.create(
            organization=cls.foreign_organization,
            division=cls.foreign_division,
            position=cls.foreign_position,
            workplace=cls.foreign_workplace,
            user=cls.foreign_user,
            personnel_number="OTHER-001",
            last_name="Иванов",
            first_name="Иван",
            employment_start=date(2026, 1, 1),
        )
        cls.foreign_site = EnergySite.objects.create(
            organization=cls.foreign_organization,
            code="other-site",
            name="Другой объект",
            site_type=EnergySite.SiteType.OTHER,
        )
        cls.foreign_equipment = EquipmentAsset.objects.create(
            organization=cls.foreign_organization,
            site=cls.foreign_site,
            equipment_type=cls.equipment_type,
            code="FOREIGN-1",
            technical_name="Чужое оборудование",
        )

    def setUp(self) -> None:
        self.document_type_core = create_and_publish_type(
            actor=self.employee,
            code="journal-equipment-defects",
            name="Карточка дефекта",
            short_name="Дефект",
            description="Тестовый тип общего ядра",
            number_prefix="ДЕФ",
            number_width=4,
            requires_workplace=True,
            field_definitions=[
                {
                    "code": "DESCRIPTION",
                    "label": "Описание дефекта",
                    "type": "LONG_TEXT",
                    "required": True,
                    "show_in_list": True,
                    "searchable": True,
                },
                {
                    "code": "PRIORITY",
                    "label": "Приоритет",
                    "type": "CHOICE",
                    "required": True,
                    "show_in_list": True,
                    "searchable": True,
                    "choices": [
                        {"value": "NORMAL", "label": "Обычный"},
                        {"value": "HIGH", "label": "Высокий"},
                    ],
                },
                {
                    "code": "REMOTE",
                    "label": "Удалённое выполнение",
                    "type": "BOOLEAN",
                    "required": False,
                    "show_in_list": False,
                    "searchable": False,
                },
            ],
        )
        self.revision = current_published_revision(self.document_type_core)
        assert self.revision is not None

    def event_time(self, minute: int = 0):
        return timezone.make_aware(datetime(2026, 7, 23, 12, minute))

    def create_test_record(self, *, title: str = "Повышенная температура", minute: int = 0):
        return create_record(
            revision=self.revision,
            actor=self.employee,
            title=title,
            summary="Требуется осмотр оборудования",
            event_at=self.event_time(minute),
            workplace=self.workplace,
            field_values={
                "DESCRIPTION": "Нагрев контактного соединения",
                "PRIORITY": "HIGH",
                "REMOTE": None,
            },
            participant_map={
                "RESPONSIBLE": [self.employee],
                "PERFORMER": [self.performer],
            },
            equipment_assets=[self.equipment],
            documents=[self.document],
        )

    def test_published_type_revision_has_canonical_hash_and_is_immutable(self) -> None:
        self.assertEqual(self.revision.status, SchemaPublicationStatus.PUBLISHED)
        self.assertEqual(len(self.revision.sha256), 64)
        self.assertEqual(
            self.revision.canonical_snapshot["schema"],
            "eod.operational-document-type.v1",
        )
        self.revision.number_prefix = "ИЗМ"
        with self.assertRaisesMessage(ValidationError, "неизменяема"):
            self.revision.save()
        with self.assertRaisesMessage(ValidationError, "Массовое изменение"):
            OperationalDocumentTypeRevision.objects.filter(pk=self.revision.pk).update(
                number_prefix="ИЗМ"
            )

    def test_record_number_snapshots_links_revision_and_audit_are_created(self) -> None:
        record = self.create_test_record()
        self.assertEqual(record.registration_number, "ДЕФ-2026-0001")
        self.assertEqual(record.status_code, "OPEN")
        self.assertEqual(record.workplace_name_snapshot, self.workplace.name)
        self.assertEqual(record.field_values["PRIORITY"]["display"], "Высокий")
        self.assertIsNone(record.field_values["REMOTE"]["value"])
        self.assertEqual(record.participants.count(), 2)
        self.assertEqual(record.equipment_links.count(), 1)
        self.assertEqual(record.document_links.count(), 1)
        revision = record.revisions.get(revision_number=1)
        self.assertEqual(len(revision.sha256), 64)
        self.assertEqual(
            revision.snapshot["record"]["workplace"]["code"],
            self.workplace.code,
        )
        self.assertTrue(record.audit_events.filter(event_type="RECORD_CREATED").exists())

    def test_server_numbering_increments_per_type_and_year(self) -> None:
        first = self.create_test_record(minute=1)
        second = self.create_test_record(title="Второй дефект", minute=2)
        self.assertEqual(first.sequence_value, 1)
        self.assertEqual(second.sequence_value, 2)
        self.assertEqual(second.registration_number, "ДЕФ-2026-0002")

    def test_update_creates_new_immutable_revision_and_preserves_first_snapshot(self) -> None:
        record = self.create_test_record()
        first_snapshot = record.revisions.get(revision_number=1).snapshot
        updated = update_record(
            record=record,
            actor=self.employee,
            title="Температура подтверждена повторно",
            summary="Осмотр выполнен",
            event_at=self.event_time(5),
            workplace=self.workplace,
            field_values={
                "DESCRIPTION": "Нагрев подтверждён тепловизором",
                "PRIORITY": "HIGH",
                "REMOTE": False,
            },
            participant_map={
                "RESPONSIBLE": [self.employee],
                "PERFORMER": [self.performer],
            },
            equipment_assets=[self.equipment],
            documents=[self.document],
            comment="Уточнение после осмотра",
        )
        self.assertEqual(updated.version, 2)
        self.assertEqual(updated.revisions.count(), 2)
        self.assertEqual(
            first_snapshot["record"]["title"],
            "Повышенная температура",
        )
        second = updated.revisions.get(revision_number=2)
        self.assertEqual(second.comment, "Уточнение после осмотра")
        second.comment = "Попытка изменения"
        with self.assertRaisesMessage(ValidationError, "неизменяема"):
            second.save()

    def test_transition_requires_comment_and_terminal_record_is_locked(self) -> None:
        record = self.create_test_record()
        with self.assertRaisesMessage(ValidationError, "требуется комментарий"):
            transition_record(
                record=record,
                actor=self.employee,
                transition_code="CLOSE_OPEN",
            )
        closed = transition_record(
            record=record,
            actor=self.employee,
            transition_code="CLOSE_OPEN",
            comment="Дефект устранён",
        )
        self.assertEqual(closed.status_code, "CLOSED")
        self.assertTrue(closed.status_is_terminal)
        self.assertIsNotNone(closed.closed_at)
        self.assertEqual(closed.version, 2)
        with self.assertRaisesMessage(ValidationError, "нельзя редактировать"):
            update_record(
                record=closed,
                actor=self.employee,
                title=closed.title,
                summary=closed.summary,
                event_at=closed.event_at,
                workplace=closed.workplace,
                field_values={
                    "DESCRIPTION": "Новая попытка",
                    "PRIORITY": "NORMAL",
                    "REMOTE": None,
                },
                participant_map={"RESPONSIBLE": [], "PERFORMER": []},
            )

    def test_cross_organization_equipment_and_participant_are_rejected(self) -> None:
        with self.assertRaisesMessage(ValidationError, "другой организации"):
            create_record(
                revision=self.revision,
                actor=self.employee,
                title="Недопустимая связь",
                summary="",
                event_at=self.event_time(),
                workplace=self.workplace,
                field_values={
                    "DESCRIPTION": "Тест",
                    "PRIORITY": "NORMAL",
                    "REMOTE": None,
                },
                participant_map={
                    "RESPONSIBLE": [self.foreign_employee],
                    "PERFORMER": [],
                },
                equipment_assets=[self.foreign_equipment],
            )
        self.assertEqual(OperationalDocumentRecord.objects.count(), 0)

    def test_physical_delete_and_bulk_update_are_forbidden(self) -> None:
        record = self.create_test_record()
        with self.assertRaisesMessage(ValidationError, "Физическое удаление"):
            record.delete()
        with self.assertRaisesMessage(ValidationError, "Массовое изменение"):
            OperationalDocumentRecord.objects.filter(pk=record.pk).update(title="Подмена")
        with self.assertRaisesMessage(ValidationError, "Физическое удаление"):
            OperationalDocumentAuditEvent.objects.filter(record=record).delete()
        with self.assertRaisesMessage(ValidationError, "Физическое удаление"):
            OperationalDocumentRecordRevision.objects.filter(record=record).delete()

    def test_common_registry_search_and_filters_show_only_own_organization(self) -> None:
        record = self.create_test_record()
        self.client.force_login(self.user)
        self.assertIn("нагрев", record.search_text)
        self.assertNotIn("Нагрев", record.search_text)
        response = self.client.get(
            reverse("operational_documents:registry"),
            {
                "q": "НАГРЕВ",
                "equipment": str(self.equipment.public_id),
                "workplace": self.workplace.code,
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, record.registration_number)
        self.assertContains(response, "Повышенная температура")
        response = self.client.get(
            reverse("operational_documents:registry"),
            {"q": "отсутствующий текст"},
        )
        self.assertNotContains(response, record.registration_number)

    def test_manual_type_builder_is_disabled_and_catalog_is_source_bound(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_documents:type_create"), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Ручное создание форм отключено")
        self.assertContains(response, "И-00-007-ОР-2025 версия 2")
        self.assertContains(response, "Приложение № 8")
        self.assertNotContains(response, "Создать тип")

    def test_browser_default_field_type_does_not_activate_empty_form(self) -> None:
        payload = {
            "fields-TOTAL_FORMS": "3",
            "fields-INITIAL_FORMS": "0",
            "fields-MIN_NUM_FORMS": "1",
            "fields-MAX_NUM_FORMS": "12",
            "fields-0-label": "Содержание",
            "fields-0-code": "CONTENT",
            "fields-0-field_type": "LONG_TEXT",
            "fields-0-required": "on",
            "fields-0-show_in_list": "on",
            "fields-0-searchable": "on",
            "fields-0-choice_options": "",
            "fields-0-help_text": "",
            "fields-1-label": "",
            "fields-1-code": "",
            "fields-1-field_type": "TEXT",
            "fields-1-choice_options": "",
            "fields-1-help_text": "",
            "fields-2-label": "",
            "fields-2-code": "",
            "fields-2-field_type": "TEXT",
            "fields-2-choice_options": "",
            "fields-2-help_text": "",
        }
        formset = OperationalFieldDefinitionFormSet(payload, prefix="fields")
        self.assertTrue(formset.is_valid(), formset.errors)
        definitions = field_definitions_from_formset(formset)
        self.assertEqual([item["code"] for item in definitions], ["CONTENT"])

    def test_record_detail_route_exposes_links_history_and_transitions(self) -> None:
        record = self.create_test_record()
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("operational_documents:record_detail", args=[record.public_id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, record.registration_number)
        self.assertContains(response, "Нагрев контактного соединения")
        self.assertContains(response, self.equipment.technical_name)
        self.assertContains(response, "Принять в работу")
        self.assertContains(response, "История редакций")
        self.assertContains(response, "И-00-007-ОР-2025 версия 2")
        self.assertNotContains(response, "Append-only аудит")
