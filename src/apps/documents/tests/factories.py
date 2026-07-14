from __future__ import annotations

from datetime import date

from apps.documents.models import DocumentType
from apps.organizations.models import ResponsibilityScope, Role, RoleAssignment
from apps.organizations.tests.factories import employee_with_user


def document_context(
    *,
    code: str = "DOC",
    role_code: str = "operator",
):
    employee, user = employee_with_user(
        username=f"{code.lower()}.user",
        code=code,
    )
    scope = ResponsibilityScope.objects.create(
        organization=employee.organization,
        code="STATION",
        name=f"Область {code}",
    )
    role, _ = Role.objects.get_or_create(
        code=role_code,
        defaults={
            "name": "Оперативный работник" if role_code == "operator" else role_code,
            "is_system": True,
            "is_active": True,
        },
    )
    RoleAssignment.objects.create(
        employee=employee,
        role=role,
        scope=scope,
        valid_from=date(2026, 1, 1),
    )
    document_type = DocumentType.objects.create(
        organization=employee.organization,
        code="general",
        name="Общий документ",
        number_prefix=code,
        number_width=6,
    )
    return employee, user, document_type
