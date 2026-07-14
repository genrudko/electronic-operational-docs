from datetime import date

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.test import TestCase

from apps.organizations.models import (
    Division,
    Employee,
    ResponsibilityScope,
    Role,
    RoleAssignment,
    Substitution,
)

from .factories import employee_with_user, organization_bundle


class OrganizationalModelTests(TestCase):
    def test_division_code_is_unique_inside_organization(self):
        organization, _, _, _ = organization_bundle()
        Division.objects.create(organization=organization, code="SECOND", name="Первое")
        with self.assertRaises(IntegrityError), transaction.atomic():
            Division.objects.create(organization=organization, code="SECOND", name="Второе")

    def test_division_parent_must_belong_to_same_organization(self):
        organization_a, division_a, _, _ = organization_bundle("A")
        _, division_b, _, _ = organization_bundle("B")
        candidate = Division(
            organization=organization_a,
            parent=division_b,
            code="CHILD",
            name="Дочернее",
        )
        with self.assertRaises(ValidationError):
            candidate.full_clean()

    def test_employee_links_must_belong_to_same_organization(self):
        organization_a, division_a, workplace_a, _ = organization_bundle("A")
        _, _, _, position_b = organization_bundle("B")
        employee = Employee(
            organization=organization_a,
            division=division_a,
            position=position_b,
            workplace=workplace_a,
            personnel_number="A-099",
            last_name="Тестов",
            first_name="Тест",
            employment_start=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            employee.full_clean()

    def test_one_personal_account_cannot_be_linked_to_two_employees(self):
        employee, user = employee_with_user()
        employee.user = user
        employee.save(update_fields=("user",))
        organization, division, workplace, position = organization_bundle("SECOND")
        duplicate = Employee(
            organization=organization,
            division=division,
            position=position,
            workplace=workplace,
            user=user,
            personnel_number="SECOND-001",
            last_name="Другой",
            first_name="Сотрудник",
            employment_start=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_role_assignment_rejects_invalid_date_window(self):
        employee, _ = employee_with_user()
        role = Role.objects.create(code="operator", name="Оператор")
        assignment = RoleAssignment(
            employee=employee,
            role=role,
            valid_from=date(2026, 2, 1),
            valid_until=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_role_assignment_scope_must_belong_to_employee_organization(self):
        employee, _ = employee_with_user(code="A")
        organization_b, _, _, _ = organization_bundle("B")
        scope = ResponsibilityScope.objects.create(
            organization=organization_b,
            code="B-SCOPE",
            name="Чужая область",
        )
        role = Role.objects.create(code="operator", name="Оператор")
        assignment = RoleAssignment(
            employee=employee,
            role=role,
            scope=scope,
            valid_from=date(2026, 1, 1),
        )
        with self.assertRaises(ValidationError):
            assignment.full_clean()

    def test_employee_cannot_substitute_self(self):
        employee, _ = employee_with_user()
        substitution = Substitution(
            replaced_employee=employee,
            substitute_employee=employee,
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 1, 2),
            reason="Ошибка",
        )
        with self.assertRaises(ValidationError):
            substitution.full_clean()

    def test_substitution_requires_same_organization(self):
        employee_a, _ = employee_with_user(username="a", code="A")
        employee_b, _ = employee_with_user(username="b", code="B")
        substitution = Substitution(
            replaced_employee=employee_a,
            substitute_employee=employee_b,
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 1, 2),
            reason="Ошибка",
        )
        with self.assertRaises(ValidationError):
            substitution.full_clean()
