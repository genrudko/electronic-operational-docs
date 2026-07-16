from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from apps.organizations.models import Employee, Organization


class ImportBatch(models.Model):
    class TargetRegistry(models.TextChoices):
        ORGANIZATION = "ORGANIZATION", "Организация и персонал"
        EQUIPMENT = "EQUIPMENT", "Оборудование"
        DISPATCHING = "DISPATCHING", "Управление и ведение"
        OTHER = "OTHER", "Другой справочник"

    class SourceFormat(models.TextChoices):
        CSV = "CSV", "CSV"
        XLSX = "XLSX", "XLSX"

    class Status(models.TextChoices):
        PROCESSING = "PROCESSING", "Обрабатывается"
        READY = "READY", "Предварительный просмотр готов"
        FAILED = "FAILED", "Ошибка разбора"
        DISCARDED = "DISCARDED", "Удалено пользователем"

    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="import_batches",
        verbose_name="Организация",
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_import_batches",
        verbose_name="Загрузил",
    )
    target_registry = models.CharField(
        "Назначение импорта",
        max_length=24,
        choices=TargetRegistry.choices,
    )
    original_filename = models.CharField("Исходное имя файла", max_length=255)
    source_format = models.CharField(
        "Формат",
        max_length=8,
        choices=SourceFormat.choices,
    )
    file_size = models.PositiveBigIntegerField("Размер файла, байт")
    file_sha256 = models.CharField("SHA-256 исходного файла", max_length=64)
    sheet_name = models.CharField("Лист XLSX", max_length=255, blank=True)
    source_encoding = models.CharField("Кодировка CSV", max_length=32, blank=True)
    source_delimiter = models.CharField("Разделитель CSV", max_length=8, blank=True)
    status = models.CharField(
        "Состояние",
        max_length=16,
        choices=Status.choices,
        default=Status.PROCESSING,
    )
    total_rows = models.PositiveIntegerField("Всего строк в источнике", default=0)
    data_rows = models.PositiveIntegerField("Строк данных", default=0)
    column_count = models.PositiveIntegerField("Колонок", default=0)
    status_counts = models.JSONField("Счётчики строк", default=dict, blank=True)
    warning_count = models.PositiveIntegerField("Замечаний", default=0)
    error_message = models.TextField("Ошибка разбора", blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    discarded_at = models.DateTimeField("Удалено пользователем", null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        indexes = [
            models.Index(
                fields=("organization", "status", "-created_at"),
                name="imp_batch_org_status_idx",
            ),
            models.Index(
                fields=("organization", "file_sha256"),
                name="imp_batch_org_sha_idx",
            ),
        ]
        verbose_name = "попытка импорта"
        verbose_name_plural = "попытки импорта"


    def __str__(self) -> str:
        return f"{self.original_filename} · {self.get_status_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.original_filename = self.original_filename.strip()
        self.file_sha256 = self.file_sha256.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            "Физическое удаление попытки импорта запрещено. Используйте отзыв загрузки."
        )

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.created_by_id and self.organization_id:
            if self.created_by.organization_id != self.organization_id:
                errors["created_by"] = "Сотрудник относится к другой организации."
        if self.status == self.Status.DISCARDED and self.discarded_at is None:
            errors["discarded_at"] = "Для удалённой загрузки требуется время удаления."
        if self.status != self.Status.DISCARDED and self.discarded_at is not None:
            errors["discarded_at"] = "Время удаления допустимо только для удалённой загрузки."
        if errors:
            raise ValidationError(errors)

    def mark_discarded(self) -> None:
        if self.status == self.Status.DISCARDED:
            return
        self.status = self.Status.DISCARDED
        self.discarded_at = timezone.now()
        self.save(update_fields=("status", "discarded_at", "updated_at"))


class ImportColumn(models.Model):
    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="columns",
        verbose_name="Загрузка",
    )
    position = models.PositiveIntegerField("Позиция")
    source_name = models.CharField("Исходный заголовок", max_length=1000, blank=True)
    normalized_name = models.CharField("Нормализованный заголовок", max_length=1000)
    recognized_key = models.CharField("Распознанное поле", max_length=64, blank=True)
    needs_review = models.BooleanField("Требует проверки", default=False)
    issues = models.JSONField("Замечания", default=list, blank=True)

    class Meta:
        ordering = ("position",)
        constraints = [
            models.UniqueConstraint(
                fields=("batch", "position"),
                name="uniq_import_col_position",
            )
        ]
        verbose_name = "колонка импорта"
        verbose_name_plural = "колонки импорта"

    def __str__(self) -> str:
        return self.source_name or self.normalized_name

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.issues, list):
            raise ValidationError({"issues": "Замечания должны храниться списком."})


class ImportRow(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "Новая"
        RECOGNIZED = "RECOGNIZED", "Распознана"
        REVIEW = "REVIEW", "Требует проверки"
        CONFLICT = "CONFLICT", "Конфликт"
        REJECTED = "REJECTED", "Отклонена"

    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="rows",
        verbose_name="Загрузка",
    )
    row_number = models.PositiveIntegerField("Номер строки в источнике")
    source_values = models.JSONField("Исходные значения", default=list)
    normalized_values = models.JSONField("Нормализованные значения", default=list)
    status = models.CharField(
        "Состояние строки",
        max_length=16,
        choices=Status.choices,
    )
    issues = models.JSONField("Замечания", default=list, blank=True)
    fingerprint = models.CharField("Отпечаток нормализованной строки", max_length=64)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("row_number",)
        constraints = [
            models.UniqueConstraint(
                fields=("batch", "row_number"),
                name="uniq_import_row_number",
            )
        ]
        indexes = [
            models.Index(
                fields=("batch", "status", "row_number"),
                name="imp_row_status_idx",
            ),
            models.Index(
                fields=("batch", "fingerprint"),
                name="imp_row_fingerprint_idx",
            ),
        ]
        verbose_name = "строка импорта"
        verbose_name_plural = "строки импорта"

    def __str__(self) -> str:
        return f"{self.batch.original_filename}: строка {self.row_number}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if not isinstance(self.source_values, list):
            errors["source_values"] = "Исходные значения должны храниться списком."
        if not isinstance(self.normalized_values, list):
            errors["normalized_values"] = "Нормализованные значения должны храниться списком."
        if not isinstance(self.issues, list):
            errors["issues"] = "Замечания должны храниться списком."
        if errors:
            raise ValidationError(errors)


class ImportEvent(models.Model):
    class EventType(models.TextChoices):
        UPLOADED = "UPLOADED", "Файл загружен"
        PARSED = "PARSED", "Предварительный просмотр сформирован"
        FAILED = "FAILED", "Разбор завершился ошибкой"
        DISCARDED = "DISCARDED", "Загрузка удалена пользователем"

    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Загрузка",
    )
    event_type = models.CharField(
        "Событие",
        max_length=16,
        choices=EventType.choices,
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="import_events",
        verbose_name="Сотрудник",
    )
    details = models.JSONField("Сведения", default=dict, blank=True)
    created_at = models.DateTimeField("Время", auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(
                fields=("batch", "created_at"),
                name="imp_event_time_idx",
            )
        ]
        verbose_name = "событие импорта"
        verbose_name_plural = "события импорта"

    def __str__(self) -> str:
        return f"{self.batch.original_filename}: {self.get_event_type_display()}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.batch_id and self.actor_id:
            if self.batch.organization_id != self.actor.organization_id:
                errors["actor"] = "Сотрудник относится к другой организации."
        if not isinstance(self.details, dict):
            errors["details"] = "Сведения события должны храниться объектом."
        if errors:
            raise ValidationError(errors)
