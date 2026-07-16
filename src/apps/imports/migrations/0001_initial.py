# Generated for Patch 008.1.

import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("organizations", "0003_operational_structure"),
    ]

    operations = [
        migrations.CreateModel(
            name="ImportBatch",
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
                    "target_registry",
                    models.CharField(
                        choices=[
                            ("ORGANIZATION", "Организация и персонал"),
                            ("EQUIPMENT", "Оборудование"),
                            ("DISPATCHING", "Управление и ведение"),
                            ("OTHER", "Другой справочник"),
                        ],
                        max_length=24,
                        verbose_name="Назначение импорта",
                    ),
                ),
                (
                    "original_filename",
                    models.CharField(
                        max_length=255,
                        verbose_name="Исходное имя файла",
                    ),
                ),
                (
                    "source_format",
                    models.CharField(
                        choices=[("CSV", "CSV"), ("XLSX", "XLSX")],
                        max_length=8,
                        verbose_name="Формат",
                    ),
                ),
                (
                    "file_size",
                    models.PositiveBigIntegerField(
                        verbose_name="Размер файла, байт"
                    ),
                ),
                (
                    "file_sha256",
                    models.CharField(
                        max_length=64,
                        verbose_name="SHA-256 исходного файла",
                    ),
                ),
                (
                    "sheet_name",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Лист XLSX",
                    ),
                ),
                (
                    "source_encoding",
                    models.CharField(
                        blank=True,
                        max_length=32,
                        verbose_name="Кодировка CSV",
                    ),
                ),
                (
                    "source_delimiter",
                    models.CharField(
                        blank=True,
                        max_length=8,
                        verbose_name="Разделитель CSV",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PROCESSING", "Обрабатывается"),
                            ("READY", "Предварительный просмотр готов"),
                            ("FAILED", "Ошибка разбора"),
                            ("DISCARDED", "Удалено пользователем"),
                        ],
                        default="PROCESSING",
                        max_length=16,
                        verbose_name="Состояние",
                    ),
                ),
                (
                    "total_rows",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Всего строк в источнике",
                    ),
                ),
                (
                    "data_rows",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Строк данных",
                    ),
                ),
                (
                    "column_count",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Колонок",
                    ),
                ),
                (
                    "status_counts",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        verbose_name="Счётчики строк",
                    ),
                ),
                (
                    "warning_count",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Замечаний",
                    ),
                ),
                (
                    "error_message",
                    models.TextField(
                        blank=True,
                        verbose_name="Ошибка разбора",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Создано",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        verbose_name="Изменено",
                    ),
                ),
                (
                    "discarded_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Удалено пользователем",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_import_batches",
                        to="organizations.employee",
                        verbose_name="Загрузил",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="import_batches",
                        to="organizations.organization",
                        verbose_name="Организация",
                    ),
                ),
            ],
            options={
                "verbose_name": "попытка импорта",
                "verbose_name_plural": "попытки импорта",
                "ordering": ("-created_at", "-id"),
                "indexes": [
                    models.Index(
                        fields=["organization", "status", "-created_at"],
                        name="imp_batch_org_status_idx",
                    ),
                    models.Index(
                        fields=["organization", "file_sha256"],
                        name="imp_batch_org_sha_idx",
                    ),
                ],
            },
        ),
        migrations.CreateModel(
            name="ImportColumn",
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
                ("position", models.PositiveIntegerField(verbose_name="Позиция")),
                (
                    "source_name",
                    models.CharField(
                        blank=True,
                        max_length=1000,
                        verbose_name="Исходный заголовок",
                    ),
                ),
                (
                    "normalized_name",
                    models.CharField(
                        max_length=1000,
                        verbose_name="Нормализованный заголовок",
                    ),
                ),
                (
                    "recognized_key",
                    models.CharField(
                        blank=True,
                        max_length=64,
                        verbose_name="Распознанное поле",
                    ),
                ),
                (
                    "needs_review",
                    models.BooleanField(
                        default=False,
                        verbose_name="Требует проверки",
                    ),
                ),
                (
                    "issues",
                    models.JSONField(
                        blank=True,
                        default=list,
                        verbose_name="Замечания",
                    ),
                ),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="columns",
                        to="imports.importbatch",
                        verbose_name="Загрузка",
                    ),
                ),
            ],
            options={
                "verbose_name": "колонка импорта",
                "verbose_name_plural": "колонки импорта",
                "ordering": ("position",),
                "constraints": [
                    models.UniqueConstraint(
                        fields=("batch", "position"),
                        name="uniq_import_col_position",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ImportEvent",
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
                    "event_type",
                    models.CharField(
                        choices=[
                            ("UPLOADED", "Файл загружен"),
                            ("PARSED", "Предварительный просмотр сформирован"),
                            ("FAILED", "Разбор завершился ошибкой"),
                            ("DISCARDED", "Загрузка удалена пользователем"),
                        ],
                        max_length=16,
                        verbose_name="Событие",
                    ),
                ),
                (
                    "details",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        verbose_name="Сведения",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Время",
                    ),
                ),
                (
                    "actor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="import_events",
                        to="organizations.employee",
                        verbose_name="Сотрудник",
                    ),
                ),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="events",
                        to="imports.importbatch",
                        verbose_name="Загрузка",
                    ),
                ),
            ],
            options={
                "verbose_name": "событие импорта",
                "verbose_name_plural": "события импорта",
                "ordering": ("created_at", "id"),
                "indexes": [
                    models.Index(
                        fields=["batch", "created_at"],
                        name="imp_event_time_idx",
                    )
                ],
            },
        ),
        migrations.CreateModel(
            name="ImportRow",
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
                    "row_number",
                    models.PositiveIntegerField(
                        verbose_name="Номер строки в источнике"
                    ),
                ),
                (
                    "source_values",
                    models.JSONField(
                        default=list,
                        verbose_name="Исходные значения",
                    ),
                ),
                (
                    "normalized_values",
                    models.JSONField(
                        default=list,
                        verbose_name="Нормализованные значения",
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("NEW", "Новая"),
                            ("RECOGNIZED", "Распознана"),
                            ("REVIEW", "Требует проверки"),
                            ("CONFLICT", "Конфликт"),
                            ("REJECTED", "Отклонена"),
                        ],
                        max_length=16,
                        verbose_name="Состояние строки",
                    ),
                ),
                (
                    "issues",
                    models.JSONField(
                        blank=True,
                        default=list,
                        verbose_name="Замечания",
                    ),
                ),
                (
                    "fingerprint",
                    models.CharField(
                        max_length=64,
                        verbose_name="Отпечаток нормализованной строки",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        verbose_name="Создано",
                    ),
                ),
                (
                    "batch",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rows",
                        to="imports.importbatch",
                        verbose_name="Загрузка",
                    ),
                ),
            ],
            options={
                "verbose_name": "строка импорта",
                "verbose_name_plural": "строки импорта",
                "ordering": ("row_number",),
                "indexes": [
                    models.Index(
                        fields=["batch", "status", "row_number"],
                        name="imp_row_status_idx",
                    ),
                    models.Index(
                        fields=["batch", "fingerprint"],
                        name="imp_row_fingerprint_idx",
                    ),
                ],
                "constraints": [
                    models.UniqueConstraint(
                        fields=("batch", "row_number"),
                        name="uniq_import_row_number",
                    )
                ],
            },
        ),
    ]
