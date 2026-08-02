from __future__ import annotations

from datetime import UTC, datetime, time, timedelta

from django.db import transaction

from .authority_models import (
    AuthorityBasisStatus,
    AuthorityScopeKind,
    OperationalAuthorityGrant,
)
from .models import Employee, EmployeeOperationalRight, EmployeeQualification
from .personnel_management_models import (
    EmployeeSpecialQualification,
    ExternalOperationalContact,
    PersonnelChangeAction,
)
from .personnel_management_services import (
    RIGHT_ACTION_CODES,
    employee_snapshot,
    manual_source_hash,
    record_personnel_change,
)


def _actor_employee(user, organization_id: int) -> Employee | None:
    employee = getattr(user, "employee_profile", None)
    if employee and employee.organization_id == organization_id:
        return employee
    return None


def _close_date_record(record, new_start) -> None:
    record.is_active = False
    if record.valid_until is None or record.valid_until >= new_start:
        record.valid_until = max(record.valid_from, new_start - timedelta(days=1))
    record.save()


@transaction.atomic
def replace_electrical_qualification(
    *,
    employee: Employee,
    cleaned_data: dict,
    user,
    existing: EmployeeQualification | None = None,
) -> EmployeeQualification:
    before = employee_snapshot(employee)
    if existing and existing.is_active:
        _close_date_record(existing, cleaned_data["valid_from"])
    source_hash = manual_source_hash(
        employee=employee,
        record_kind="ELECTRICAL_QUALIFICATION",
        basis=cleaned_data["source_reference"],
    )
    qualification = EmployeeQualification.objects.create(
        employee=employee,
        personnel_category=cleaned_data["personnel_category"],
        electrical_safety_group=cleaned_data["electrical_safety_group"],
        voltage_scope=cleaned_data["voltage_scope"],
        electrical_installation_scope=cleaned_data["electrical_installation_scope"],
        valid_from=cleaned_data["valid_from"],
        valid_until=cleaned_data.get("valid_until"),
        is_active=cleaned_data.get("is_active", True),
        source_reference=cleaned_data["source_reference"],
        source_file_sha256=source_hash,
        source_row_number=0,
    )
    record_personnel_change(
        user=user,
        employee=employee,
        action=PersonnelChangeAction.QUALIFICATION,
        reason=cleaned_data["change_reason"],
        before=before,
        after=employee_snapshot(employee),
    )
    return qualification


@transaction.atomic
def replace_special_qualification(
    *,
    employee: Employee,
    cleaned_data: dict,
    user,
    existing: EmployeeSpecialQualification | None = None,
) -> EmployeeSpecialQualification:
    before = employee_snapshot(employee)
    if existing and existing.is_active:
        _close_date_record(existing, cleaned_data["valid_from"])
    source_hash = manual_source_hash(
        employee=employee,
        record_kind=f"SPECIAL_QUALIFICATION:{cleaned_data['kind']}",
        basis=cleaned_data["basis_reference"],
    )
    qualification = EmployeeSpecialQualification.objects.create(
        employee=employee,
        kind=cleaned_data["kind"],
        level=cleaned_data["level"],
        scope_text=cleaned_data.get("scope_text", ""),
        valid_from=cleaned_data["valid_from"],
        valid_until=cleaned_data.get("valid_until"),
        basis_reference=cleaned_data["basis_reference"],
        source_file_sha256=source_hash,
        source_row_number=0,
        is_active=cleaned_data.get("is_active", True),
    )
    record_personnel_change(
        user=user,
        employee=employee,
        action=PersonnelChangeAction.QUALIFICATION,
        reason=cleaned_data["change_reason"],
        before=before,
        after=employee_snapshot(employee),
    )
    return qualification


@transaction.atomic
def replace_operational_right(
    *,
    employee: Employee,
    cleaned_data: dict,
    user,
    existing: EmployeeOperationalRight | None = None,
) -> EmployeeOperationalRight:
    before = employee_snapshot(employee)
    if existing and existing.is_active:
        _close_date_record(existing, cleaned_data["valid_from"])
        for grant in existing.published_structured_grants.filter(is_active=True):
            grant.is_active = False
            grant.save(update_fields=("is_active",))
    source_hash = manual_source_hash(
        employee=employee,
        record_kind=f"OPERATIONAL_RIGHT:{cleaned_data['right_definition'].code}",
        basis=cleaned_data["source_reference"],
    )
    source_right = EmployeeOperationalRight.objects.create(
        employee=employee,
        right_definition=cleaned_data["right_definition"],
        qualifier=cleaned_data.get("qualifier", ""),
        scope_text=cleaned_data.get("scope_text", ""),
        source_marker=cleaned_data["source_marker"],
        source_reference=cleaned_data["source_reference"],
        source_file_sha256=source_hash,
        source_row_number=0,
        valid_from=cleaned_data["valid_from"],
        valid_until=cleaned_data.get("valid_until"),
        is_active=cleaned_data.get("is_active", True),
    )
    definition = source_right.right_definition
    action_code = RIGHT_ACTION_CODES.get(
        definition.code,
        f"PERSONNEL.RIGHT.{definition.code.upper()}",
    )
    marker = source_right.source_marker.strip()
    start = datetime.combine(source_right.valid_from, time.min, tzinfo=UTC)
    end = (
        datetime.combine(source_right.valid_until, time.max, tzinfo=UTC)
        if source_right.valid_until
        else None
    )
    OperationalAuthorityGrant.objects.create(
        organization=employee.organization,
        employee=employee,
        right_definition=definition,
        action_code=action_code,
        scope_kind=AuthorityScopeKind.ORGANIZATION,
        scope_reference=str(employee.organization_id),
        scope_label=source_right.scope_text or employee.organization.name,
        granting_organization=employee.organization,
        basis_status=(
            AuthorityBasisStatus.CONFIRMED
            if marker == "+"
            else AuthorityBasisStatus.VERIFY
        ),
        basis_reference=source_right.source_reference,
        source_ids=["MANUAL-PERSONNEL-CARD", definition.code],
        source_operational_right=source_right,
        valid_from=start,
        valid_until=end,
        is_active=source_right.is_active,
        allow_substitution=False,
        created_by=_actor_employee(user, employee.organization_id),
    )
    record_personnel_change(
        user=user,
        employee=employee,
        action=PersonnelChangeAction.RIGHT,
        reason=cleaned_data["change_reason"],
        before=before,
        after=employee_snapshot(employee),
    )
    return source_right


@transaction.atomic
def replace_external_contact(
    *,
    employee: Employee,
    cleaned_data: dict,
    user,
    existing: ExternalOperationalContact | None = None,
) -> ExternalOperationalContact:
    before = employee_snapshot(employee)
    if existing and existing.is_active:
        _close_date_record(existing, cleaned_data["valid_from"])
    contact = ExternalOperationalContact.objects.create(
        employee=employee,
        host_organization=cleaned_data["host_organization"],
        relation_kind=cleaned_data["relation_kind"],
        operational_scope=cleaned_data.get("operational_scope", ""),
        authority_summary=cleaned_data.get("authority_summary", ""),
        valid_from=cleaned_data["valid_from"],
        valid_until=cleaned_data.get("valid_until"),
        basis_reference=cleaned_data["basis_reference"],
        is_active=cleaned_data.get("is_active", True),
    )
    record_personnel_change(
        user=user,
        employee=employee,
        action=PersonnelChangeAction.UPDATE,
        reason=cleaned_data["change_reason"],
        before=before,
        after=employee_snapshot(employee),
    )
    return contact


@transaction.atomic
def deactivate_employee(*, employee: Employee, user, reason: str) -> None:
    before = employee_snapshot(employee)
    employee.is_active = False
    if employee.employment_end is None:
        employee.employment_end = datetime.now(tz=UTC).date()
    employee.save(update_fields=("is_active", "employment_end"))
    employee.qualifications.filter(is_active=True).update(is_active=False)
    employee.special_qualifications.filter(is_active=True).update(is_active=False)
    employee.operational_rights.filter(is_active=True).update(is_active=False)
    employee.structured_authority_grants.filter(is_active=True).update(is_active=False)
    employee.external_operational_contacts.filter(is_active=True).update(is_active=False)
    record_personnel_change(
        user=user,
        employee=employee,
        action=PersonnelChangeAction.DEACTIVATE,
        reason=reason,
        before=before,
        after=employee_snapshot(employee),
    )
