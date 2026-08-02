import hashlib

from django.db import migrations


DEMO_CODES = (
    "DEMO-ODU-YUG",
    "DEMO-SK-RDU",
    "DEMO-SK-PMES",
    "DEMO-PS500-NEV",
    "DEMO-KDC-VES",
)


def stable_code(prefix, organization_code, name):
    payload = f"{organization_code}|{name.strip().casefold()}"
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"


def stabilize_codes(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    Division = apps.get_model("organizations", "Division")
    Position = apps.get_model("organizations", "Position")

    organizations = Organization.objects.filter(code__in=DEMO_CODES)
    for organization in organizations:
        for division in Division.objects.filter(organization=organization):
            division.code = stable_code("DIV", organization.code, division.name)
            division.save(update_fields=("code",))
        for position in Position.objects.filter(organization=organization):
            position.code = stable_code("POS", organization.code, position.name)
            position.save(update_fields=("code",))


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0014_seed_demo_external_operational_directories"),
    ]

    operations = [
        migrations.RunPython(stabilize_codes, migrations.RunPython.noop),
    ]
