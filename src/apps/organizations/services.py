from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from django.db.models import Q
from django.utils import timezone

from .models import Employee, RoleAssignment, Substitution


@dataclass(frozen=True, slots=True)
class EffectiveRole:
    assignment: RoleAssignment
    source_employee: Employee
    substitution: Substitution | None = None

    @property
    def is_substituted(self) -> bool:
        return self.substitution is not None


def _active_assignments(employee: Employee, day: date):
    return (
        RoleAssignment.objects.select_related("role", "scope", "employee")
        .filter(employee=employee, is_active=True, valid_from__lte=day)
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=day))
    )


def get_effective_roles(employee: Employee, day: date | None = None) -> list[EffectiveRole]:
    current = day or timezone.localdate()
    effective: list[EffectiveRole] = [
        EffectiveRole(assignment=assignment, source_employee=employee)
        for assignment in _active_assignments(employee, current)
    ]

    substitutions = (
        Substitution.objects.select_related(
            "replaced_employee",
            "substitute_employee",
            "scope",
        )
        .filter(
            substitute_employee=employee,
            is_active=True,
            valid_from__lte=current,
            valid_until__gte=current,
        )
    )
    for substitution in substitutions:
        assignments = _active_assignments(substitution.replaced_employee, current)
        if substitution.scope_id:
            assignments = assignments.filter(scope_id=substitution.scope_id)
        effective.extend(
            EffectiveRole(
                assignment=assignment,
                source_employee=substitution.replaced_employee,
                substitution=substitution,
            )
            for assignment in assignments
        )

    unique: dict[tuple[int, int | None], EffectiveRole] = {}
    for item in effective:
        key = (item.assignment.pk, item.substitution.pk if item.substitution else None)
        unique[key] = item
    return sorted(
        unique.values(),
        key=lambda item: (
            item.assignment.role.name,
            item.assignment.scope.name if item.assignment.scope else "",
            item.is_substituted,
        ),
    )


def user_has_role(
    user,
    role_code: str,
    scope_code: str | None = None,
    day: date | None = None,
) -> bool:
    employee = getattr(user, "employee_profile", None)
    if employee is None or not employee.is_active:
        return False
    for effective in get_effective_roles(employee, day):
        if effective.assignment.role.code != role_code:
            continue
        if scope_code is None:
            return True
        if effective.assignment.scope and effective.assignment.scope.code == scope_code:
            return True
    return False
