from __future__ import annotations

from django.db import migrations, models

EDITOR_SCHEMA_VERSION = "operational-draft-editor.v1"


def backfill_editor_payload(apps, schema_editor) -> None:
    draft_model = apps.get_model(
        "operational_log",
        "OperationalDraftEntry",
    )
    for entry in draft_model.objects.all().iterator(chunk_size=200):
        content = (entry.content or "").replace("\r\n", "\n").replace(
            "\r",
            "\n",
        )
        blocks = []
        for line in content.split("\n"):
            blocks.append(
                {
                    "type": "paragraph",
                    "segments": (
                        [{"text": line, "marks": []}] if line else []
                    ),
                }
            )
        draft_model.objects.filter(pk=entry.pk).update(
            editor_schema_version=EDITOR_SCHEMA_VERSION,
            editor_payload={
                "schema_version": EDITOR_SCHEMA_VERSION,
                "blocks": blocks
                or [{"type": "paragraph", "segments": []}],
            },
        )


class Migration(migrations.Migration):
    dependencies = [
        ("operational_log", "0002_operational_shift_draft"),
    ]

    operations = [
        migrations.AddField(
            model_name="operationaldraftentry",
            name="editor_schema_version",
            field=models.CharField(
                default=EDITOR_SCHEMA_VERSION,
                editable=False,
                max_length=64,
                verbose_name="Версия структуры редактора",
            ),
        ),
        migrations.AddField(
            model_name="operationaldraftentry",
            name="editor_payload",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Структура редактора",
            ),
        ),
        migrations.RunPython(
            backfill_editor_payload,
            migrations.RunPython.noop,
        ),
    ]
