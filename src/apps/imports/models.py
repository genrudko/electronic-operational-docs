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
        DISCARDED = "DISCARDED", "Убрано из рабочего списка"

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
    mapping_revision = models.PositiveIntegerField("Редакция сопоставления", default=0)
    mapping_completed_at = models.DateTimeField(
        "Сопоставление подтверждено",
        null=True,
        blank=True,
    )
    review_recalculated_at = models.DateTimeField(
        "Проверка строк пересчитана",
        null=True,
        blank=True,
    )
    review_counts = models.JSONField(
        "Счётчики ручной проверки",
        default=dict,
        blank=True,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    discarded_at = models.DateTimeField(
        "Убрано из рабочего списка",
        null=True,
        blank=True,
    )

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
            "Физическое удаление попытки импорта запрещено. "
            "Используйте удаление из рабочего списка."
        )

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.created_by_id and self.organization_id:
            if self.created_by.organization_id != self.organization_id:
                errors["created_by"] = "Сотрудник относится к другой организации."
        if self.status == self.Status.DISCARDED and self.discarded_at is None:
            errors["discarded_at"] = "Для убранной загрузки требуется время операции."
        if self.status != self.Status.DISCARDED and self.discarded_at is not None:
            errors["discarded_at"] = (
                "Время удаления из рабочего списка допустимо только для убранной загрузки."
            )
        if not isinstance(self.review_counts, dict):
            errors["review_counts"] = "Счётчики проверки должны храниться объектом."
        if errors:
            raise ValidationError(errors)

    def mark_discarded(self) -> None:
        if self.status == self.Status.DISCARDED:
            return
        self.status = self.Status.DISCARDED
        self.discarded_at = timezone.now()
        self.save(update_fields=("status", "discarded_at", "updated_at"))


class ImportColumn(models.Model):
    class MappingOrigin(models.TextChoices):
        AUTO = "AUTO", "Предложено автоматически"
        MANUAL = "MANUAL", "Назначено пользователем"
        IGNORED = "IGNORED", "Не используется"

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
    mapped_key = models.CharField("Назначенное поле", max_length=64, blank=True)
    mapping_origin = models.CharField(
        "Источник сопоставления",
        max_length=12,
        choices=MappingOrigin.choices,
        default=MappingOrigin.AUTO,
    )
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
        errors: dict[str, str] = {}
        if not isinstance(self.issues, list):
            errors["issues"] = "Замечания должны храниться списком."
        if self.mapping_origin == self.MappingOrigin.IGNORED and self.mapped_key:
            errors["mapped_key"] = "Игнорируемая колонка не может быть назначена полю."
        if errors:
            raise ValidationError(errors)


class ImportRow(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "Новая"
        RECOGNIZED = "RECOGNIZED", "Распознана"
        REVIEW = "REVIEW", "Требует проверки"
        CONFLICT = "CONFLICT", "Конфликт"
        REJECTED = "REJECTED", "Отклонена"

    class ReviewStatus(models.TextChoices):
        NOT_MAPPED = "NOT_MAPPED", "Сопоставление не подтверждено"
        VALID = "VALID", "Готова к решению"
        REVIEW = "REVIEW", "Нужна ручная проверка"
        CONFLICT = "CONFLICT", "Обнаружен конфликт"
        INVALID = "INVALID", "Есть ошибки"

    class Decision(models.TextChoices):
        PENDING = "PENDING", "Решение не принято"
        ACCEPTED = "ACCEPTED", "Принята предварительно"
        REJECTED = "REJECTED", "Отклонена пользователем"

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
        "Состояние строки источника",
        max_length=16,
        choices=Status.choices,
    )
    issues = models.JSONField("Замечания разбора", default=list, blank=True)
    fingerprint = models.CharField("Отпечаток нормализованной строки", max_length=64)
    mapped_values = models.JSONField("Сопоставленные значения", default=dict, blank=True)
    review_status = models.CharField(
        "Состояние ручной проверки",
        max_length=16,
        choices=ReviewStatus.choices,
        default=ReviewStatus.NOT_MAPPED,
    )
    validation_issues = models.JSONField(
        "Ошибки проверки",
        default=list,
        blank=True,
    )
    registry_conflicts = models.JSONField(
        "Конфликты с реестрами",
        default=list,
        blank=True,
    )
    decision = models.CharField(
        "Предварительное решение",
        max_length=12,
        choices=Decision.choices,
        default=Decision.PENDING,
    )
    decision_values = models.JSONField(
        "Исправленные значения решения",
        default=dict,
        blank=True,
    )
    decision_note = models.TextField("Комментарий к решению", blank=True)
    decided_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="decided_import_rows",
        verbose_name="Решение принял",
    )
    decided_at = models.DateTimeField("Время решения", null=True, blank=True)
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
            models.Index(
                fields=("batch", "review_status", "decision"),
                name="imp_row_review_idx",
            ),
        ]
        verbose_name = "строка импорта"
        verbose_name_plural = "строки импорта"

    def __str__(self) -> str:
        return f"{self.batch.original_filename}: строка {self.row_number}"

    @property
    def effective_values(self) -> dict[str, str]:
        if self.decision == self.Decision.ACCEPTED and self.decision_values:
            return dict(self.decision_values)
        return dict(self.mapped_values)

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        list_fields = (
            "source_values",
            "normalized_values",
            "issues",
            "validation_issues",
            "registry_conflicts",
        )
        for field in list_fields:
            if not isinstance(getattr(self, field), list):
                errors[field] = "Значение должно храниться списком."
        for field in ("mapped_values", "decision_values"):
            if not isinstance(getattr(self, field), dict):
                errors[field] = "Значение должно храниться объектом."
        has_decision_actor = self.decided_by_id is not None and self.decided_at is not None
        if self.decision == self.Decision.PENDING:
            if self.decided_by_id or self.decided_at or self.decision_values or self.decision_note:
                errors["decision"] = "Ожидающая строка не должна содержать реквизиты решения."
        elif not has_decision_actor:
            errors["decided_by"] = "Для решения требуются сотрудник и время."
        if self.decided_by_id and self.batch_id:
            if self.decided_by.organization_id != self.batch.organization_id:
                errors["decided_by"] = "Сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


class ImmutableAuditQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение аудиторских событий запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление аудиторских событий запрещено.")


ImmutableAuditManager = models.Manager.from_queryset(ImmutableAuditQuerySet)


class ImportEvent(models.Model):
    class EventType(models.TextChoices):
        UPLOADED = "UPLOADED", "Файл загружен"
        PARSED = "PARSED", "Предварительный просмотр сформирован"
        FAILED = "FAILED", "Разбор завершился ошибкой"
        DISCARDED = "DISCARDED", "Загрузка убрана из рабочего списка"
        MAPPING_UPDATED = "MAPPING_UPDATED", "Сопоставление колонок подтверждено"
        REVIEW_RECALCULATED = "REVIEW_RECALCULATED", "Проверка строк пересчитана"
        ROW_DECISION = "ROW_DECISION", "Принято решение по строке"
        BULK_DECISION = "BULK_DECISION", "Выполнено массовое решение"

    batch = models.ForeignKey(
        ImportBatch,
        on_delete=models.CASCADE,
        related_name="events",
        verbose_name="Загрузка",
    )
    event_type = models.CharField(
        "Событие",
        max_length=24,
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

    objects = ImmutableAuditManager()

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

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Аудиторское событие импорта неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление аудиторского события запрещено.")

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
