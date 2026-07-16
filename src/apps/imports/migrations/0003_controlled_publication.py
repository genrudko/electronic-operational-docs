# Generated for Patch 008.3.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0002_mapping_and_review"),
        ("organizations", "0003_operational_structure"),
    ]

    operations = [
        migrations.AddField(
            model_name="importbatch",
            name="published_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                verbose_name="Опубликовано в рабочий справочник",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="published_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="published_import_batches",
                to="organizations.employee",
                verbose_name="Опубликовал",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="publication_digest",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=64,
                verbose_name="SHA-256 публикации",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="publication_counts",
            field=models.JSONField(
                blank=True,
                default=dict,
                verbose_name="Итоги публикации",
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
                    ("PUBLISHED", "Опубликовано в рабочий справочник"),
                ],
                default="PROCESSING",
                max_length=16,
                verbose_name="Состояние",
            ),
        ),
        migrations.CreateModel(
            name="ImportPublication",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "public_id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                        verbose_name="Публичный идентификатор",
                    ),
                ),
                (
                    "schema_version",
                    models.CharField(
                        default="eod.import.publication.v1",
                        max_length=64,
                        verbose_name="Версия схемы снимка",
                    ),
                ),
                (
                    "target_registry",
                    models.CharField(
                        choices=[
                            ("ORGANIZATION", "Организация и персонал"),
                            ("EQUIPMENT", "Оборудование"),
                            ("DISPATCHING", "Управление и ведение"),
                            ("OTHER", "Другой справочник"),
                        ],
                        max_length=24,
                        verbose_name="Назначение",
                    ),
                ),
                (
                    "mapping_revision",
                    models.PositiveIntegerField(verbose_name="Редакция сопоставления"),
                ),
                (
                    "canonical_json",
                    models.TextField(verbose_name="Канонический снимок публикации"),
                ),
                (
                    "digest",
                    models.CharField(
                        max_length=64,
                        unique=True,
                        verbose_name="SHA-256 снимка публикации",
                    ),
                ),
                (
                    "result_summary",
                    models.JSONField(
                        default=dict,
                        verbose_name="Итоги записи",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Опубликовано",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="import_publications",
                        to="organizations.employee",
                        verbose_name="Опубликовал",
                    ),
                ),
                (
                    "batch",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication",
                        to="imports.importbatch",
                        verbose_name="Загрузка",
                    ),
                ),
            ],
            options={
                "verbose_name": "публикация импорта",
                "verbose_name_plural": "публикации импорта",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.CreateModel(
            name="ImportPublicationRow",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "target_model",
                    models.CharField(
                        max_length=128,
                        verbose_name="Целевая модель",
                    ),
                ),
                (
                    "target_object_id",
                    models.CharField(
                        max_length=128,
                        verbose_name="Идентификатор созданной записи",
                    ),
                ),
                (
                    "result",
                    models.JSONField(
                        default=dict,
                        verbose_name="Результат строки",
                    ),
                ),
                (
                    "digest",
                    models.CharField(
                        max_length=64,
                        verbose_name="SHA-256 результата строки",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Записано",
                    ),
                ),
                (
                    "publication",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="published_rows",
                        to="imports.importpublication",
                        verbose_name="Публикация",
                    ),
                ),
                (
                    "row",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="publication_result",
                        to="imports.importrow",
                        verbose_name="Строка импорта",
                    ),
                ),
            ],
            options={
                "verbose_name": "результат публикации строки",
                "verbose_name_plural": "результаты публикации строк",
                "ordering": ("row__row_number",),
            },
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
                    ("PUBLISHED", "Принятые строки опубликованы"),
                ],
                max_length=24,
                verbose_name="Событие",
            ),
        ),
    ]
