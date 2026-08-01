from __future__ import annotations

from datetime import UTC, date, datetime

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
    OperationalRightDefinition,
    Organization,
    Position,
    Workplace,
)

VALID_FROM = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
VALID_UNTIL = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)
SCOPE_KIND = AuthorityScopeKind.OPERATIONAL_AREA
SCOPE_REFERENCE = "KOCH"
SCOPE_LABEL = "Кочубеевская ВЭС — демонстрационная область"
SOURCE_IDS = ["DEMO-SYNTHETIC", "SRC-DEC-STAGE2"]
DEMO_PERSONNEL_NUMBERS = (
    "DEMO-001",
    "DEMO-002",
    "DEMO-003",
    "DEMO-013",
)


class Command(BaseCommand):
    help = (
        "Создаёт синтетические grants и authority-at-action примеры "
        "для презентационной базы."
    )

    @transaction.atomic
    def handle(self, *args, **options) -> None:
        try:
            host = Organization.objects.get(code="DEMO")
        except Organization.DoesNotExist as exc:
            raise CommandError(
                "Сначала выполните seed_demo_organization: "
                "презентационная организация отсутствует."
            ) from exc

        employees = {
            employee.personnel_number: employee
            for employee in Employee.objects.filter(
                organization=host,
                personnel_number__in=DEMO_PERSONNEL_NUMBERS,
            ).select_related("division", "position", "workplace")
        }
        required_numbers = set(DEMO_PERSONNEL_NUMBERS)
        if set(employees) != required_numbers:
            missing = ", ".join(sorted(required_numbers - set(employees)))
            raise CommandError(
                f"В presentation seed отсутствуют сотрудники: {missing}."
            )

        switching_right = OperationalRightDefinition.objects.get(
            code="switching_operation"
        )
        inspection_right = OperationalRightDefinition.objects.get(
            code="sole_inspection"
        )
        supervisor = employees["DEMO-002"]

        self._grant(
            host=host,
            employee=employees["DEMO-001"],
            right_definition=switching_right,
            action_code="SWITCHING.EXECUTE",
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="DEMO-ONLY / EXECUTION-AUTHORITY / R1",
            created_by=supervisor,
        )
        self._grant(
            host=host,
            employee=supervisor,
            right_definition=switching_right,
            action_code="SWITCHING.CONTROL",
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="DEMO-ONLY / CONTROL-AUTHORITY / R1",
            created_by=supervisor,
            allow_substitution=True,
        )
        self._grant(
            host=host,
            employee=employees["DEMO-003"],
            right_definition=switching_right,
            action_code="SWITCHING.AUTHORIZE",
            basis_status=AuthorityBasisStatus.VERIFY,
            basis_reference="DEMO-ONLY / UNCONFIRMED-AUTHORITY / R1",
            created_by=supervisor,
        )

        contractor = self._external_personnel(
            host=host,
            created_by=supervisor,
        )
        self._grant(
            host=host,
            employee=contractor,
            right_definition=inspection_right,
            action_code="EQUIPMENT.INSPECT",
            basis_status=AuthorityBasisStatus.CONFIRMED,
            basis_reference="DEMO-ONLY / CONTRACTOR-ADMISSION / R1",
            created_by=supervisor,
        )

        self._evaluation(
            host=host,
            employee=employees["DEMO-001"],
            action_code="SWITCHING.EXECUTE",
            occurred_at=datetime(2026, 8, 1, 7, 0, tzinfo=UTC),
            subject_id="DEMO-AUTH-ALLOW",
            recorded_by=supervisor,
        )
        self._evaluation(
            host=host,
            employee=employees["DEMO-013"],
            action_code="SWITCHING.EXECUTE",
            occurred_at=datetime(2026, 8, 1, 7, 5, tzinfo=UTC),
            subject_id="DEMO-AUTH-DENY",
            recorded_by=supervisor,
        )
        self._evaluation(
            host=host,
            employee=employees["DEMO-003"],
            action_code="SWITCHING.AUTHORIZE",
            occurred_at=datetime(2026, 8, 1, 7, 10, tzinfo=UTC),
            subject_id="DEMO-AUTH-VERIFY",
            recorded_by=supervisor,
        )
        self._evaluation(
            host=host,
            employee=contractor,
            action_code="EQUIPMENT.INSPECT",
            occurred_at=datetime(2026, 8, 1, 7, 15, tzinfo=UTC),
            subject_id="DEMO-AUTH-EXTERNAL",
            recorded_by=supervisor,
            external_relation_kind=PersonnelRelationKind.CONTRACTOR,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Синтетические оперативные полномочия и четыре "
                "результата проверки созданы."
            )
        )
        self.stdout.write(
            "Все основания помечены DEMO-ONLY; реальные персональные "
            "данные и локальные акты не используются."
        )

    def _grant(
        self,
        *,
        host: Organization,
        employee: Employee,
        right_definition: OperationalRightDefinition,
        action_code: str,
        basis_status: str,
        basis_reference: str,
        created_by: Employee,
        allow_substitution: bool = False,
    ) -> OperationalAuthorityGrant:
        grant, _ = OperationalAuthorityGrant.objects.update_or_create(
            employee=employee,
            action_code=action_code,
            scope_kind=SCOPE_KIND,
            scope_reference=SCOPE_REFERENCE,
            valid_from=VALID_FROM,
            basis_reference=basis_reference,
            defaults={
                "organization": host,
                "right_definition": right_definition,
                "scope_label": SCOPE_LABEL,
                "granting_organization": host,
                "basis_status": basis_status,
                "source_ids": SOURCE_IDS,
                "valid_until": VALID_UNTIL,
                "is_active": True,
                "allow_substitution": allow_substitution,
                "created_by": created_by,
            },
        )
        return grant

    def _external_personnel(
        self,
        *,
        host: Organization,
        created_by: Employee,
    ) -> Employee:
        home, _ = Organization.objects.update_or_create(
            code="DEMO-CONTRACTOR",
            defaults={
                "name": "ООО «Энергосервис — демонстрационный контур»",
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
                "employment_start": date(2026, 1, 1),
                "employment_end": None,
                "is_active": True,
            },
        )
        ExternalPersonnelEngagement.objects.update_or_create(
            employee=employee,
            host_organization=host,
            scope_kind=SCOPE_KIND,
            scope_reference=SCOPE_REFERENCE,
            valid_from=VALID_FROM,
            defaults={
                "home_organization": home,
                "relation_kind": ExternalPersonnelRelationKind.CONTRACTOR,
                "scope_label": SCOPE_LABEL,
                "valid_until": VALID_UNTIL,
                "basis_status": AuthorityBasisStatus.CONFIRMED,
                "basis_reference": (
                    "DEMO-ONLY / CONTRACTOR-ADMISSION / R1"
                ),
                "source_ids": ["DEMO-SYNTHETIC", "REF-OD-052"],
                "is_active": True,
                "created_by": created_by,
            },
        )
        return employee

    def _evaluation(
        self,
        *,
        host: Organization,
        employee: Employee,
        action_code: str,
        occurred_at: datetime,
        subject_id: str,
        recorded_by: Employee,
        external_relation_kind: PersonnelRelationKind | None = None,
    ) -> None:
        if AuthorityEvaluationRecord.objects.filter(
            organization=host,
            actor=employee,
            subject_type="DEMO_SCENARIO",
            subject_id=subject_id,
            occurred_at=occurred_at,
        ).exists():
            return
        evaluate_and_record_authority(
            employee=employee,
            organization=host,
            action_code=action_code,
            occurred_at=occurred_at,
            scope_kind=SCOPE_KIND,
            scope_reference=SCOPE_REFERENCE,
            scope_label=SCOPE_LABEL,
            subject_type="DEMO_SCENARIO",
            subject_id=subject_id,
            external_relation_kind=external_relation_kind,
            recorded_by=recorded_by,
        )
