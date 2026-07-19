from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "operational_log",
            "0004_alter_operationaldraftentry_editor_schema_version",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="operationaldraftentry",
            name="editor_schema_version",
            field=models.CharField(
                default="operational-draft-editor.v3",
                editable=False,
                max_length=64,
                verbose_name="Версия структуры редактора",
            ),
        ),
    ]
