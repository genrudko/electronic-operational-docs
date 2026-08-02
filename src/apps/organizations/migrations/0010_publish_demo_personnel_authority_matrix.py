from __future__ import annotations

import importlib

from django.core.management import call_command
from django.db import migrations

SOURCE_HASH = "d" * 64
MATRIX_SUBJECT_IDS = (
    "DEMO-AUTH-VERIFY-MATRIX-CONDITION",
)


def publish_demo_matrix(apps, schema_editor) -> None:
    organization = apps.get_model("organizations", "Organization")
    if not organization.objects.filter(code="DEMO").exists():
        return
    call_command("seed_demo_personnel_authority", verbosity=0)


def unpublish_demo_matrix(apps, schema_editor) -> None:
    source_right = apps.get_model(
        "organizations",
        "EmployeeOperationalRight",
    )
    qualification = apps.get_model(
        "organizations",
        "EmployeeQualification",
    )
    grant = apps.get_model(
        "organizations",
        "OperationalAuthorityGrant",
    )
    record = apps.get_model(
        "organizations",
        "AuthorityEvaluationRecord",
    )

    published_rights = source_right.objects.filter(
        source_file_sha256=SOURCE_HASH,
    )
    record.objects.filter(
        subject_type="DEMO_SCENARIO",
        subject_id__in=MATRIX_SUBJECT_IDS,
    ).delete()
    grant.objects.filter(
        source_operational_right__in=published_rights,
    ).delete()
    published_rights.delete()
    qualification.objects.filter(
        source_file_sha256=SOURCE_HASH,
    ).delete()

    previous_seed = importlib.import_module(
        "apps.organizations.migrations.0009_seed_demo_personnel_authority"
    )
    previous_seed.seed_demo_authority(apps, schema_editor)


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0009_seed_demo_personnel_authority"),
    ]

    operations = [
        migrations.RunPython(
            publish_demo_matrix,
            unpublish_demo_matrix,
        ),
    ]
