from __future__ import annotations

from django.db import migrations, models

EDITOR_SCHEMA_VERSION = "operational-draft-editor.v2"


class Migration(migrations.Migration):
    dependencies = [
        ("operational_log", "0003_draft_editor_payload"),
    ]

    operations = [
        migrations.AlterField(
            model_name="operationaldraftentry",
            name="editor_schema_version",
            field=models.CharField(
                default=EDITOR_SCHEMA_VERSION,
                editable=False,
                max_length=64,
                verbose_name="Версия структуры редактора",
            ),
        ),
    ]
