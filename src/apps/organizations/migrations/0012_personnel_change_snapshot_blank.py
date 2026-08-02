from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0011_personnel_management"),
    ]

    operations = [
        migrations.AlterField(
            model_name="personnelchangerecord",
            name="before_snapshot",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Состояние до изменения",
            ),
        ),
        migrations.AlterField(
            model_name="personnelchangerecord",
            name="after_snapshot",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Состояние после изменения",
            ),
        ),
        migrations.AlterField(
            model_name="personnelimportbatch",
            name="validation_errors",
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name="Ошибки проверки",
            ),
        ),
    ]
