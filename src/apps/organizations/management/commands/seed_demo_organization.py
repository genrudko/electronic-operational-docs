from __future__ import annotations

from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.organizations.demo_access import (
    DEMO_ACCESS_ENV,
    DemoAccessPolicyError,
    reconcile_demo_access,
)
from apps.organizations.models import (
    Division,
    Employee,
    InterfacePreference,
    OperationalArea,
    Organization,
    Position,
    ResponsibilityScope,
    Role,
    RoleAssignment,
    Substitution,
    Workplace,
)


class Command(BaseCommand):
    help = "Создаёт безопасную презентационную структуру ЦОТУиЭ и вымышленных сотрудников."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--reset-passwords",
            action="store_true",
            help=(
                "Совместимый флаг: доступ всегда настраивается только через "
                f"{DEMO_ACCESS_ENV}."
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        organization, _ = Organization.objects.update_or_create(
            code="DEMO",
            defaults={
                "name": "АО «Росатом Возобновляемая энергия» — презентационный контур",
                "short_name": "АО «Росатом Возобновляемая энергия»",
                "is_active": True,
            },
        )

        divisions: dict[str, Division] = {}

        def division(code: str, name: str, parent: str | None = None) -> Division:
            item, _ = Division.objects.update_or_create(
                organization=organization,
                code=code,
                defaults={
                    "name": name,
                    "parent": divisions.get(parent) if parent else None,
                    "is_active": True,
                },
            )
            divisions[code] = item
            return item

        division("CHIEF_ENGINEER_BLOCK", "Блок ЗГД — главного инженера")
        division(
            "CENTER",
            "ЦОТУиЭ ВЭС Невинномысск",
            "CHIEF_ENGINEER_BLOCK",
        )
        division("RZA", "Группа ТОиР РЗиА", "CENTER")
        division("WTG_SERVICE", "Участок ТОиР ветроэнергетических установок", "CENTER")
        division("TECHNICAL", "Технический отдел", "CENTER")
        division("ASUTP", "Группа ТОиР АСУ ТП", "CENTER")
        division("OPS", "Участок оперативного обслуживания ВЭС", "CENTER")
        division("ELECTRICAL", "Участок ТОиР электротехнического оборудования", "CENTER")
        division(
            "BLADE_SERVICE",
            "Участок ТОиР лопастей ВЭУ",
            "CHIEF_ENGINEER_BLOCK",
        )

        workplaces: dict[str, Workplace] = {}

        def workplace(code: str, name: str, division_code: str) -> Workplace:
            item, _ = Workplace.objects.update_or_create(
                organization=organization,
                code=code,
                defaults={
                    "division": divisions[division_code],
                    "name": name,
                    "is_active": True,
                },
            )
            workplaces[code] = item
            return item

        workplace(
            "SHIFT_POOL",
            "Сменный персонал ЦОТУиЭ ВЭС Невинномысск",
            "OPS",
        )
        workplace(
            "KOCH_CONTROL_ROOM",
            "Главный щит управления Кочубеевской ВЭС",
            "OPS",
        )
        workplace(
            "KUZ_CONTROL_ROOM",
            "Главный щит управления Кузьминской ВЭС",
            "OPS",
        )
        workplace(
            "BARSUKI_OPERATIONAL_POINT",
            "Оперативный пункт ПС 330 кВ Барсуки",
            "OPS",
        )
        workplace(
            "NEVIN_BLADE_BASE",
            "Территориальная база участка ТОиР лопастей ВЭУ",
            "BLADE_SERVICE",
        )

        areas: dict[str, OperationalArea] = {}

        def operational_area(code: str, name: str, workplace_code: str) -> OperationalArea:
            item, _ = OperationalArea.objects.update_or_create(
                organization=organization,
                code=code,
                defaults={
                    "division": divisions["OPS"],
                    "name": name,
                    "is_active": True,
                },
            )
            item.workplaces.set([workplaces[workplace_code]])
            areas[code] = item
            return item

        operational_area("KOCH", "Кочубеевская ВЭС", "KOCH_CONTROL_ROOM")
        operational_area("KUZ", "Кузьминская ВЭС", "KUZ_CONTROL_ROOM")
        operational_area("BARSUKI", "ПС 330 кВ Барсуки", "BARSUKI_OPERATIONAL_POINT")

        positions: dict[str, Position] = {}

        def position(code: str, name: str, *, operational: bool = False) -> Position:
            item, _ = Position.objects.update_or_create(
                organization=organization,
                code=code,
                defaults={
                    "name": name,
                    "is_operational": operational,
                    "is_active": True,
                },
            )
            positions[code] = item
            return item

        position("TECHNICAL_DIRECTOR", "Технический директор")
        position(
            "DEPUTY_OPERATIONS",
            "Заместитель технического директора по оперативной работе",
            operational=True,
        )
        position("DEPUTY_REPAIRS", "Заместитель технического директора по ремонту")
        position("SHIFT_SUPERVISOR", "Начальник смены", operational=True)
        position("DUTY_ELECTRICIAN", "Электромонтёр", operational=True)
        position("LEAD_ENGINEER", "Ведущий инженер")
        position("ENGINEER", "Инженер")
        position("DEPARTMENT_HEAD", "Начальник отдела")
        position("SITE_HEAD", "Начальник участка")
        position("LEAD_WTG_SERVICE_ENGINEER", "Ведущий инженер по сервису ВЭУ")
        position("WTG_SERVICE_ENGINEER", "Инженер по сервису ВЭУ")
        position("WTG_REPAIR_TECHNICIAN", "Техник по ремонту ВЭУ")
        position("LEAD_SPECIALIST", "Ведущий специалист")
        position("CHIEF_SPECIALIST", "Главный специалист")
        position("EQUIPMENT_REPAIR_ELECTRICIAN", "Электромонтёр по ремонту оборудования")
        position("REPAIR_TECHNICIAN", "Техник по ремонту и обслуживанию")

        scopes: dict[str, ResponsibilityScope] = {}
        for code, name, area_code in (
            ("ALL_SITES", "Энергообъекты ЦОТУиЭ ВЭС Невинномысск", None),
            ("KOCH", "Кочубеевская ВЭС", "KOCH"),
            ("KUZ", "Кузьминская ВЭС", "KUZ"),
            ("BARSUKI", "ПС 330 кВ Барсуки", "BARSUKI"),
        ):
            scopes[code], _ = ResponsibilityScope.objects.update_or_create(
                organization=organization,
                code=code,
                defaults={
                    "operational_area": areas.get(area_code),
                    "name": name,
                    "is_active": True,
                },
            )

        roles: dict[str, Role] = {}
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
            first_name="Илья",
            last_name="Кузнецов",
        )
        supervisor_user = self._user(
            user_model,
            username="supervisor.demo",
            first_name="Анна",
            last_name="Орлова",
        )
        try:
            access_result = reconcile_demo_access(require_injection=True)
        except DemoAccessPolicyError as exc:
            raise CommandError(str(exc)) from exc

        for demo_user in (operator_user, supervisor_user):
            InterfacePreference.objects.get_or_create(
                user=demo_user,
                defaults={
                    "theme": InterfacePreference.Theme.LIGHT,
                    "density": InterfacePreference.Density.COMFORTABLE,
                    "font_scale": InterfacePreference.FontScale.NORMAL,
                    "content_width": InterfacePreference.ContentWidth.STANDARD,
                    "show_technical_details": False,
                },
            )

        employee_rows = (
            (
                "DEMO-001", "Кузнецов", "Илья", "Андреевич",
                "OPS", "DUTY_ELECTRICIAN", "SHIFT_POOL", operator_user,
            ),
            (
                "DEMO-002", "Орлова", "Анна", "Сергеевна",
                "OPS", "SHIFT_SUPERVISOR", "SHIFT_POOL", supervisor_user,
            ),
            (
                "DEMO-003", "Петров", "Сергей", "Викторович",
                "CENTER", "DEPUTY_OPERATIONS", None, None,
            ),
            (
                "DEMO-004", "Волков", "Александр", "Николаевич",
                "CENTER", "TECHNICAL_DIRECTOR", None, None,
            ),
            ("DEMO-005", "Смирнов", "Олег", "Андреевич", "CENTER", "DEPUTY_REPAIRS", None, None),
            ("DEMO-006", "Морозов", "Дмитрий", "Павлович", "RZA", "LEAD_ENGINEER", None, None),
            ("DEMO-007", "Фёдоров", "Алексей", "Игоревич", "WTG_SERVICE", "SITE_HEAD", None, None),
            ("DEMO-008", "Лебедев", "Роман", "Алексеевич", "TECHNICAL", "DEPARTMENT_HEAD", None, None),
            ("DEMO-009", "Новиков", "Михаил", "Сергеевич", "ASUTP", "LEAD_ENGINEER", None, None),
            ("DEMO-010", "Соколов", "Андрей", "Владимирович", "ELECTRICAL", "SITE_HEAD", None, None),
            (
                "DEMO-011", "Крылов", "Виктор", "Евгеньевич",
                "BLADE_SERVICE", "SITE_HEAD", "NEVIN_BLADE_BASE", None,
            ),
            ("DEMO-012", "Громов", "Денис", "Олегович", "OPS", "SHIFT_SUPERVISOR", "SHIFT_POOL", None),
            ("DEMO-013", "Белов", "Алексей", "Романович", "OPS", "DUTY_ELECTRICIAN", "SHIFT_POOL", None),
            ("DEMO-014", "Захаров", "Павел", "Ильич", "RZA", "ENGINEER", None, None),
            (
                "DEMO-015", "Васильев", "Николай", "Михайлович",
                "WTG_SERVICE", "WTG_SERVICE_ENGINEER", None, None,
            ),
            ("DEMO-016", "Мельников", "Игорь", "Петрович", "TECHNICAL", "CHIEF_SPECIALIST", None, None),
            (
                "DEMO-017", "Егоров", "Андрей", "Анатольевич",
                "ELECTRICAL", "EQUIPMENT_REPAIR_ELECTRICIAN", None, None,
            ),
        )
        employees: dict[str, Employee] = {}
        for number, last, first, middle, division_code, position_code, workplace_code, user in employee_rows:
            employee, _ = Employee.objects.update_or_create(
                organization=organization,
                personnel_number=number,
                defaults={
                    "division": divisions[division_code],
                    "position": positions[position_code],
                    "workplace": workplaces.get(workplace_code),
                    "user": user,
                    "last_name": last,
                    "first_name": first,
                    "middle_name": middle,
                    "employment_start": date(2026, 1, 1),
                    "employment_end": None,
                    "is_active": True,
                },
            )
            employees[number] = employee

        assignment_start = date(2026, 1, 1)
        for employee_number, role_code in (
            ("DEMO-001", "operator"),
            ("DEMO-002", "shift_supervisor"),
            ("DEMO-002", "operator"),
            ("DEMO-002", "organization_admin"),
        ):
            RoleAssignment.objects.update_or_create(
                employee=employees[employee_number],
                role=roles[role_code],
                scope=scopes["ALL_SITES"],
                valid_from=assignment_start,
                defaults={"valid_until": None, "is_active": True},
            )

        today = timezone.localdate()
        Substitution.objects.update_or_create(
            replaced_employee=employees["DEMO-002"],
            substitute_employee=employees["DEMO-001"],
            scope=scopes["ALL_SITES"],
            defaults={
                "valid_from": today - timedelta(days=1),
                "valid_until": today + timedelta(days=7),
                "reason": "Презентационный сценарий временного замещения",
                "is_active": True,
            },
        )

        self.stdout.write(self.style.SUCCESS("Презентационная структура организации создана или обновлена."))
        self.stdout.write("Персональные тестовые учётные записи подготовлены.")
        self.stdout.write(
            f"Контракт доступа: {access_result.status}; значение {DEMO_ACCESS_ENV} не выводится."
        )
        self.stdout.write(f"Подразделений: {Division.objects.filter(organization=organization).count()}")
        employee_count = Employee.objects.filter(organization=organization).count()
        self.stdout.write(f"Вымышленных сотрудников: {employee_count}")
        self.stdout.write("Реальные ФИО, контакты и табельные данные не используются.")

    def _user(self, user_model, *, username: str, first_name: str, last_name: str):
        user, created = user_model.objects.get_or_create(username=username)
        user.first_name = first_name
        user.last_name = last_name
        user.email = f"{username}@example.invalid"
        user.is_active = True
        user.is_staff = False
        if created:
            user.set_unusable_password()
        user.save()
        return user
