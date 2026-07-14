from datetime import date

from django.test import TestCase

from apps.organizations.models import (
    Employee,
    Position,
    ResponsibilityScope,
    Role,
    RoleAssignment,
    Substitution,
)
from apps.organizations.services import get_effective_roles, user_has_role

from .factories import employee_with_user


class EffectiveRoleTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator, cls.user = employee_with_user()
        cls.organization = cls.operator.organization
        cls.scope = ResponsibilityScope.objects.create(
            organization=cls.organization,
            code="STATION",
            name="Объект",
        )
        cls.operator_role = Role.objects.create(code="operator", name="Оператор")
        cls.supervisor_role = Role.objects.create(code="shift_supervisor", name="Начальник смены")
        RoleAssignment.objects.create(
            employee=cls.operator,
            role=cls.operator_role,
            scope=cls.scope,
            valid_from=date(2026, 1, 1),
        )
        supervisor_position = Position.objects.create(
            organization=cls.organization,
            code="SUPERVISOR",
            name="Начальник смены",
            is_operational=True,
        )
        cls.supervisor = Employee.objects.create(
            organization=cls.organization,
            division=cls.operator.division,
            position=supervisor_position,
            workplace=cls.operator.workplace,
            personnel_number="ORG-002",
            last_name="Сменов",
            first_name="Начальник",
            employment_start=date(2026, 1, 1),
        )
        RoleAssignment.objects.create(
            employee=cls.supervisor,
            role=cls.supervisor_role,
            scope=cls.scope,
            valid_from=date(2026, 1, 1),
        )

    def test_direct_role_is_effective(self):
        effective = get_effective_roles(self.operator, date(2026, 3, 1))
        self.assertEqual([item.assignment.role.code for item in effective], ["operator"])
        self.assertFalse(effective[0].is_substituted)

    def test_active_substitution_transfers_role(self):
        Substitution.objects.create(
            replaced_employee=self.supervisor,
            substitute_employee=self.operator,
            scope=self.scope,
            valid_from=date(2026, 2, 1),
            valid_until=date(2026, 4, 1),
            reason="Отпуск",
        )
        effective = get_effective_roles(self.operator, date(2026, 3, 1))
        by_code = {item.assignment.role.code: item for item in effective}
        self.assertIn("shift_supervisor", by_code)
        self.assertTrue(by_code["shift_supervisor"].is_substituted)
        self.assertEqual(by_code["shift_supervisor"].source_employee, self.supervisor)

    def test_expired_substitution_does_not_transfer_role(self):
        Substitution.objects.create(
            replaced_employee=self.supervisor,
            substitute_employee=self.operator,
            scope=self.scope,
            valid_from=date(2026, 1, 1),
            valid_until=date(2026, 1, 31),
            reason="Завершено",
        )
        codes = {
            item.assignment.role.code
            for item in get_effective_roles(self.operator, date(2026, 3, 1))
        }
        self.assertNotIn("shift_supervisor", codes)

    def test_scope_limited_substitution_does_not_transfer_other_scope(self):
        other_scope = ResponsibilityScope.objects.create(
            organization=self.organization,
            code="OTHER",
            name="Другая область",
        )
        other_role = Role.objects.create(code="other_role", name="Другая роль")
        RoleAssignment.objects.create(
            employee=self.supervisor,
            role=other_role,
            scope=other_scope,
            valid_from=date(2026, 1, 1),
        )
        Substitution.objects.create(
            replaced_employee=self.supervisor,
            substitute_employee=self.operator,
            scope=self.scope,
            valid_from=date(2026, 2, 1),
            valid_until=date(2026, 4, 1),
            reason="Ограниченное замещение",
        )
        codes = {
            item.assignment.role.code
            for item in get_effective_roles(self.operator, date(2026, 3, 1))
        }
        self.assertIn("shift_supervisor", codes)
        self.assertNotIn("other_role", codes)

    def test_user_has_role_uses_personal_employee_link(self):
        self.assertTrue(user_has_role(self.user, "operator", "STATION", date(2026, 3, 1)))
        self.assertFalse(user_has_role(self.user, "organization_admin", day=date(2026, 3, 1)))
