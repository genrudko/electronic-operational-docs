from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("workplace_docs", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="workplacedocumententry",
            name="storage_form",
            field=models.CharField(
                choices=[
                    ("UNKNOWN", "Не определена"),
                    ("PAPER", "Бумажная"),
                    ("ELECTRONIC", "Электронная"),
                    ("MIXED", "Смешанная"),
                ],
                max_length=16,
                verbose_name="Форма хранения",
            ),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="approval_date",
            field=models.DateField(blank=True, null=True, verbose_name="Дата утверждения позиции"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="approver_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Утвердивший по источнику"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="approving_role",
            field=models.CharField(blank=True, max_length=255, verbose_name="Должность утвердившего"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="document_type_label",
            field=models.CharField(blank=True, max_length=255, verbose_name="Тип документа из источника"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="electronic_storage_interpretation",
            field=models.CharField(
                choices=[
                    ("INDICATED", "Электронная форма указана"),
                    ("NOT_INDICATED", "Электронная форма не указана"),
                    ("UNKNOWN", "Не удалось определить"),
                ],
                default="UNKNOWN",
                max_length=24,
                verbose_name="Интерпретация электронной формы",
            ),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="electronic_storage_mark",
            field=models.CharField(
                blank=True,
                max_length=16,
                verbose_name="Отметка электронной формы из источника",
            ),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="review_interval_months",
            field=models.PositiveSmallIntegerField(
                blank=True,
                null=True,
                verbose_name="Нормализованный период пересмотра, месяцев",
            ),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="review_period_raw",
            field=models.CharField(blank=True, max_length=255, verbose_name="Периодичность из источника"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="section_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Наименование раздела"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="section_no",
            field=models.CharField(blank=True, max_length=32, verbose_name="Номер раздела источника"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="source_document_no",
            field=models.CharField(blank=True, max_length=64, verbose_name="Номер документа в разделе"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="source_pdf_page",
            field=models.PositiveSmallIntegerField(blank=True, null=True, verbose_name="Страница источника"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="source_register_entry_no",
            field=models.PositiveIntegerField(
                blank=True,
                null=True,
                verbose_name="Сквозной номер позиции источника",
            ),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="subsection_name",
            field=models.CharField(blank=True, max_length=255, verbose_name="Наименование подраздела"),
        ),
        migrations.AddField(
            model_name="workplacedocumententry",
            name="subsection_no",
            field=models.CharField(blank=True, max_length=32, verbose_name="Номер подраздела источника"),
        ),
    ]
