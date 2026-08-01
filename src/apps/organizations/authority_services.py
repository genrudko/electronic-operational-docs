from __future__ import annotations

import json
import re
from datetime import datetime, time

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.normatives.evidence import canonical_json

from .authority import (
    AuthorityActorFact,
    AuthorityGrantFact,
    AuthorityQualificationFact,
    AuthorityRequest,
    AuthorityScope,
    AuthoritySubstitutionFact,
    ExternalPersonnelEngagementFact,
    PersonnelRelationKind,
    evaluate_authority,
)
from .authority import AuthorityBasisStatus as ContractBasisStatus
from .authority import AuthorityScopeKind as ContractScopeKind
from .authority_models import (
    AuthorityEvaluationRecord,
    ExternalPersonnelEngagement,
    OperationalAuthorityGrant,
    OperationalAuthoritySubstitution,
)
from .models import Employee, EmployeeQualification, Organization, RoleAssignment

_QUALIFICATION_TOKEN_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]*$")


def _day_start(value, *, tz) -> datetime:
    return datetime.combine(value, time.min, tzinfo=tz)


def _day_end(value, *, tz) -> datetime:
    return datetime.combine(value, time.max, tzinfo=tz)


def _controlled_qualification_code(namespace: str, value: object) -> str | None:
    token = "_".join(str(value or "").strip().upper().split())
    if not token or not _QUALIFICATION_TOKEN_PATTERN.fullmatch(token):
        return None
    return f"{namespace}:{token}"


def qualification_codes_for_model(
    qualification: EmployeeQualification,
) -> tuple[str, ...]:
    codes = {
        code
        for code in (
            _controlled_qualification_code(
                "PERSONNEL_CATEGORY",
                qualification.personnel_category,
            ),
            _controlled_qualification_code(
                "ELECTRICAL_SAFETY_GROUP",
                qualification.electrical_safety_group,
            ),
            _controlled_qualification_code(
                "VOLTAGE_SCOPE",
                qualification.voltage_scope,
            ),
        )
        if code is not None
    }
    return tuple(sorted(codes))


def _actor_fact(
    *,
    employee: Employee,
    organization: Organization,
    occurred_at: datetime,
    external_relation_kind: PersonnelRelationKind | None,
    engagements: list[ExternalPersonnelEngagement],
) -> AuthorityActorFact:
    tz = timezone.get_current_timezone()
    if employee.organization_id == organization.id:
        relation_kind = PersonnelRelationKind.EMPLOYEE
    elif external_relation_kind is not None:
        relation_kind = PersonnelRelationKind(external_relation_kind)
    elif engagements:
        relation_kind = PersonnelRelationKind(engagements[0].relation_kind)
    else:
        raise ValidationError(
            {
                "external_relation_kind": (
                    "Для внешнего сотрудника без зарегистрированного допуска требуется "
                    "явно указать вид отношения."
                )
            }
        )

    local_day = timezone.localdate(occurred_at)
    role_assignments = (
        RoleAssignment.objects.select_related("role")
        .filter(employee=employee, is_active=True, valid_from__lte=local_day)
        .filter(Q(valid_until__isnull=True) | Q(valid_until__gte=local_day))
    )
    application_roles = tuple(
        sorted({assignment.role.code for assignment in role_assignments})
    )

    return AuthorityActorFact(
        employee_id=employee.id,
        organization_id=employee.organization_id,
        relation_kind=relation_kind,
        full_name=employee.full_name,
        position=employee.position.name,
        division=employee.division.name,
        workplace=employee.workplace.name if employee.workplace_id else "",
        employment_from=_day_start(employee.employment_start, tz=tz),
        employment_until=(
            _day_end(employee.employment_end, tz=tz)
            if employee.employment_end
            else None
        ),
        is_active=employee.is_active,
        application_roles=application_roles,
    )


def _grant_fact(grant: OperationalAuthorityGrant) -> AuthorityGrantFact:
    return AuthorityGrantFact(
        grant_id=str(grant.public_id),
        employee_id=grant.employee_id,
        organization_id=grant.organization_id,
        action_code=grant.action_code,
        scope=AuthorityScope(
            kind=ContractScopeKind(grant.scope_kind),
            reference=grant.scope_reference,
            label=grant.scope_label,
        ),
        valid_from=grant.valid_from,
        valid_until=grant.valid_until,
        basis_status=ContractBasisStatus(grant.basis_status),
        basis_reference=grant.basis_reference,
        source_ids=tuple(grant.source_ids),
        is_active=grant.is_active,
        allow_substitution=grant.allow_substitution,
    )


def _qualification_facts(
    qualification: EmployeeQualification,
) -> tuple[AuthorityQualificationFact, ...]:
    tz = timezone.get_current_timezone()
    return tuple(
        AuthorityQualificationFact(
            employee_id=qualification.employee_id,
            code=code,
            valid_from=_day_start(qualification.valid_from, tz=tz),
            valid_until=(
                _day_end(qualification.valid_until, tz=tz)
                if qualification.valid_until
                else None
            ),
            is_active=qualification.is_active,
        )
        for code in qualification_codes_for_model(qualification)
    )


def _substitution_fact(
    item: OperationalAuthoritySubstitution,
) -> AuthoritySubstitutionFact:
    tz = timezone.get_current_timezone()
    base = item.substitution
    return AuthoritySubstitutionFact(
        substitution_id=str(item.public_id),
        replaced_employee_id=base.replaced_employee_id,
        substitute_employee_id=base.substitute_employee_id,
        organization_id=item.organization_id,
        action_codes=tuple(item.action_codes),
        scope=AuthorityScope(
            kind=ContractScopeKind(item.scope_kind),
            reference=item.scope_reference,
            label=item.scope_label,
        ),
        valid_from=_day_start(base.valid_from, tz=tz),
        valid_until=_day_end(base.valid_until, tz=tz),
        basis_status=ContractBasisStatus(item.basis_status),
        basis_reference=item.basis_reference,
        is_active=item.is_active and base.is_active,
    )


def _engagement_fact(
    item: ExternalPersonnelEngagement,
) -> ExternalPersonnelEngagementFact:
    return ExternalPersonnelEngagementFact(
        engagement_id=str(item.public_id),
        employee_id=item.employee_id,
        home_organization_id=item.home_organization_id,
        host_organization_id=item.host_organization_id,
        relation_kind=PersonnelRelationKind(item.relation_kind),
        scope=AuthorityScope(
            kind=ContractScopeKind(item.scope_kind),
            reference=item.scope_reference,
            label=item.scope_label,
        ),
        valid_from=item.valid_from,
        valid_until=item.valid_until,
        basis_status=ContractBasisStatus(item.basis_status),
        basis_reference=item.basis_reference,
        is_active=item.is_active,
    )


@transaction.atomic
def evaluate_and_record_authority(
    *,
    employee: Employee,
    organization: Organization,
    action_code: str,
    occurred_at: datetime,
    scope_kind: str,
    scope_reference: str,
    scope_label: str,
    subject_type: str,
    subject_id: str,
    required_qualification_codes: tuple[str, ...] = (),
    external_relation_kind: PersonnelRelationKind | None = None,
    recorded_by: Employee | None = None,
    previous_evaluation: AuthorityEvaluationRecord | None = None,
) -> AuthorityEvaluationRecord:
    if timezone.is_naive(occurred_at):
        raise ValidationError({"occurred_at": "Время должно содержать часовой пояс."})

    request = AuthorityRequest(
        organization_id=organization.id,
        actor_employee_id=employee.id,
        action_code=action_code,
        occurred_at=occurred_at,
        scope=AuthorityScope(
            kind=ContractScopeKind(scope_kind),
            reference=scope_reference,
            label=scope_label,
        ),
        subject_type=subject_type,
        subject_id=subject_id,
        required_qualification_codes=required_qualification_codes,
    )

    grants = list(
        OperationalAuthorityGrant.objects.select_related(
            "employee",
            "organization",
            "right_definition",
        ).filter(
            organization=organization,
            action_code=request.action_code,
        )
    )
    qualifications = list(EmployeeQualification.objects.filter(employee=employee))
    substitutions = list(
        OperationalAuthoritySubstitution.objects.select_related(
            "substitution__replaced_employee",
            "substitution__substitute_employee",
        ).filter(
            organization=organization,
            substitution__substitute_employee=employee,
        )
    )
    engagements = list(
        ExternalPersonnelEngagement.objects.select_related(
            "employee",
            "home_organization",
            "host_organization",
        ).filter(
            employee=employee,
            host_organization=organization,
        )
    )

    actor = _actor_fact(
        employee=employee,
        organization=organization,
        occurred_at=occurred_at,
        external_relation_kind=external_relation_kind,
        engagements=engagements,
    )
    result = evaluate_authority(
        actor=actor,
        request=request,
        grants=tuple(_grant_fact(item) for item in grants),
        qualifications=tuple(
            fact
            for qualification in qualifications
            for fact in _qualification_facts(qualification)
        ),
        substitutions=tuple(_substitution_fact(item) for item in substitutions),
        external_engagements=tuple(_engagement_fact(item) for item in engagements),
    )

    grant_by_public_id = {str(item.public_id): item for item in grants}
    matched_grant = grant_by_public_id.get(result.matched_grant_id)
    snapshot = json.loads(canonical_json(dict(result.snapshot)))

    record = AuthorityEvaluationRecord(
        organization=organization,
        actor=employee,
        action_code=request.action_code,
        occurred_at=request.occurred_at,
        scope_kind=request.scope.kind.value,
        scope_reference=request.scope.reference,
        scope_label=request.scope.label,
        subject_type=request.subject_type,
        subject_id=request.subject_id,
        decision=result.decision.value,
        reasons=[reason.value for reason in result.reasons],
        matched_grant=matched_grant,
        snapshot=snapshot,
        previous_evaluation=previous_evaluation,
        recorded_by=recorded_by,
    )
    record.save()
    return record
