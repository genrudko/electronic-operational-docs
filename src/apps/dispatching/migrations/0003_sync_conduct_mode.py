from django.db import migrations


def forwards(apps, schema_editor):
    revision = apps.get_model("dispatching", "SupervisionRevision")
    revision.objects.filter(is_information_only=True).update(
        conduct_mode="INFORMATIONAL"
    )
    revision.objects.filter(is_information_only=False).update(
        conduct_mode="OPERATIONAL"
    )


def backwards(apps, schema_editor):
    revision = apps.get_model("dispatching", "SupervisionRevision")
    revision.objects.filter(conduct_mode="INFORMATIONAL").update(
        is_information_only=True
    )
    revision.objects.exclude(conduct_mode="INFORMATIONAL").update(
        is_information_only=False
    )


class Migration(migrations.Migration):
    dependencies = [
        (
            "dispatching",
            "0002_patch_011_5_power_system_asset_importer",
        ),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
