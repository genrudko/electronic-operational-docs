from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.organizations.models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    OperationalRightDefinition,
    Organization,
    Position,
)
from apps.organizations.personnel_management_models import (
    EmployeeContactProfile,
    EmployeeSpecialQualification,
    ExternalOperationalContact,
    OrganizationOperationalProfile,
)
from tests.credential_fixtures import ephemeral_credential


class PersonnelAuthorityAcceptanceRepairTests(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        user_model = get_user_model()
        cls.user = user_model.objects.create_user(
            username="authority-repair-reviewer",
            password=ephemeral_credential("AuthorityRepairReviewer"),
        )
        cls.organization = Organization.objects.create(
            code="REPAIR-HOST",
            name="Синтетическая принимающая организация",
            short_name="REPAIR-HOST",
        )
        cls.division = Division.objects.create(
            organization=cls.organization,
            code="OPS",
            name="Участок оперативного обслуживания ВЭС",
        )
        cls.position = Position.objects.create(
            organization=cls.organization,
            code="SHIFT-SUPERVISOR",
            name="Начальник смены",
            is_operational=True,
        )
        cls.employee = Employee.objects.create(
            organization=cls.organization,
            division=cls.division,
            position=cls.position,
            personnel_number="REPAIR-001",
            last_name="Условный",
            first_name="Оператор",
            middle_name="Тестович",
            employment_start=date(2026, 1, 1),
        )
        EmployeeContactProfile.objects.create(
            employee=cls.employee,
            operational_phone="1001",
            availability_schedule="Круглосуточно",
            is_round_the_clock=True,
        )
        EmployeeQualification.objects.create(
            employee=cls.employee,
            personnel_category="ОП",
            electrical_safety_group="V",
            voltage_scope="до и выше 1000 В",
            electrical_installation_scope="Синтетическая оперативная область",
            valid_from=date(2026, 1, 1),
            source_reference="SYNTHETIC-MATRIX-R2",
            source_file_sha256="a" * 64,
            source_row_number=1,
        )
        EmployeeSpecialQualification.objects.create(
            employee=cls.employee,
            kind="RZA",
            level="IV",
            scope_text="Устройства РЗА до 330 кВ включительно",
            valid_from=date(2026, 1, 1),
            basis_reference="SYNTHETIC-RZA-LIST",
            source_file_sha256="b" * 64,
            source_row_number=1,
        )
        right_definition = OperationalRightDefinition.objects.get(
            code="switching_operation"
        )
        cls.conditional_right = EmployeeOperationalRight.objects.create(
            employee=cls.employee,
            right_definition=right_definition,
            qualifier="После выполнения требования пункта 5.4.",
            scope_text="Синтетическая оперативная область",
            source_marker="+1",
            source_reference="SYNTHETIC-MATRIX-R2",
            source_file_sha256="c" * 64,
            source_row_number=1,
            valid_from=date(2026, 1, 1),
        )

        cls.dispatch_organization = Organization.objects.create(
            code="REPAIR-RDU",
            name="Синтетический диспетчерский центр",
            short_name="РДУ — тест",
        )
        OrganizationOperationalProfile.objects.create(
            organization=cls.dispatch_organization,
            relation_kind="DISPATCH_CENTER",
            directory_scope="Руководство и диспетчерский персонал",
        )
        dispatch_division = Division.objects.create(
            organization=cls.dispatch_organization,
            code="ODS",
            name="Оперативно-диспетчерская служба",
        )
        dispatch_position = Position.objects.create(
            organization=cls.dispatch_organization,
            code="DISPATCHER",
            name="Диспетчер",
            is_operational=True,
        )
        cls.dispatcher = Employee.objects.create(
            organization=cls.dispatch_organization,
            division=dispatch_division,
            position=dispatch_position,
            personnel_number="REPAIR-EXT-001",
            last_name="Диспетчерский",
            first_name="Контакт",
            middle_name="Тестович",
            employment_start=date(2026, 1, 1),
        )
        EmployeeContactProfile.objects.create(
            employee=cls.dispatcher,
            operational_phone="2002",
            is_round_the_clock=True,
        )
        ExternalOperationalContact.objects.create(
            employee=cls.dispatcher,
            host_organization=cls.organization,
            relation_kind="DISPATCH",
            operational_scope="Диспетчерское управление синтетическим объектом",
            authority_summary="Оперативные переговоры и диспетчерские команды",
            valid_from=date(2026, 1, 1),
            basis_reference="SYNTHETIC-RDU-LIST",
        )

    def setUp(self) -> None:
        self.client.force_login(self.user)

    def test_matrix_shows_exact_condition_integrated_legend_and_rza(self) -> None:
        response = self.client.get(
            reverse("organizations:authority_registry"),
            {"organization": self.organization.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Условие по п. 5.4")
        self.assertContains(response, "приказом Минтруда России от 15.12.2020 № 903н")
        self.assertContains(response, "Категория допуска по РЗА: IV")
        self.assertContains(response, "icon-org-operations")
        self.assertContains(response, "category-op")
        self.assertNotContains(response, "<summary>Обозначения и сокращения</summary>")

    def test_employee_card_explains_condition_and_rza_scope(self) -> None:
        response = self.client.get(
            reverse(
                "organizations:employee_detail",
                kwargs={"public_id": self.employee.public_id},
            )
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Предоставлено с условием +1")
        self.assertContains(response, "пункт 5.4")
        self.assertContains(response, "Категория допуска по РЗА — IV")
        self.assertContains(response, "Устройства РЗА до 330 кВ включительно")

    def test_dispatch_directory_is_separate_from_contractors(self) -> None:
        response = self.client.get(
            reverse("organizations:authority_registry"),
            {"organization": self.organization.code},
        )

        self.assertContains(response, "ОДУ и РДУ")
        self.assertContains(response, "РДУ — тест")
        self.assertContains(response, self.dispatcher.full_name)
        self.assertContains(response, "Оперативные переговоры и диспетчерские команды")
        self.assertContains(response, "Подрядный персонал")

    def test_organization_page_is_direction_a_management_workspace(self) -> None:
        response = self.client.get(
            reverse("organizations:directory"),
            {"organization": self.organization.code},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "data-direction-a-shell")
        self.assertContains(response, "Рабочий центр ведения структуры")
        self.assertContains(response, "Добавить сотрудника")
        self.assertContains(response, "Импорт из XLSX")
        self.assertContains(response, "Иерархия подразделений")
        self.assertContains(response, "Внешние оперативные контакты")
        self.assertContains(response, self.dispatcher.full_name)

    def test_manual_catalog_values_create_employee_without_empty_selects(self) -> None:
        response = self.client.get(reverse("organizations:employee_create"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.division.name)
        self.assertContains(response, self.position.name)
        self.assertContains(response, "Новое подразделение")
        self.assertContains(response, "Новая должность")
        self.assertContains(response, "Новое рабочее место")

        create_response = self.client.post(
            reverse("organizations:employee_create"),
            {
                "employee-organization": str(self.organization.id),
                "employee-division": "",
                "employee-position": "",
                "employee-workplace": "",
                "employee-new_division_name": "Новая оперативная группа",
                "employee-new_position_name": "Дежурный инженер",
                "employee-new_workplace_name": "Диспетчерский пункт",
                "employee-personnel_number": "REPAIR-MANUAL-001",
                "employee-last_name": "Ручной",
                "employee-first_name": "Сотрудник",
                "employee-middle_name": "Тестович",
                "employee-employment_start": "2026-01-01",
                "employee-employment_end": "",
                "employee-is_active": "on",
                "employee-change_reason": "Ручное ведение справочника",
                "contact-primary_phone": "3003",
                "contact-operational_phone": "3004",
                "contact-email": "manual@example.test",
                "contact-availability_schedule": "Рабочие дни",
                "contact-note": "Синтетическая карточка",
            },
        )

        self.assertEqual(create_response.status_code, 302)
        employee = Employee.objects.get(
            organization=self.organization,
            personnel_number="REPAIR-MANUAL-001",
        )
        self.assertEqual(employee.division.name, "Новая оперативная группа")
        self.assertEqual(employee.position.name, "Дежурный инженер")
        self.assertEqual(employee.workplace.name, "Диспетчерский пункт")
