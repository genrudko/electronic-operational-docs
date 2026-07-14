from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import (
    Division,
    Employee,
    OperationalArea,
    Organization,
    Position,
    ResponsibilityScope,
    Role,
    RoleAssignment,
    Substitution,
    Workplace,
)

DEMO_PASSWORD = "EodDemo!2026"


class Command(BaseCommand):
    help = "Создаёт обезличенную демонстрационную организацию и персональные тестовые учётные записи."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help="Установить демонстрационный пароль заново.",
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        organization, _ = Organization.objects.update_or_create(
            code="DEMO",
            defaults={
                "name": "Демонстрационный энергообъект",
                "short_name": "ДЕМО-ЭО",
                "is_active": True,
            },
        )
        division, _ = Division.objects.update_or_create(
            organization=organization,
            code="OPS",
            defaults={"name": "Оперативная служба", "is_active": True},
        )
        workplace, _ = Workplace.objects.update_or_create(
            organization=organization,
            code="CONTROL_ROOM",
            defaults={
                "division": division,
                "name": "Главный щит управления",
                "is_active": True,
            },
        )
        area, _ = OperationalArea.objects.update_or_create(
            organization=organization,
            code="STATION",
            defaults={
                "division": division,
                "name": "Электроустановки демонстрационного объекта",
                "is_active": True,
            },
        )
        area.workplaces.set([workplace])
        operator_position, _ = Position.objects.update_or_create(
            organization=organization,
            code="OPERATOR",
            defaults={
                "name": "Оперативный работник",
                "is_operational": True,
                "is_active": True,
            },
        )
        supervisor_position, _ = Position.objects.update_or_create(
            organization=organization,
            code="SHIFT_SUPERVISOR",
            defaults={
                "name": "Начальник смены",
                "is_operational": True,
                "is_active": True,
            },
        )
        scope, _ = ResponsibilityScope.objects.update_or_create(
            organization=organization,
            code="STATION",
            defaults={
                "operational_area": area,
                "name": "Демонстрационный объект целиком",
                "is_active": True,
            },
        )

        roles = {}
        for code, name, description in (
            ("operator", "Оперативный работник", "Ведение оперативной документации."),
            ("shift_supervisor", "Начальник смены", "Контроль смены и подтверждение действий."),
            ("organization_admin", "Администратор справочников", "Настройка организационных справочников."),
        ):
            roles[code], _ = Role.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "description": description,
                    "is_system": True,
                    "is_active": True,
                },
            )

        user_model = get_user_model()
        operator_user = self._user(
            user_model,
            username="operator.demo",
            first_name="Алексей",
            last_name="Операторов",
            reset_password=options["reset_passwords"],
        )
        supervisor_user = self._user(
            user_model,
            username="supervisor.demo",
            first_name="Марина",
            last_name="Сменова",
            reset_password=options["reset_passwords"],
        )

        operator, _ = Employee.objects.update_or_create(
            organization=organization,
            personnel_number="DEMO-001",
            defaults={
                "division": division,
                "position": operator_position,
                "workplace": workplace,
                "user": operator_user,
                "last_name": "Операторов",
                "first_name": "Алексей",
                "middle_name": "Демонстрационный",
                "employment_start": date(2026, 1, 1),
                "employment_end": None,
                "is_active": True,
            },
        )
        supervisor, _ = Employee.objects.update_or_create(
            organization=organization,
            personnel_number="DEMO-002",
            defaults={
                "division": division,
                "position": supervisor_position,
                "workplace": workplace,
                "user": supervisor_user,
                "last_name": "Сменова",
                "first_name": "Марина",
                "middle_name": "Демонстрационная",
                "employment_start": date(2026, 1, 1),
                "employment_end": None,
                "is_active": True,
            },
        )

        assignment_start = date(2026, 1, 1)
        RoleAssignment.objects.update_or_create(
            employee=operator,
            role=roles["operator"],
            scope=scope,
            valid_from=assignment_start,
            defaults={"valid_until": None, "is_active": True},
        )
        RoleAssignment.objects.update_or_create(
            employee=supervisor,
            role=roles["shift_supervisor"],
            scope=scope,
            valid_from=assignment_start,
            defaults={"valid_until": None, "is_active": True},
        )
        RoleAssignment.objects.update_or_create(
            employee=supervisor,
            role=roles["operator"],
            scope=scope,
            valid_from=assignment_start,
            defaults={"valid_until": None, "is_active": True},
        )

        today = timezone.localdate()
        Substitution.objects.update_or_create(
            replaced_employee=supervisor,
            substitute_employee=operator,
            scope=scope,
            defaults={
                "valid_from": today - timedelta(days=1),
                "valid_until": today + timedelta(days=7),
                "reason": "Демонстрационное временное замещение",
                "is_active": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Демонстрационная организация создана или обновлена."))
        self.stdout.write("Персональные тестовые учётные записи:")
        self.stdout.write(f"  operator.demo / {DEMO_PASSWORD}")
        self.stdout.write(f"  supervisor.demo / {DEMO_PASSWORD}")
        self.stdout.write("Данные являются вымышленными и предназначены только для локального прототипа.")

    def _user(self, user_model, *, username: str, first_name: str, last_name: str, reset_password: bool):
        user, created = user_model.objects.get_or_create(username=username)
        user.first_name = first_name
        user.last_name = last_name
        user.email = f"{username}@example.invalid"
        user.is_active = True
        user.is_staff = False
        if created or reset_password or not user.has_usable_password():
            user.set_password(DEMO_PASSWORD)
        user.save()
        return user
