from __future__ import annotations

from datetime import date

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.equipment.models import EnergySite
from apps.organizations.models import (
    Division,
    DivisionEnergySiteService,
    DivisionServiceProfile,
    Employee,
    EmployeeEnergySiteAuthorization,
    OperationalReportingLine,
    Organization,
)


class Command(BaseCommand):
    help = "Связывает презентационные подразделения и персонал с энергообъектами."

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        organization = Organization.objects.get(code="DEMO")
        divisions = {
            division.code: division
            for division in Division.objects.filter(organization=organization)
        }
        sites = {
            site.code: site
            for site in EnergySite.objects.filter(organization=organization)
        }
        employees = {
            employee.personnel_number: employee
            for employee in Employee.objects.filter(organization=organization)
        }

        required_divisions = {
            "CENTER",
            "RZA",
            "WTG_SERVICE",
            "TECHNICAL",
            "ASUTP",
            "OPS",
            "ELECTRICAL",
            "BLADE_SERVICE",
        }
        required_sites = {
            "demo-wpp",
            "demo-kuzminskaya-wpp",
            "demo-grid-substation",
        }
        missing_divisions = required_divisions - divisions.keys()
        missing_sites = required_sites - sites.keys()
        if missing_divisions or missing_sites:
            raise RuntimeError(
                "Не хватает данных для организационных связей: "
                f"подразделения={sorted(missing_divisions)}, "
                f"энергообъекты={sorted(missing_sites)}"
            )

        DivisionServiceProfile.objects.update_or_create(
            division=divisions["CENTER"],
            defaults={
                "territorial_base": "Невинномысск",
                "service_scope": (
                    "Эксплуатация и техническое обслуживание Кочубеевской ВЭС, "
                    "Кузьминской ВЭС и ПС 330 кВ Барсуки."
                ),
                "is_cross_territory": True,
            },
        )
        DivisionServiceProfile.objects.update_or_create(
            division=divisions["BLADE_SERVICE"],
            defaults={
                "territorial_base": "Невинномысск",
                "service_scope": (
                    "Специализированное обслуживание лопастей ВЭУ на нескольких территориях; "
                    "подразделение не входит в ЦОТУиЭ ВЭС Невинномысск."
                ),
                "is_cross_territory": True,
            },
        )

        all_sites = (
            "demo-wpp",
            "demo-kuzminskaya-wpp",
            "demo-grid-substation",
        )
        service_rows: list[tuple[str, str, str, str]] = []
        for site_code in all_sites:
            service_rows.extend(
                (
                    (
                        "CENTER",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.OPERATING_CENTER,
                        "Энергообъект входит в эксплуатационный контур ЦОТУиЭ.",
                    ),
                    (
                        "OPS",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.OPERATIONAL,
                        "Оперативное обслуживание общим сменным персоналом.",
                    ),
                    (
                        "RZA",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.MAINTENANCE,
                        "Техническое обслуживание устройств РЗиА.",
                    ),
                    (
                        "TECHNICAL",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.ENGINEERING,
                        "Инженерное сопровождение эксплуатации.",
                    ),
                    (
                        "ASUTP",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.MAINTENANCE,
                        "Техническое обслуживание АСУ ТП.",
                    ),
                    (
                        "ELECTRICAL",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.MAINTENANCE,
                        "ТОиР электротехнического оборудования.",
                    ),
                )
            )
        for site_code in ("demo-wpp", "demo-kuzminskaya-wpp"):
            service_rows.extend(
                (
                    (
                        "WTG_SERVICE",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.MAINTENANCE,
                        "ТОиР ветроэнергетических установок.",
                    ),
                    (
                        "BLADE_SERVICE",
                        site_code,
                        DivisionEnergySiteService.ServiceKind.SPECIALIZED,
                        "Специализированное обслуживание лопастей ВЭУ.",
                    ),
                )
            )

        start = date(2026, 1, 1)
        for division_code, site_code, service_kind, note in service_rows:
            DivisionEnergySiteService.objects.update_or_create(
                division=divisions[division_code],
                energy_site=sites[site_code],
                service_kind=service_kind,
                valid_from=start,
                defaults={
                    "valid_until": None,
                    "note": note,
                    "is_active": True,
                },
            )

        OperationalReportingLine.objects.update_or_create(
            supervisor=employees["DEMO-003"],
            subordinate_division=divisions["OPS"],
            relation_type=OperationalReportingLine.RelationType.DIRECT,
            valid_from=start,
            defaults={
                "valid_until": None,
                "note": (
                    "Заместитель технического директора по оперативной работе является "
                    "непосредственно вышестоящим оперативным руководителем участка."
                ),
                "is_active": True,
            },
        )

        authorization_rows = (
            ("DEMO-001", EmployeeEnergySiteAuthorization.OperationalRole.DUTY_ELECTRICIAN),
            ("DEMO-002", EmployeeEnergySiteAuthorization.OperationalRole.SHIFT_SUPERVISOR),
            ("DEMO-012", EmployeeEnergySiteAuthorization.OperationalRole.SHIFT_SUPERVISOR),
            ("DEMO-013", EmployeeEnergySiteAuthorization.OperationalRole.DUTY_ELECTRICIAN),
        )
        for employee_number, operational_role in authorization_rows:
            for site_code in all_sites:
                EmployeeEnergySiteAuthorization.objects.update_or_create(
                    employee=employees[employee_number],
                    energy_site=sites[site_code],
                    operational_role=operational_role,
                    valid_from=start,
                    defaults={
                        "valid_until": None,
                        "note": (
                            "Презентационный допуск: сотрудник может быть назначен "
                            "в смену на любом энергообъекте ЦОТУиЭ."
                        ),
                        "is_active": True,
                    },
                )

        self.stdout.write("Организационные связи с энергообъектами созданы или проверены.")
        self.stdout.write(
            "Связей обслуживания: "
            f"{DivisionEnergySiteService.objects.filter(division__organization=organization).count()}"
        )
        self.stdout.write(
            "Допусков персонала: "
            f"{EmployeeEnergySiteAuthorization.objects.filter(employee__organization=organization).count()}"
        )
        self.stdout.write(
            "Оперативных линий подчинённости: "
            f"{OperationalReportingLine.objects.filter(
                subordinate_division__organization=organization
            ).count()}"
        )
