from django.db import migrations, models


# This migration expands serialized choices only; stored registry values are unchanged.
TARGET_CHOICES = (
    ("ORGANIZATION", "Организация и персонал"),
    (
        "ORGANIZATION_STRUCTURE",
        "Организационная структура и энергообъекты",
    ),
    ("EQUIPMENT", "Оборудование"),
    ("DISPATCHING", "Управление и ведение"),
    ("OTHER", "Другой справочник"),
)


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0008_workplace_document_target_workplace_context"),
    ]

    operations = [
        migrations.AlterField(
            model_name="importmappingtemplate",
            name="target_registry",
            field=models.CharField(
                choices=TARGET_CHOICES,
                max_length=24,
                verbose_name="Назначение импорта",
            ),
        ),
        migrations.AlterField(
            model_name="importbatch",
            name="target_registry",
            field=models.CharField(
                choices=TARGET_CHOICES,
                max_length=24,
                verbose_name="Назначение импорта",
            ),
        ),
        migrations.AlterField(
            model_name="importpublication",
            name="target_registry",
            field=models.CharField(
                choices=TARGET_CHOICES,
                max_length=24,
                verbose_name="Назначение",
            ),
        ),
    ]
