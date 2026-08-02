from __future__ import annotations

from datetime import UTC, datetime

from django.db import migrations

VALID_FROM = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
VALID_UNTIL = datetime(2027, 12, 31, 23, 59, tzinfo=UTC)
ACTION_CODES = (
    "OPJ.REGISTER",
    "OPJ.CORRECT",
    "OPJ.CANCEL",
    "OPJ.COMMUNICATION",
)


def seed_demo_opj_authority(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    Employee = apps.get_model("organizations", "Employee")
    Right = apps.get_model("organizations", "OperationalRightDefinition")
    Grant = apps.get_model("organizations", "OperationalAuthorityGrant")

    organization = Organization.objects.filter(code="DEMO").first()
    if organization is None:
        return

    right, _ = Right.objects.update_or_create(
        code="operational_journal_actions",
        defaults={
            "name": "Ведение оперативного журнала и оперативных переговоров",
            "category": "COMMUNICATIONS",
            "value_kind": "QUALIFIED",
            "description": (
                "Демонстрационное структурированное право на регистрацию, "
                "исправление и отмену записей ОЖ, а также фиксацию переговоров."
            ),
            "display_order": 35,
            "is_active": True,
        },
    )

    employees = list(
        Employee.objects.filter(
            organization=organization,
            personnel_number__in=("DEMO-001", "DEMO-002", "DEMO-003"),
            is_active=True,
            workplace__isnull=False,
        ).select_related("workplace")
    )
    for employee in employees:
        basis_status = (
            "CONFIRMED"
            if employee.personnel_number in {"DEMO-001", "DEMO-002"}
            else "VERIFY"
        )
        basis_reference = (
            "DEMO-ONLY / OPJ-LIFECYCLE-001 / R1"
            if basis_status == "CONFIRMED"
            else "DEMO-ONLY / OPJ-LIFECYCLE-001 / VERIFY"
        )
        for action_code in ACTION_CODES:
            Grant.objects.update_or_create(
                employee=employee,
                action_code=action_code,
                scope_kind="WORKPLACE",
                scope_reference=str(employee.workplace_id),
                valid_from=VALID_FROM,
                basis_reference=basis_reference,
                defaults={
                    "organization": organization,
                    "right_definition": right,
                    "scope_label": employee.workplace.name,
                    "granting_organization": organization,
                    "basis_status": basis_status,
                    "source_ids": [
                        "DEMO-SYNTHETIC",
                        "OPJ-LIFECYCLE-001",
                    ],
                    "valid_until": VALID_UNTIL,
                    "is_active": True,
                    "allow_substitution": False,
                    "created_by": None,
                },
            )


def remove_demo_opj_authority(apps, schema_editor):
    Grant = apps.get_model("organizations", "OperationalAuthorityGrant")
    Right = apps.get_model("organizations", "OperationalRightDefinition")
    Grant.objects.filter(
        action_code__in=ACTION_CODES,
        basis_reference__startswith="DEMO-ONLY / OPJ-LIFECYCLE-001",
    ).delete()
    Right.objects.filter(code="operational_journal_actions").delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0015_stabilize_demo_external_directory_codes"),
    ]

    operations = [
        migrations.RunPython(
            seed_demo_opj_authority,
            remove_demo_opj_authority,
        ),
    ]
