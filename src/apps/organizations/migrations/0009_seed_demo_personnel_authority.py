from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, date, datetime

from django.db import migrations

VALID_FROM = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
VALID_UNTIL = datetime(2026, 12, 31, 23, 59, tzinfo=UTC)
SCOPE_KIND = "OPERATIONAL_AREA"
SCOPE_REFERENCE = "KOCH"
SCOPE_LABEL = "Кочубеевская ВЭС — демонстрационная область"
SUBJECT_TYPE = "DEMO_SCENARIO"
DEMO_SUBJECT_IDS = (
    "DEMO-AUTH-ALLOW",
    "DEMO-AUTH-DENY",
    "DEMO-AUTH-VERIFY",
    "DEMO-AUTH-EXTERNAL",
)


def _digest(payload) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _grant(
    OperationalAuthorityGrant,
    *,
    host,
    employee,
    right_definition,
    action_code,
    basis_status,
    basis_reference,
    created_by,
    allow_substitution=False,
):
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
            "source_ids": ["DEMO-SYNTHETIC", "SRC-DEC-STAGE2"],
            "valid_until": VALID_UNTIL,
            "is_active": True,
            "allow_substitution": allow_substitution,
            "created_by": created_by,
        },
    )
    return grant


def _snapshot(
    *,
    employee,
    host,
    action_code,
    occurred_at,
    subject_id,
    decision,
    reasons,
    grant=None,
    relation_kind="EMPLOYEE",
    external_engagement=None,
):
    snapshot = {
        "actor": {
            "employee_id": employee.id,
            "organization_id": employee.organization_id,
            "relation_kind": relation_kind,
            "full_name": " ".join(
                part
                for part in (
                    employee.last_name,
                    employee.first_name,
                    employee.middle_name,
                )
                if part
            ),
            "position": employee.position.name,
            "division": employee.division.name,
            "workplace": employee.workplace.name if employee.workplace_id else "",
            "application_roles": [],
        },
        "request": {
            "organization_id": host.id,
            "actor_employee_id": employee.id,
            "action_code": action_code,
            "occurred_at": occurred_at.isoformat().replace("+00:00", "Z"),
            "scope": {
                "kind": SCOPE_KIND,
                "reference": SCOPE_REFERENCE,
                "label": SCOPE_LABEL,
            },
            "subject_type": SUBJECT_TYPE,
            "subject_id": subject_id,
            "required_qualification_codes": [],
        },
        "grant": None,
        "substitution": None,
        "external_engagement": external_engagement,
        "qualifications": [],
        "decision": decision,
        "reasons": reasons,
    }
    if grant is not None:
        snapshot["grant"] = {
            "grant_id": str(grant.public_id),
            "employee_id": grant.employee_id,
            "organization_id": grant.organization_id,
            "action_code": grant.action_code,
            "scope": {
                "kind": grant.scope_kind,
                "reference": grant.scope_reference,
                "label": grant.scope_label,
            },
            "valid_from": grant.valid_from.isoformat().replace("+00:00", "Z"),
            "valid_until": grant.valid_until.isoformat().replace("+00:00", "Z"),
            "basis_status": grant.basis_status,
            "basis_reference": grant.basis_reference,
            "source_ids": grant.source_ids,
            "allow_substitution": grant.allow_substitution,
        }
    return snapshot


def _evaluation(
    AuthorityEvaluationRecord,
    *,
    host,
    employee,
    action_code,
    occurred_at,
    subject_id,
    decision,
    reasons,
    recorded_by,
    grant=None,
    relation_kind="EMPLOYEE",
    external_engagement=None,
):
    snapshot = _snapshot(
        employee=employee,
        host=host,
        action_code=action_code,
        occurred_at=occurred_at,
        subject_id=subject_id,
        decision=decision,
        reasons=reasons,
        grant=grant,
        relation_kind=relation_kind,
        external_engagement=external_engagement,
    )
    payload = {
        "schema": "eod.personnel-authority.evaluation.v1",
        "decision": decision,
        "reasons": reasons,
        "matched_grant_id": str(grant.public_id) if grant is not None else "",
        "snapshot": snapshot,
    }
    AuthorityEvaluationRecord.objects.update_or_create(
        organization=host,
        actor=employee,
        subject_type=SUBJECT_TYPE,
        subject_id=subject_id,
        occurred_at=occurred_at,
        defaults={
            "public_id": uuid.uuid4(),
            "action_code": action_code,
            "scope_kind": SCOPE_KIND,
            "scope_reference": SCOPE_REFERENCE,
            "scope_label": SCOPE_LABEL,
            "decision": decision,
            "reasons": reasons,
            "matched_grant": grant,
            "snapshot": snapshot,
            "digest": _digest(payload),
            "recorded_by": recorded_by,
        },
    )


def seed_demo_authority(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    Division = apps.get_model("organizations", "Division")
    Position = apps.get_model("organizations", "Position")
    Workplace = apps.get_model("organizations", "Workplace")
    Employee = apps.get_model("organizations", "Employee")
    OperationalRightDefinition = apps.get_model(
        "organizations",
        "OperationalRightDefinition",
    )
    OperationalAuthorityGrant = apps.get_model(
        "organizations",
        "OperationalAuthorityGrant",
    )
    ExternalPersonnelEngagement = apps.get_model(
        "organizations",
        "ExternalPersonnelEngagement",
    )
    AuthorityEvaluationRecord = apps.get_model(
        "organizations",
        "AuthorityEvaluationRecord",
    )

    host = Organization.objects.filter(code="DEMO").first()
    if host is None:
        return

    employees = {
        employee.personnel_number: employee
        for employee in Employee.objects.filter(
            organization=host,
            personnel_number__in=("DEMO-001", "DEMO-002", "DEMO-003", "DEMO-013"),
        ).select_related("division", "position", "workplace")
    }
    if set(employees) != {"DEMO-001", "DEMO-002", "DEMO-003", "DEMO-013"}:
        return

    right_definition = OperationalRightDefinition.objects.filter(
        code="switching_operation"
    ).first()
    if right_definition is None:
        return

    supervisor = employees["DEMO-002"]
    execution_grant = _grant(
        OperationalAuthorityGrant,
        host=host,
        employee=employees["DEMO-001"],
        right_definition=right_definition,
        action_code="SWITCHING.EXECUTE",
        basis_status="CONFIRMED",
        basis_reference="DEMO-ONLY / EXECUTION-AUTHORITY / R1",
        created_by=supervisor,
    )
    _grant(
        OperationalAuthorityGrant,
        host=host,
        employee=supervisor,
        right_definition=right_definition,
        action_code="SWITCHING.CONTROL",
        basis_status="CONFIRMED",
        basis_reference="DEMO-ONLY / CONTROL-AUTHORITY / R1",
        created_by=supervisor,
        allow_substitution=True,
    )
    verify_grant = _grant(
        OperationalAuthorityGrant,
        host=host,
        employee=employees["DEMO-003"],
        right_definition=right_definition,
        action_code="SWITCHING.AUTHORIZE",
        basis_status="VERIFY",
        basis_reference="DEMO-ONLY / UNCONFIRMED-AUTHORITY / R1",
        created_by=supervisor,
    )

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
        defaults={"name": "Выездная сервисная группа", "is_active": True},
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
    contractor, _ = Employee.objects.update_or_create(
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
    engagement, _ = ExternalPersonnelEngagement.objects.update_or_create(
        employee=contractor,
        host_organization=host,
        scope_kind=SCOPE_KIND,
        scope_reference=SCOPE_REFERENCE,
        valid_from=VALID_FROM,
        defaults={
            "home_organization": home,
            "relation_kind": "CONTRACTOR",
            "scope_label": SCOPE_LABEL,
            "valid_until": VALID_UNTIL,
            "basis_status": "CONFIRMED",
            "basis_reference": "DEMO-ONLY / CONTRACTOR-ADMISSION / R1",
            "source_ids": ["DEMO-SYNTHETIC", "REF-OD-052"],
            "is_active": True,
            "created_by": supervisor,
        },
    )
    external_grant = _grant(
        OperationalAuthorityGrant,
        host=host,
        employee=contractor,
        right_definition=right_definition,
        action_code="EQUIPMENT.INSPECT",
        basis_status="CONFIRMED",
        basis_reference="DEMO-ONLY / CONTRACTOR-ADMISSION / R1",
        created_by=supervisor,
    )

    _evaluation(
        AuthorityEvaluationRecord,
        host=host,
        employee=employees["DEMO-001"],
        action_code="SWITCHING.EXECUTE",
        occurred_at=datetime(2026, 8, 1, 7, 0, tzinfo=UTC),
        subject_id="DEMO-AUTH-ALLOW",
        decision="ALLOW",
        reasons=["EXPLICIT_GRANT"],
        recorded_by=supervisor,
        grant=execution_grant,
    )
    _evaluation(
        AuthorityEvaluationRecord,
        host=host,
        employee=employees["DEMO-013"],
        action_code="SWITCHING.EXECUTE",
        occurred_at=datetime(2026, 8, 1, 7, 5, tzinfo=UTC),
        subject_id="DEMO-AUTH-DENY",
        decision="DENY",
        reasons=["SUBSTITUTION_NOT_ALLOWED"],
        recorded_by=supervisor,
    )
    _evaluation(
        AuthorityEvaluationRecord,
        host=host,
        employee=employees["DEMO-003"],
        action_code="SWITCHING.AUTHORIZE",
        occurred_at=datetime(2026, 8, 1, 7, 10, tzinfo=UTC),
        subject_id="DEMO-AUTH-VERIFY",
        decision="VERIFY",
        reasons=["BASIS_VERIFY"],
        recorded_by=supervisor,
        grant=verify_grant,
    )
    _evaluation(
        AuthorityEvaluationRecord,
        host=host,
        employee=contractor,
        action_code="EQUIPMENT.INSPECT",
        occurred_at=datetime(2026, 8, 1, 7, 15, tzinfo=UTC),
        subject_id="DEMO-AUTH-EXTERNAL",
        decision="ALLOW",
        reasons=["EXPLICIT_GRANT"],
        recorded_by=supervisor,
        grant=external_grant,
        relation_kind="CONTRACTOR",
        external_engagement={
            "engagement_id": str(engagement.public_id),
            "home_organization_id": home.id,
            "host_organization_id": host.id,
            "relation_kind": "CONTRACTOR",
            "scope": {
                "kind": SCOPE_KIND,
                "reference": SCOPE_REFERENCE,
                "label": SCOPE_LABEL,
            },
            "basis_status": "CONFIRMED",
            "basis_reference": engagement.basis_reference,
        },
    )


def remove_demo_authority(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    Employee = apps.get_model("organizations", "Employee")
    AuthorityEvaluationRecord = apps.get_model(
        "organizations",
        "AuthorityEvaluationRecord",
    )
    OperationalAuthorityGrant = apps.get_model(
        "organizations",
        "OperationalAuthorityGrant",
    )
    ExternalPersonnelEngagement = apps.get_model(
        "organizations",
        "ExternalPersonnelEngagement",
    )

    AuthorityEvaluationRecord.objects.filter(
        subject_type=SUBJECT_TYPE,
        subject_id__in=DEMO_SUBJECT_IDS,
    ).delete()
    OperationalAuthorityGrant.objects.filter(
        basis_reference__startswith="DEMO-ONLY /"
    ).delete()
    ExternalPersonnelEngagement.objects.filter(
        basis_reference="DEMO-ONLY / CONTRACTOR-ADMISSION / R1"
    ).delete()
    Employee.objects.filter(
        organization__code="DEMO-CONTRACTOR",
        personnel_number="DEMO-EXT-001",
    ).delete()
    Organization.objects.filter(code="DEMO-CONTRACTOR").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0008_personnel_authority_persistence"),
    ]

    operations = [
        migrations.RunPython(seed_demo_authority, remove_demo_authority),
    ]
