from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0007_workplace_document_register_importer"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="workplacedocumentsourcerevision",
            name="uniq_workdoc_source_context",
        ),
        migrations.AddConstraint(
            model_name="workplacedocumentsourcerevision",
            constraint=models.UniqueConstraint(
                fields=(
                    "organization",
                    "file_sha256",
                    "source_reference",
                    "effective_from",
                    "list_review_period_months",
                    "matched_workplace",
                ),
                name="uniq_workdoc_src_context_wp",
            ),
        ),
    ]
