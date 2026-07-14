from datetime import date

from django.contrib.auth import get_user_model

from apps.organizations.models import Division, Employee, Organization, Position, Workplace


def organization_bundle(code: str = "ORG"):
    organization = Organization.objects.create(code=code, name=f"Организация {code}")
    division = Division.objects.create(organization=organization, code="OPS", name="Оперативная служба")
    workplace = Workplace.objects.create(
        organization=organization,
        division=division,
        code="ROOM",
        name="Щит управления",
    )
    position = Position.objects.create(
        organization=organization,
        code="OPERATOR",
        name="Оперативный работник",
        is_operational=True,
    )
    return organization, division, workplace, position


def employee_with_user(username: str = "operator.test", code: str = "ORG"):
    organization, division, workplace, position = organization_bundle(code)
    user = get_user_model().objects.create_user(username=username, password="TestPass!2026")
    employee = Employee.objects.create(
        organization=organization,
        division=division,
        position=position,
        workplace=workplace,
        user=user,
        personnel_number=f"{code}-001",
        last_name="Тестов",
        first_name="Оператор",
        employment_start=date(2026, 1, 1),
    )
    return employee, user
