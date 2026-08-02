from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Final

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.organizations.authority import PersonnelRelationKind
from apps.organizations.authority_models import (
    AuthorityBasisStatus,
    AuthorityEvaluationRecord,
    AuthorityScopeKind,
    ExternalPersonnelEngagement,
    ExternalPersonnelRelationKind,
    OperationalAuthorityGrant,
)
from apps.organizations.authority_services import evaluate_and_record_authority
from apps.organizations.models import (
    Division,
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    OperationalRightDefinition,
    Organization,
    Position,
    Workplace,
)

VALID_FROM_DATE: Final = date(2026, 1, 1)
VALID_UNTIL_DATE: Final = date(2026, 12, 31)
VALID_FROM: Final = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
VALID_UNTIL: Final = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)
SCOPE_KIND: Final = AuthorityScopeKind.OPERATIONAL_AREA
SCOPE_REFERENCE: Final = "ALL_SITES"
SCOPE_LABEL: Final = "Энергообъекты ЦОТУиЭ ВЭС Невинномысск"
SOURCE_HASH: Final = "d" * 64
SOURCE_REFERENCE: Final = (
    "DEMO-ONLY / опубликованная матрица прав "
    "штатного персонала / редакция 01.01.2026"
)
SOURCE_IDS: Final = ["DEMO-SYNTHETIC", "PERSONNEL-AUTHORITY-MATRIX-R1"]

RIGHT_DEFINITIONS: Final = (
    (
        "dispatch_request_submit",
        "Подача диспетчерской заявки",
        "APPLICATIONS",
        "BOOLEAN",
        "REQUEST.DISPATCH.SUBMIT",
    ),
    (
        "dispatch_request_approve",
        "Согласование диспетчерской заявки",
        "APPLICATIONS",
        "BOOLEAN",
        "REQUEST.DISPATCH.APPROVE",
    ),
    (
        "operational_request_submit",
        "Подача оперативной заявки",
        "APPLICATIONS",
        "BOOLEAN",
        "REQUEST.OPERATIONAL.SUBMIT",
    ),
    (
        "operational_request_approve",
        "Согласование оперативной заявки",
        "APPLICATIONS",
        "BOOLEAN",
        "REQUEST.OPERATIONAL.APPROVE",
    ),
    (
        "interlock_release",
        (
            "Разрешение на деблокировку "
            "при неисправной блокировке"
        ),
        "SWITCHING",
        "BOOLEAN",
        "INTERLOCK.RELEASE",
    ),
    (
        "worksite_preparation_admission_authorize",
        (
            "Разрешение на подготовку рабочего места "
            "и допуск"
        ),
        "WORK_SAFETY",
        "BOOLEAN",
        "WORKSITE.AUTHORIZE",
    ),
    (
        "work_permit_issue",
        "Выдача наряда-допуска или распоряжения",
        "WORK_SAFETY",
        "BOOLEAN",
        "WORK.PERMIT.ISSUE",
    ),
    (
        "responsible_work_manager",
        "Ответственный руководитель работ",
        "WORK_SAFETY",
        "BOOLEAN",
        "WORK.RESPONSIBLE_MANAGER",
    ),
    (
        "admitting_person",
        "Допускающий",
        "WORK_SAFETY",
        "BOOLEAN",
        "WORK.ADMIT",
    ),
    (
        "work_supervisor",
        "Производитель работ",
        "WORK_SAFETY",
        "BOOLEAN",
        "WORK.SUPERVISE",
    ),
    (
        "observer",
        "Наблюдающий",
        "WORK_SAFETY",
        "BOOLEAN",
        "WORK.OBSERVE",
    ),
    (
        "crew_member",
        "Член бригады",
        "WORK_SAFETY",
        "BOOLEAN",
        "WORK.CREW_MEMBER",
    ),
    (
        "sole_inspection",
        "Единоличный осмотр",
        "WORK_SAFETY",
        "BOOLEAN",
        "EQUIPMENT.INSPECT",
    ),
    (
        "operational_communications",
        "Ведение оперативных переговоров",
        "COMMUNICATIONS",
        "BOOLEAN",
        "COMMUNICATIONS.OPERATIONAL",
    ),
    (
        "switching_operation",
        "Производство переключений",
        "SWITCHING",
        "BOOLEAN",
        "SWITCHING.EXECUTE",
    ),
    (
        "switching_control",
        "Контроль переключений",
        "SWITCHING",
        "BOOLEAN",
        "SWITCHING.CONTROL",
    ),
    (
        "electrical_installation_scope",
        "Электроустановки, в которых действует право",
        "SPECIAL_WORK",
        "QUALIFIED",
        "ELECTRICAL_INSTALLATION.ACCESS",
    ),
    (
        "work_at_height",
        "Работы на высоте",
        "SPECIAL_WORK",
        "QUALIFIED",
        "SPECIAL_WORK.HEIGHT",
    ),
    (
        "live_work",
        "Работы под напряжением на токоведущих частях",
        "SPECIAL_WORK",
        "QUALIFIED",
        "SPECIAL_WORK.LIVE",
    ),
    (
        "induced_voltage_work",
        "Работы под наведённым напряжением",
        "SPECIAL_WORK",
        "QUALIFIED",
        "SPECIAL_WORK.INDUCED_VOLTAGE",
    ),
    (
        "high_voltage_testing",
        "Испытания оборудования повышенным напряжением",
        "SPECIAL_WORK",
        "BOOLEAN",
        "SPECIAL_WORK.HIGH_VOLTAGE_TEST",
    ),
    (
        "rza_maintenance_category",
        (
            "Категория допуска к техническому "
            "обслуживанию устройств РЗА"
        ),
        "RZA",
        "ENUM",
        "RZA.MAINTENANCE",
    ),
)

CONDITIONS: Final = {
    "+1": (
        "После подтверждения оперативным "
        "руководителем в смене."
    ),
    "+2": (
        "В пределах закреплённой "
        "электроустановки и группы."
    ),
    "+3": (
        "Только при наличии действующего "
        "специального допуска."
    ),
}
COMMON_SCOPE: Final = (
    "Кочубеевская ВЭС, Кузьминская ВЭС "
    "и ПС 330 кВ Барсуки"
)
OPS_SCOPE: Final = "Оперативная зона ЦОТУиЭ ВЭС Невинномысск"


def cell(
    code: str,
    marker: str = "+",
    qualifier: str = "",
    scope: str = COMMON_SCOPE,
) -> tuple[str, str, str, str]:
    return (code, marker, qualifier or CONDITIONS.get(marker, ""), scope)


def combine(*groups):
    result = []
    seen = set()
    for group in groups:
        for item in group:
            if item[0] not in seen:
                result.append(item)
                seen.add(item[0])
    return tuple(result)


APPLICATIONS = tuple(cell(code) for code in (
    "dispatch_request_submit",
    "dispatch_request_approve",
    "operational_request_submit",
    "operational_request_approve",
))
WORK_MANAGEMENT = tuple(cell(code) for code in (
    "worksite_preparation_admission_authorize",
    "work_permit_issue",
    "responsible_work_manager",
))
WORK_EXECUTION = tuple(cell(code) for code in (
    "admitting_person",
    "work_supervisor",
    "observer",
    "crew_member",
    "sole_inspection",
))
OPERATIONS = (
    cell("operational_communications", scope=OPS_SCOPE),
    cell("switching_operation", scope=OPS_SCOPE),
    cell("switching_control", scope=OPS_SCOPE),
)
ELECTRICAL_SCOPE = (
    cell(
        "electrical_installation_scope",
        qualifier="ЭУ до и выше 1000 В",
    ),
)
SPECIAL_MANAGER = (
    cell("work_at_height", "+3", "3 группа"),
    cell("live_work", "+3", "III"),
    cell("induced_voltage_work", "+3"),
    cell("high_voltage_testing", "+3"),
)
SPECIAL_WORKER = (
    cell("work_at_height", "+2", "2 группа"),
    cell("live_work", "+3", "III"),
    cell("induced_voltage_work", "+3"),
)


def matrix_row(category, group, voltage, rights):
    return {
        "category": category,
        "group": group,
        "voltage": voltage,
        "rights": rights,
    }


MATRIX_ROWS: Final = {
    "DEMO-004": matrix_row(
        "АТП", "V", "до и выше 1000 В",
        combine(APPLICATIONS, WORK_MANAGEMENT, WORK_EXECUTION, ELECTRICAL_SCOPE),
    ),
    "DEMO-003": matrix_row(
        "АТП/ОП", "V", "до и выше 1000 В",
        combine(
            APPLICATIONS,
            (cell("interlock_release", "+1"),),
            WORK_MANAGEMENT,
            WORK_EXECUTION,
            OPERATIONS,
            ELECTRICAL_SCOPE,
        ),
    ),
    "DEMO-005": matrix_row(
        "АТП", "V", "до и выше 1000 В",
        combine(
            APPLICATIONS[2:],
            WORK_MANAGEMENT,
            WORK_EXECUTION,
            ELECTRICAL_SCOPE,
            SPECIAL_MANAGER,
        ),
    ),
    "DEMO-008": matrix_row(
        "АТП", "V", "до и выше 1000 В",
        combine(APPLICATIONS, WORK_MANAGEMENT, WORK_EXECUTION, ELECTRICAL_SCOPE),
    ),
    "DEMO-016": matrix_row(
        "АТП", "IV", "до 1000 В",
        combine(APPLICATIONS[2:3], WORK_EXECUTION[3:], ELECTRICAL_SCOPE),
    ),
    "DEMO-002": matrix_row(
        "ОП", "V", "до и выше 1000 В",
        combine(
            APPLICATIONS[::2],
            (cell("operational_request_approve"), cell("interlock_release", "+1")),
            WORK_EXECUTION,
            OPERATIONS,
            ELECTRICAL_SCOPE,
        ),
    ),
    "DEMO-012": matrix_row(
        "ОП", "V", "до и выше 1000 В",
        combine(
            APPLICATIONS[::2],
            (cell("operational_request_approve"), cell("interlock_release", "+1")),
            WORK_EXECUTION,
            OPERATIONS,
            ELECTRICAL_SCOPE,
        ),
    ),
    "DEMO-001": matrix_row(
        "ОП", "IV", "до и выше 1000 В",
        combine(APPLICATIONS[::2], WORK_EXECUTION, OPERATIONS[:2], ELECTRICAL_SCOPE),
    ),
    "DEMO-013": matrix_row(
        "ОП", "IV", "до и выше 1000 В",
        combine(APPLICATIONS[::2], WORK_EXECUTION[3:], OPERATIONS[:2], ELECTRICAL_SCOPE),
    ),
    "DEMO-006": matrix_row(
        "ОРП", "V", "до и выше 1000 В",
        combine(
            APPLICATIONS[2:],
            WORK_MANAGEMENT,
            WORK_EXECUTION,
            ELECTRICAL_SCOPE,
            SPECIAL_MANAGER,
            (cell("rza_maintenance_category", qualifier="IV"),),
        ),
    ),
    "DEMO-014": matrix_row(
        "РП", "IV", "до и выше 1000 В",
        combine(
            APPLICATIONS[2:3],
            WORK_EXECUTION[1:],
            ELECTRICAL_SCOPE,
            SPECIAL_WORKER,
            (cell("rza_maintenance_category", qualifier="III"),),
        ),
    ),
    "DEMO-007": matrix_row(
        "АТП", "IV", "до 1000 В",
        combine(APPLICATIONS[2:], WORK_MANAGEMENT, WORK_EXECUTION, SPECIAL_MANAGER[:2]),
    ),
    "DEMO-015": matrix_row(
        "РП", "IV", "до 1000 В",
        combine(APPLICATIONS[2:3], WORK_EXECUTION[1:], SPECIAL_MANAGER[:2]),
    ),
    "DEMO-009": matrix_row(
        "РП", "IV", "до 1000 В",
        combine(
            APPLICATIONS[2:3],
            WORK_EXECUTION[1:],
            ELECTRICAL_SCOPE,
            SPECIAL_WORKER[:1],
            (cell("rza_maintenance_category", qualifier="III"),),
        ),
    ),
    "DEMO-010": matrix_row(
        "АТП", "V", "до и выше 1000 В",
        combine(
            APPLICATIONS[2:],
            WORK_MANAGEMENT,
            WORK_EXECUTION,
            ELECTRICAL_SCOPE,
            SPECIAL_MANAGER,
        ),
    ),
    "DEMO-017": matrix_row(
        "РП", "IV", "до и выше 1000 В",
        combine(
            APPLICATIONS[2:3],
            WORK_EXECUTION[1:],
            ELECTRICAL_SCOPE,
            SPECIAL_WORKER,
            SPECIAL_MANAGER[3:],
        ),
    ),
    "DEMO-011": matrix_row(
        "АТП", "III", "до 1000 В",
        combine(APPLICATIONS[2:], WORK_MANAGEMENT, WORK_EXECUTION, SPECIAL_MANAGER[:1]),
    ),
}


class Command(BaseCommand):
    help = (
        "Публикует синтетическую матрицу "
        "прав штатного персонала, "
        "linked evaluator projections и примеры решений."
    )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        try:
            host = Organization.objects.get(code="DEMO")
        except Organization.DoesNotExist as exc:
            raise CommandError(
                "Сначала выполните seed_demo_organization."
            ) from exc

        employees = {
            item.personnel_number: item
            for item in Employee.objects.filter(
                organization=host,
                personnel_number__in=MATRIX_ROWS,
            ).select_related("division", "position", "workplace")
        }
        missing = sorted(set(MATRIX_ROWS) - set(employees))
        if missing:
            raise CommandError(
                "В presentation seed отсутствуют сотрудники: "
                + ", ".join(missing)
            )

        definitions = self._right_definitions()
        supervisor = employees["DEMO-002"]
        published_cells = self._publish_matrix(
            host,
            employees,
            definitions,
            supervisor,
        )
        contractor = self._external_personnel(host, supervisor)
        inspection_right = definitions["sole_inspection"][0]
        self._structured_grant(
            host,
            contractor,
            inspection_right,
            "EQUIPMENT.INSPECT",
            None,
            AuthorityBasisStatus.CONFIRMED,
            "DEMO-ONLY / CONTRACTOR-ADMISSION / R1",
            supervisor,
            scope_reference="KOCH",
            scope_label=(
                "Кочубеевская ВЭС — "
                "демонстрационная область"
            ),
        )

        scenarios = (
            (employees["DEMO-001"], "SWITCHING.EXECUTE", 0, "DEMO-AUTH-ALLOW", None),
            (employees["DEMO-013"], "SWITCHING.CONTROL", 5, "DEMO-AUTH-DENY", None),
            (
                employees["DEMO-003"],
                "INTERLOCK.RELEASE",
                10,
                "DEMO-AUTH-VERIFY-MATRIX-CONDITION",
                None,
            ),
            (
                contractor,
                "EQUIPMENT.INSPECT",
                15,
                "DEMO-AUTH-EXTERNAL",
                PersonnelRelationKind.CONTRACTOR,
            ),
        )
        for employee, action, minute, subject, relation in scenarios:
            self._evaluation(
                host,
                employee,
                action,
                datetime(2026, 8, 1, 7, minute, tzinfo=UTC),
                subject,
                supervisor,
                relation,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Матрица создана: {len(employees)} сотрудников, "
                f"{published_cells} положительных ячеек."
            )
        )

    def _right_definitions(self):
        result = {}
        for order, row in enumerate(RIGHT_DEFINITIONS, start=10):
            code, name, category, value_kind, action_code = row
            item, _ = OperationalRightDefinition.objects.update_or_create(
                code=code,
                defaults={
                    "name": name,
                    "category": category,
                    "value_kind": value_kind,
                    "description": (
                        "Колонка опубликованной "
                        "матрицы прав."
                    ),
                    "display_order": order,
                    "is_active": True,
                },
            )
            result[code] = (item, action_code)
        return result

    def _publish_matrix(self, host, employees, definitions, created_by):
        count = 0
        for row_number, employee_number in enumerate(MATRIX_ROWS, start=9):
            employee = employees[employee_number]
            row = MATRIX_ROWS[employee_number]
            EmployeeQualification.objects.update_or_create(
                employee=employee,
                source_file_sha256=SOURCE_HASH,
                source_row_number=row_number,
                defaults={
                    "personnel_category": row["category"],
                    "electrical_safety_group": row["group"],
                    "voltage_scope": row["voltage"],
                    "electrical_installation_scope": COMMON_SCOPE,
                    "valid_from": VALID_FROM_DATE,
                    "valid_until": VALID_UNTIL_DATE,
                    "is_active": True,
                    "source_reference": SOURCE_REFERENCE,
                },
            )
            for right_code, marker, qualifier, scope_text in row["rights"]:
                definition, action_code = definitions[right_code]
                source_right, _ = EmployeeOperationalRight.objects.update_or_create(
                    employee=employee,
                    right_definition=definition,
                    source_file_sha256=SOURCE_HASH,
                    source_row_number=row_number,
                    defaults={
                        "qualifier": qualifier,
                        "scope_text": scope_text,
                        "source_marker": marker,
                        "source_reference": SOURCE_REFERENCE,
                        "valid_from": VALID_FROM_DATE,
                        "valid_until": VALID_UNTIL_DATE,
                        "is_active": True,
                    },
                )
                status = (
                    AuthorityBasisStatus.CONFIRMED
                    if marker == "+"
                    else AuthorityBasisStatus.VERIFY
                )
                self._structured_grant(
                    host,
                    employee,
                    definition,
                    action_code,
                    source_right,
                    status,
                    f"{SOURCE_REFERENCE} / строка {row_number} / {marker}",
                    created_by,
                )
                count += 1
        return count

    def _structured_grant(
        self,
        host,
        employee,
        definition,
        action_code,
        source_right,
        basis_status,
        basis_reference,
        created_by,
        *,
        scope_reference=SCOPE_REFERENCE,
        scope_label=SCOPE_LABEL,
    ):
        grant = OperationalAuthorityGrant.objects.filter(
            employee=employee,
            action_code=action_code,
            scope_kind=SCOPE_KIND,
            scope_reference=scope_reference,
            valid_from=VALID_FROM,
        ).order_by("id").first()
        if grant is None:
            grant = OperationalAuthorityGrant(
                employee=employee,
                action_code=action_code,
                scope_kind=SCOPE_KIND,
                scope_reference=scope_reference,
                valid_from=VALID_FROM,
            )
        grant.organization = host
        grant.right_definition = definition
        grant.scope_label = scope_label
        grant.granting_organization = host
        grant.basis_status = basis_status
        grant.basis_reference = basis_reference
        grant.source_ids = SOURCE_IDS
        grant.source_operational_right = source_right
        grant.valid_until = VALID_UNTIL
        grant.is_active = True
        grant.allow_substitution = False
        grant.created_by = created_by
        grant.save()
        return grant

    def _external_personnel(self, host, created_by):
        home, _ = Organization.objects.update_or_create(
            code="DEMO-CONTRACTOR",
            defaults={
                "name": (
                    "ООО «Энергосервис — "
                    "демонстрационный контур»"
                ),
                "short_name": "ООО «Энергосервис — Demo»",
                "is_active": True,
            },
        )
        division, _ = Division.objects.update_or_create(
            organization=home,
            code="FIELD-SERVICE",
            defaults={
                "name": "Выездная сервисная группа",
                "is_active": True,
            },
        )
        position, _ = Position.objects.update_or_create(
            organization=home,
            code="SERVICE-SPECIALIST",
            defaults={
                "name": "Специалист сервисной организации",
                "is_operational": False,
                "is_active": True,
            },
        )
        workplace, _ = Workplace.objects.update_or_create(
            organization=home,
            code="FIELD-TEAM",
            defaults={
                "division": division,
                "name": "Мобильная сервисная бригада",
                "is_active": True,
            },
        )
        employee, _ = Employee.objects.update_or_create(
            organization=home,
            personnel_number="DEMO-EXT-001",
            defaults={
                "division": division,
                "position": position,
                "workplace": workplace,
                "last_name": "Серов",
                "first_name": "Максим",
                "middle_name": "Олегович",
                "employment_start": VALID_FROM_DATE,
                "is_active": True,
            },
        )
        ExternalPersonnelEngagement.objects.update_or_create(
            employee=employee,
            host_organization=host,
            scope_kind=SCOPE_KIND,
            scope_reference="KOCH",
            valid_from=VALID_FROM,
            defaults={
                "home_organization": home,
                "relation_kind": ExternalPersonnelRelationKind.CONTRACTOR,
                "scope_label": (
                    "Кочубеевская ВЭС — "
                    "демонстрационная область"
                ),
                "valid_until": VALID_UNTIL,
                "basis_status": AuthorityBasisStatus.CONFIRMED,
                "basis_reference": "DEMO-ONLY / CONTRACTOR-ADMISSION / R1",
                "source_ids": ["DEMO-SYNTHETIC", "REF-OD-052"],
                "is_active": True,
                "created_by": created_by,
            },
        )
        return employee

    def _evaluation(
        self,
        host,
        employee,
        action_code,
        occurred_at,
        subject_id,
        recorded_by,
        relation_kind=None,
    ):
        if AuthorityEvaluationRecord.objects.filter(
            organization=host,
            actor=employee,
            subject_type="DEMO_SCENARIO",
            subject_id=subject_id,
            occurred_at=occurred_at,
        ).exists():
            return
        external = relation_kind == PersonnelRelationKind.CONTRACTOR
        evaluate_and_record_authority(
            employee=employee,
            organization=host,
            action_code=action_code,
            occurred_at=occurred_at,
            scope_kind=SCOPE_KIND,
            scope_reference="KOCH" if external else SCOPE_REFERENCE,
            scope_label=(
                "Кочубеевская ВЭС — "
                "демонстрационная область"
                if external
                else SCOPE_LABEL
            ),
            subject_type="DEMO_SCENARIO",
            subject_id=subject_id,
            external_relation_kind=relation_kind,
            recorded_by=recorded_by,
        )
