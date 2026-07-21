from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.organizations.models import Employee, Organization

DATA_PROFILE_SPECS: tuple[dict[str, object], ...] = (
    {
        "code": "presentation-safe",
        "name": "Безопасная презентационная база",
        "kind": "PRESENTATION_SAFE",
        "sensitivity_level": "SAFE_DEMO",
        "export_policy": "ALLOWED",
        "allows_real_personal_data": False,
        "is_default": True,
        "description": (
            "Предметная демонстрационная база: реальные диспетчерские наименования "
            "допустимы, персональные данные и реальные оперативные события запрещены."
        ),
    },
    {
        "code": "local-validation",
        "name": "Локальная проверочная база",
        "kind": "LOCAL_VALIDATION",
        "sensitivity_level": "PERSONAL_INTERNAL",
        "export_policy": "PROHIBITED",
        "allows_real_personal_data": True,
        "is_default": False,
        "description": (
            "Локальная база углублённой проверки. Может содержать реальные ФИО и "
            "внутреннюю номенклатуру; обычный экспорт запрещён."
        ),
    },
    {
        "code": "automated-tests",
        "name": "Автоматизированные тесты",
        "kind": "AUTOMATED_TEST",
        "sensitivity_level": "SYNTHETIC",
        "export_policy": "PROHIBITED",
        "allows_real_personal_data": False,
        "is_default": False,
        "description": "Полностью синтетические данные для изолированных автоматизированных проверок.",
    },
)


class DataProfile(models.Model):
    class Kind(models.TextChoices):
        PRESENTATION_SAFE = "PRESENTATION_SAFE", "Безопасная презентационная база"
        LOCAL_VALIDATION = "LOCAL_VALIDATION", "Локальная проверочная база"
        AUTOMATED_TEST = "AUTOMATED_TEST", "Автоматизированные тесты"

    class SensitivityLevel(models.TextChoices):
        SYNTHETIC = "SYNTHETIC", "Синтетические данные"
        SAFE_DEMO = "SAFE_DEMO", "Безопасные демонстрационные данные"
        INTERNAL_OPERATIONAL = "INTERNAL_OPERATIONAL", "Внутренняя оперативная номенклатура"
        PERSONAL_INTERNAL = "PERSONAL_INTERNAL", "Внутренние данные с персональными сведениями"

    class ExportPolicy(models.TextChoices):
        ALLOWED = "ALLOWED", "Разрешён безопасный экспорт"
        RESTRICTED = "RESTRICTED", "Экспорт только после проверки"
        PROHIBITED = "PROHIBITED", "Обычный экспорт запрещён"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="data_profiles",
        verbose_name="Организация",
    )
    code = models.SlugField("Внутренний код", max_length=64)
    name = models.CharField("Наименование", max_length=255)
    kind = models.CharField("Тип профиля", max_length=24, choices=Kind.choices)
    sensitivity_level = models.CharField(
        "Уровень чувствительности",
        max_length=24,
        choices=SensitivityLevel.choices,
    )
    export_policy = models.CharField(
        "Политика экспорта",
        max_length=16,
        choices=ExportPolicy.choices,
    )
    allows_real_personal_data = models.BooleanField(
        "Допускает реальные персональные данные",
        default=False,
    )
    is_default = models.BooleanField("Профиль по умолчанию", default=False)
    is_active = models.BooleanField("Действующий", default=True)
    description = models.TextField("Назначение и ограничения", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_data_profile_code_per_org",
            ),
            models.UniqueConstraint(
                fields=("organization",),
                condition=Q(is_default=True),
                name="uniq_default_data_profile_per_org",
            ),
        ]
        verbose_name = "профиль данных"
        verbose_name_plural = "профили данных"

    def __str__(self) -> str:
        return f"{self.organization}: {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        self.name = self.name.strip()
        self.description = self.description.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.is_default and not self.is_active:
            errors["is_active"] = "Профиль по умолчанию должен быть действующим."
        if self.kind == self.Kind.PRESENTATION_SAFE:
            if self.allows_real_personal_data:
                errors["allows_real_personal_data"] = (
                    "Безопасный презентационный профиль не допускает реальные персональные данные."
                )
            if self.export_policy != self.ExportPolicy.ALLOWED:
                errors["export_policy"] = (
                    "Безопасный презентационный профиль должен допускать контролируемый экспорт."
                )
        if self.kind == self.Kind.LOCAL_VALIDATION:
            if self.export_policy != self.ExportPolicy.PROHIBITED:
                errors["export_policy"] = (
                    "Для локального проверочного профиля обычный экспорт должен быть запрещён."
                )
        if self.kind == self.Kind.AUTOMATED_TEST:
            if self.allows_real_personal_data:
                errors["allows_real_personal_data"] = (
                    "Профиль автоматизированных тестов должен быть полностью синтетическим."
                )
            if self.export_policy != self.ExportPolicy.PROHIBITED:
                errors["export_policy"] = (
                    "Профиль автоматизированных тестов не предназначен для экспорта."
                )
        if errors:
            raise ValidationError(errors)

    @classmethod
    def ensure_for_organization(cls, organization: Organization) -> tuple[DataProfile, ...]:
        profiles: list[DataProfile] = []
        for spec in DATA_PROFILE_SPECS:
            defaults = {key: value for key, value in spec.items() if key != "code"}
            profile, _created = cls.objects.get_or_create(
                organization=organization,
                code=str(spec["code"]),
                defaults=defaults,
            )
            profiles.append(profile)
        return tuple(profiles)

    @classmethod
    def default_for_organization(cls, organization: Organization) -> DataProfile:
        cls.ensure_for_organization(organization)
        return cls.objects.get(organization=organization, is_default=True, is_active=True)


class ImportMappingTemplate(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="import_mapping_templates",
        verbose_name="Организация",
    )
    target_registry = models.CharField(
        "Назначение импорта",
        max_length=24,
        choices=(
            ("ORGANIZATION", "Организация и персонал"),
            ("EQUIPMENT", "Оборудование"),
            ("DISPATCHING", "Управление и ведение"),
            ("OTHER", "Другой справочник"),
        ),
    )
    name = models.CharField("Наименование схемы", max_length=255)
    header_signature = models.CharField("SHA-256 структуры заголовков", max_length=64)
    mapping = models.JSONField("Сопоставление колонок", default=dict)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_import_mapping_templates",
        verbose_name="Создал",
    )
    updated_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="updated_import_mapping_templates",
        verbose_name="Изменил",
    )
    usage_count = models.PositiveIntegerField("Количество применений", default=0)
    last_used_at = models.DateTimeField("Последнее применение", null=True, blank=True)
    is_active = models.BooleanField("Действующая схема", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)

    class Meta:
        ordering = ("organization__name", "target_registry", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "target_registry", "header_signature"),
                name="uniq_mapping_template_headers",
            )
        ]
        verbose_name = "схема сопоставления импорта"
        verbose_name_plural = "схемы сопоставления импорта"

    def __str__(self) -> str:
        return f"{self.name} · {self.target_registry}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.name = self.name.strip()
        self.header_signature = self.header_signature.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if len(self.header_signature) != 64:
            errors["header_signature"] = "Для структуры заголовков требуется SHA-256."
        if not isinstance(self.mapping, dict):
            errors["mapping"] = "Сопоставление должно храниться объектом."
        else:
            for position, key in self.mapping.items():
                if not str(position).isdigit() or int(position) < 1:
                    errors["mapping"] = "Позиции колонок должны быть положительными целыми числами."
                    break
                if not isinstance(key, str):
                    errors["mapping"] = "Ключи полей сопоставления должны быть строками."
                    break
        if self.created_by_id and self.organization_id:
            if self.created_by.organization_id != self.organization_id:
                errors["created_by"] = "Создатель относится к другой организации."
        if self.updated_by_id and self.organization_id:
            if self.updated_by.organization_id != self.organization_id:
                errors["updated_by"] = "Изменивший сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


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
        PUBLISHED = "PUBLISHED", "Опубликовано в рабочий справочник"

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
    data_profile = models.ForeignKey(
        DataProfile,
        on_delete=models.PROTECT,
        related_name="import_batches",
        verbose_name="Профиль данных",
    )
    target_registry = models.CharField(
        "Назначение импорта",
        max_length=24,
        choices=TargetRegistry.choices,
    )
    applied_mapping_template = models.ForeignKey(
        ImportMappingTemplate,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="applied_batches",
        verbose_name="Применённая схема сопоставления",
    )
    original_filename = models.CharField("Исходное имя файла", max_length=255)
    source_format = models.CharField(
        "Формат",
        max_length=8,
        choices=SourceFormat.choices,
    )
    file_size = models.PositiveBigIntegerField("Размер файла, байт")
    file_sha256 = models.CharField("SHA-256 исходного файла", max_length=64)
    header_signature = models.CharField(
        "SHA-256 структуры заголовков",
        max_length=64,
        blank=True,
        editable=False,
    )
    source_reference = models.CharField(
        "Источник или основание",
        max_length=1000,
        blank=True,
    )
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
    published_at = models.DateTimeField(
        "Опубликовано в рабочий справочник",
        null=True,
        blank=True,
    )
    published_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_import_batches",
        verbose_name="Опубликовал",
    )
    publication_digest = models.CharField(
        "SHA-256 публикации",
        max_length=64,
        blank=True,
        editable=False,
    )
    publication_counts = models.JSONField(
        "Итоги публикации",
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
        self.header_signature = self.header_signature.strip().lower()
        self.source_reference = self.source_reference.strip()
        if self.organization_id and not self.data_profile_id:
            self.data_profile = DataProfile.default_for_organization(self.organization)
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
        if self.data_profile_id and self.organization_id:
            if self.data_profile.organization_id != self.organization_id:
                errors["data_profile"] = "Профиль данных относится к другой организации."
            if not self.data_profile.is_active:
                errors["data_profile"] = "Нельзя использовать отключённый профиль данных."
        if self.applied_mapping_template_id and self.organization_id:
            template = self.applied_mapping_template
            if template.organization_id != self.organization_id:
                errors["applied_mapping_template"] = (
                    "Схема сопоставления относится к другой организации."
                )
            if template.target_registry != self.target_registry:
                errors["applied_mapping_template"] = (
                    "Схема сопоставления предназначена для другого реестра."
                )
            if self.header_signature and template.header_signature != self.header_signature:
                errors["applied_mapping_template"] = (
                    "Схема сопоставления не соответствует структуре заголовков."
                )
        if self.header_signature and len(self.header_signature) != 64:
            errors["header_signature"] = "Для структуры заголовков требуется SHA-256."
        if self.status == self.Status.DISCARDED and self.discarded_at is None:
            errors["discarded_at"] = "Для убранной загрузки требуется время операции."
        if self.status != self.Status.DISCARDED and self.discarded_at is not None:
            errors["discarded_at"] = (
                "Время удаления из рабочего списка допустимо только для убранной загрузки."
            )
        if not isinstance(self.review_counts, dict):
            errors["review_counts"] = "Счётчики проверки должны храниться объектом."
        if not isinstance(self.publication_counts, dict):
            errors["publication_counts"] = "Итоги публикации должны храниться объектом."
        publication_fields_present = bool(
            self.published_at
            or self.published_by_id
            or self.publication_digest
            or self.publication_counts
        )
        if self.status == self.Status.PUBLISHED:
            if (
                self.published_at is None
                or self.published_by_id is None
                or len(self.publication_digest) != 64
                or not self.publication_counts
            ):
                errors["status"] = (
                    "Опубликованная загрузка требует автора, времени, SHA-256 и итогов."
                )
        elif publication_fields_present:
            errors["status"] = (
                "Реквизиты публикации допустимы только для опубликованной загрузки."
            )
        if self.published_by_id and self.organization_id:
            if self.published_by.organization_id != self.organization_id:
                errors["published_by"] = "Публикующий сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)

    def mark_discarded(self) -> None:
        if self.status == self.Status.PUBLISHED:
            raise ValidationError("Опубликованную загрузку нельзя убрать из рабочего списка.")
        if self.status == self.Status.DISCARDED:
            return
        self.status = self.Status.DISCARDED
        self.discarded_at = timezone.now()
        self.save(update_fields=("status", "discarded_at", "updated_at"))


class ImportColumn(models.Model):
    class MappingOrigin(models.TextChoices):
        AUTO = "AUTO", "Предложено автоматически"
        TEMPLATE = "TEMPLATE", "Из сохранённой схемы"
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
        MAPPING_TEMPLATE_APPLIED = (
            "MAPPING_TEMPLATE_APPLIED",
            "Применена сохранённая схема сопоставления",
        )
        MAPPING_TEMPLATE_SAVED = (
            "MAPPING_TEMPLATE_SAVED",
            "Схема сопоставления сохранена",
        )
        REVIEW_RECALCULATED = "REVIEW_RECALCULATED", "Проверка строк пересчитана"
        ROW_DECISION = "ROW_DECISION", "Принято решение по строке"
        BULK_DECISION = "BULK_DECISION", "Выполнено массовое решение"
        PUBLISHED = "PUBLISHED", "Принятые строки опубликованы"

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


class ImportPublication(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    batch = models.OneToOneField(
        ImportBatch,
        on_delete=models.PROTECT,
        related_name="publication",
        verbose_name="Загрузка",
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="import_publications",
        verbose_name="Опубликовал",
    )
    schema_version = models.CharField(
        "Версия схемы снимка",
        max_length=64,
        default="eod.import.publication.v2",
    )
    target_registry = models.CharField(
        "Назначение",
        max_length=24,
        choices=ImportBatch.TargetRegistry.choices,
    )
    mapping_revision = models.PositiveIntegerField("Редакция сопоставления")
    canonical_json = models.TextField("Канонический снимок публикации")
    digest = models.CharField("SHA-256 снимка публикации", max_length=64, unique=True)
    result_summary = models.JSONField("Итоги записи", default=dict)
    created_at = models.DateTimeField("Опубликовано", auto_now_add=True)

    objects = ImmutableAuditManager()

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "публикация импорта"
        verbose_name_plural = "публикации импорта"

    def __str__(self) -> str:
        return f"{self.batch.original_filename} · {self.digest[:12]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Снимок публикации импорта неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление публикации импорта запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.batch_id and self.actor_id:
            if self.batch.organization_id != self.actor.organization_id:
                errors["actor"] = "Сотрудник относится к другой организации."
            if self.target_registry != self.batch.target_registry:
                errors["target_registry"] = "Назначение снимка не совпадает с загрузкой."
        if len(self.digest) != 64:
            errors["digest"] = "Для публикации требуется SHA-256."
        if not isinstance(self.result_summary, dict):
            errors["result_summary"] = "Итоги должны храниться объектом."
        if errors:
            raise ValidationError(errors)


class ImportPublicationRow(models.Model):
    publication = models.ForeignKey(
        ImportPublication,
        on_delete=models.PROTECT,
        related_name="published_rows",
        verbose_name="Публикация",
    )
    row = models.OneToOneField(
        ImportRow,
        on_delete=models.PROTECT,
        related_name="publication_result",
        verbose_name="Строка импорта",
    )
    target_model = models.CharField("Целевая модель", max_length=128)
    target_object_id = models.CharField("Идентификатор созданной записи", max_length=128)
    result = models.JSONField("Результат строки", default=dict)
    digest = models.CharField("SHA-256 результата строки", max_length=64)
    created_at = models.DateTimeField("Записано", auto_now_add=True)

    objects = ImmutableAuditManager()

    class Meta:
        ordering = ("row__row_number",)
        verbose_name = "результат публикации строки"
        verbose_name_plural = "результаты публикации строк"

    def __str__(self) -> str:
        return f"Строка {self.row.row_number} → {self.target_model}:{self.target_object_id}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Результат публикации строки неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление результата публикации запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.publication_id and self.row_id:
            if self.row.batch_id != self.publication.batch_id:
                errors["row"] = "Строка относится к другой загрузке."
            if self.row.decision != ImportRow.Decision.ACCEPTED:
                errors["row"] = "Публиковать можно только предварительно принятую строку."
        if not isinstance(self.result, dict):
            errors["result"] = "Результат должен храниться объектом."
        if len(self.digest) != 64:
            errors["digest"] = "Для результата строки требуется SHA-256."
        if errors:
            raise ValidationError(errors)
