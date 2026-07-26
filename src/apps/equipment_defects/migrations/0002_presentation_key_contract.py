from django.db import migrations, models
from django.db.models import Q


def normalize_presentation_keys(apps, schema_editor):
    del schema_editor
    context_model = apps.get_model("equipment_defects", "EquipmentDefectContext")
    context_model.objects.filter(presentation_key__isnull=True).update(presentation_key="")


class Migration(migrations.Migration):
    dependencies = [
        ("equipment_defects", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(
            normalize_presentation_keys,
            reverse_code=migrations.RunPython.noop,
        ),
        migrations.AlterField(
            model_name="equipmentdefectcontext",
            name="presentation_key",
            field=models.CharField(
                blank=True,
                default="",
                editable=False,
                max_length=96,
                verbose_name="Ключ презентационных данных",
            ),
        ),
        migrations.AddConstraint(
            model_name="equipmentdefectcontext",
            constraint=models.UniqueConstraint(
                condition=~Q(presentation_key=""),
                fields=("presentation_key",),
                name="uniq_defect_presentation_key",
            ),
        ),
    ]
