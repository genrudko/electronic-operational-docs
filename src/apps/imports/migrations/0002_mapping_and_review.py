# Generated for Patch 008.2.

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0001_initial"),
        ("organizations", "0003_operational_structure"),
    ]

    operations = [
        migrations.AddField(
            model_name="importbatch",
            name="mapping_revision",
            field=models.PositiveIntegerField(
                default=0,
                verbose_name="Редакция сопоставления",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="mapping_completed_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Сопоставление подтверждено",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="review_recalculated_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Проверка строк пересчитана",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="review_counts",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Счётчики ручной проверки",
            ),
        ),
        migrations.AlterField(
            model_name="importbatch",
            name="status",
            field=models.CharField(
                choices=[
                    ("PROCESSING", "Обрабатывается"),
                    ("READY", "Предварительный просмотр готов"),
                    ("FAILED", "Ошибка разбора"),
                    ("DISCARDED", "Убрано из рабочего списка"),
                ],
                default="PROCESSING",
                max_length=16,
                verbose_name="Состояние",
            ),
        ),
        migrations.AlterField(
            model_name="importbatch",
            name="discarded_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Убрано из рабочего списка",
            ),
        ),
        migrations.AddField(
            model_name="importcolumn",
            name="mapped_key",
            field=models.CharField(
                blank=True,
                max_length=64,
                verbose_name="Назначенное поле",
            ),
        ),
        migrations.AddField(
            model_name="importcolumn",
            name="mapping_origin",
            field=models.CharField(
                choices=[
                    ("AUTO", "Предложено автоматически"),
                    ("MANUAL", "Назначено пользователем"),
                    ("IGNORED", "Не используется"),
                ],
                default="AUTO",
                max_length=12,
                verbose_name="Источник сопоставления",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="mapped_values",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Сопоставленные значения",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="review_status",
            field=models.CharField(
                choices=[
                    ("NOT_MAPPED", "Сопоставление не подтверждено"),
                    ("VALID", "Готова к решению"),
                    ("REVIEW", "Нужна ручная проверка"),
                    ("CONFLICT", "Обнаружен конфликт"),
                    ("INVALID", "Есть ошибки"),
                ],
                default="NOT_MAPPED",
                max_length=16,
                verbose_name="Состояние ручной проверки",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="validation_issues",
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name="Ошибки проверки",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="registry_conflicts",
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name="Конфликты с реестрами",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="decision",
            field=models.CharField(
                choices=[
                    ("PENDING", "Решение не принято"),
                    ("ACCEPTED", "Принята предварительно"),
                    ("REJECTED", "Отклонена пользователем"),
                ],
                default="PENDING",
                max_length=12,
                verbose_name="Предварительное решение",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="decision_values",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Исправленные значения решения",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="decision_note",
            field=models.TextField(
                blank=True,
                verbose_name="Комментарий к решению",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="decided_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Время решения",
            ),
        ),
        migrations.AddField(
            model_name="importrow",
            name="decided_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="decided_import_rows",
                to="organizations.employee",
                verbose_name="Решение принял",
            ),
        ),
        migrations.AlterField(
            model_name="importrow",
            name="status",
            field=models.CharField(
                choices=[
                    ("NEW", "Новая"),
                    ("RECOGNIZED", "Распознана"),
                    ("REVIEW", "Требует проверки"),
                    ("CONFLICT", "Конфликт"),
                    ("REJECTED", "Отклонена"),
                ],
                max_length=16,
                verbose_name="Состояние строки источника",
            ),
        ),
        migrations.AlterField(
            model_name="importrow",
            name="issues",
            field=models.JSONField(
                blank=True,
                default=list,
                verbose_name="Замечания разбора",
            ),
        ),
        migrations.AddIndex(
            model_name="importrow",
            index=models.Index(
                fields=["batch", "review_status", "decision"],
                name="imp_row_review_idx",
            ),
        ),
        migrations.AlterField(
            model_name="importevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("UPLOADED", "Файл загружен"),
                    ("PARSED", "Предварительный просмотр сформирован"),
                    ("FAILED", "Разбор завершился ошибкой"),
                    ("DISCARDED", "Загрузка убрана из рабочего списка"),
                    ("MAPPING_UPDATED", "Сопоставление колонок подтверждено"),
                    ("REVIEW_RECALCULATED", "Проверка строк пересчитана"),
                    ("ROW_DECISION", "Принято решение по строке"),
                    ("BULK_DECISION", "Выполнено массовое решение"),
                ],
                max_length=24,
                verbose_name="Событие",
            ),
        ),
    ]
