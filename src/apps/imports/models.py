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


class PowerSystemSourceRevision(models.Model):
    class Status(models.TextChoices):
        STAGED = "STAGED", "Подготовлена к проверке"
        PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED", "Опубликована частично"
        PUBLISHED = "PUBLISHED", "Опубликована"
        DISCARDED = "DISCARDED", "Убрана из рабочего списка"

    class SourceApprovalStatus(models.TextChoices):
        DRAFT = "DRAFT", "Черновик или неподтверждённая редакция"
        APPROVED = "APPROVED", "Утверждённая редакция"
        UNKNOWN = "UNKNOWN", "Статус редакции не установлен"

    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="power_system_source_revisions",
        verbose_name="Организация",
    )
    data_profile = models.ForeignKey(
        DataProfile,
        on_delete=models.PROTECT,
        related_name="power_system_source_revisions",
        verbose_name="Профиль данных",
    )
    uploaded_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="uploaded_power_system_revisions",
        verbose_name="Загрузил",
    )
    source_reference = models.CharField("Источник или основание", max_length=1000)
    source_approval_status = models.CharField(
        "Статус исходной редакции",
        max_length=16,
        choices=SourceApprovalStatus.choices,
        default=SourceApprovalStatus.UNKNOWN,
    )
    effective_from = models.DateField("Действует с", null=True, blank=True)
    original_filename = models.CharField("Имя ZIP-пакета", max_length=255)
    file_size = models.PositiveBigIntegerField("Размер ZIP-пакета, байт")
    file_sha256 = models.CharField("SHA-256 ZIP-пакета", max_length=64)
    source_document_name = models.CharField(
        "Имя исходного документа",
        max_length=500,
        blank=True,
    )
    source_document_sha256 = models.CharField(
        "SHA-256 исходного документа",
        max_length=64,
        blank=True,
    )
    analysis_filename = models.CharField("Файл аналитического отчёта", max_length=255)
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="superseded_by",
        verbose_name="Предыдущая редакция",
    )
    manifest = models.JSONField("Манифест пакета", default=dict)
    type_dictionary = models.JSONField("Словарь типов пакета", default=list)
    diff_counts = models.JSONField(
        "Итоги сравнения с предыдущей редакцией",
        default=dict,
        blank=True,
    )
    total_occurrences = models.PositiveIntegerField("Всего source occurrences", default=0)
    hierarchy_nodes = models.PositiveIntegerField("Иерархических узлов", default=0)
    authority_rows = models.PositiveIntegerField("Строк полномочий", default=0)
    alias_rows = models.PositiveIntegerField("Строк алиасов", default=0)
    issue_rows = models.PositiveIntegerField("Проблем источника", default=0)
    ready_count = models.PositiveIntegerField("Готово к публикации", default=0)
    review_count = models.PositiveIntegerField("Требует проверки", default=0)
    blocked_count = models.PositiveIntegerField("Заблокировано", default=0)
    excluded_count = models.PositiveIntegerField("Исключено", default=0)
    published_count = models.PositiveIntegerField("Опубликовано", default=0)
    status = models.CharField(
        "Состояние",
        max_length=24,
        choices=Status.choices,
        default=Status.STAGED,
        db_index=True,
    )
    publication_digest = models.CharField(
        "SHA-256 публикации",
        max_length=64,
        blank=True,
        editable=False,
    )
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True)
    published_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_power_system_revisions",
        verbose_name="Опубликовал",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    discarded_at = models.DateTimeField("Убрано из рабочего списка", null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "file_sha256"),
                name="uniq_ps_package_sha_org",
            )
        ]
        indexes = [
            models.Index(
                fields=("organization", "status", "-created_at"),
                name="ps_source_org_status_idx",
            ),
            models.Index(
                fields=("organization", "source_reference", "-created_at"),
                name="ps_source_reference_idx",
            ),
        ]
        verbose_name = "редакция источника объектов энергосистемы"
        verbose_name_plural = "редакции источников объектов энергосистемы"

    def __str__(self) -> str:
        return f"{self.original_filename} · {self.get_status_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.original_filename = self.original_filename.strip()
        self.file_sha256 = self.file_sha256.strip().lower()
        self.source_document_sha256 = self.source_document_sha256.strip().lower()
        self.source_reference = self.source_reference.strip()
        self.source_document_name = self.source_document_name.strip()
        self.analysis_filename = self.analysis_filename.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            "Физическое удаление редакции источника запрещено. "
            "Используйте удаление из рабочего списка."
        )

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.organization_id and self.data_profile_id:
            if self.data_profile.organization_id != self.organization_id:
                errors["data_profile"] = "Профиль данных относится к другой организации."
        if self.organization_id and self.uploaded_by_id:
            if self.uploaded_by.organization_id != self.organization_id:
                errors["uploaded_by"] = "Загрузивший сотрудник относится к другой организации."
        if self.organization_id and self.published_by_id:
            if self.published_by.organization_id != self.organization_id:
                errors["published_by"] = "Публикующий сотрудник относится к другой организации."
        if self.supersedes_id and self.organization_id:
            if self.supersedes.organization_id != self.organization_id:
                errors["supersedes"] = "Предыдущая редакция относится к другой организации."
        if len(self.file_sha256) != 64:
            errors["file_sha256"] = "Для ZIP-пакета требуется SHA-256."
        if self.source_document_sha256 and len(self.source_document_sha256) != 64:
            errors["source_document_sha256"] = "SHA-256 исходного документа должен содержать 64 знака."
        for field in ("manifest", "diff_counts"):
            if not isinstance(getattr(self, field), dict):
                errors[field] = "Значение должно храниться JSON-объектом."
        if not isinstance(self.type_dictionary, list):
            errors["type_dictionary"] = "Словарь типов должен храниться списком."
        if self.status in {self.Status.PUBLISHED, self.Status.PARTIALLY_PUBLISHED}:
            if not self.published_at or not self.published_by_id or len(self.publication_digest) != 64:
                errors["status"] = "Публикация требует автора, времени и SHA-256."
        elif self.published_at or self.published_by_id or self.publication_digest:
            errors["status"] = "Реквизиты публикации допустимы только после публикации."
        if self.status == self.Status.DISCARDED and self.discarded_at is None:
            errors["discarded_at"] = "Для убранной редакции требуется время операции."
        if errors:
            raise ValidationError(errors)


class PowerSystemAssetOccurrence(models.Model):
    class RecordRole(models.TextChoices):
        HIERARCHY_NODE = "HIERARCHY_NODE", "Узел иерархии"
        DISPATCHING_OBJECT_OCCURRENCE = (
            "DISPATCHING_OBJECT_OCCURRENCE",
            "Строка объекта диспетчеризации",
        )

    class DiffState(models.TextChoices):
        ADDED = "ADDED", "Добавлена"
        UNCHANGED = "UNCHANGED", "Без изменений"
        CHANGED = "CHANGED", "Изменена"

    class ReviewStatus(models.TextChoices):
        READY = "READY", "Готова"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Требует проверки"
        BLOCKED = "BLOCKED", "Заблокирована"
        EXCLUDED = "EXCLUDED", "Исключена"
        PUBLISHED = "PUBLISHED", "Опубликована"

    class ReviewDecision(models.TextChoices):
        NONE = "NONE", "Решение не принято"
        ACCEPT_AS_NEW = "ACCEPT_AS_NEW", "Принять как отдельный объект"
        MERGE_WITH = "MERGE_WITH", "Объединить с другой строкой"
        EXCLUDE = "EXCLUDE", "Исключить из публикации"

    source_revision = models.ForeignKey(
        PowerSystemSourceRevision,
        on_delete=models.CASCADE,
        related_name="asset_occurrences",
        verbose_name="Редакция источника",
    )
    occurrence_id = models.CharField("Идентификатор строки источника", max_length=128)
    source_sheet = models.CharField("Лист источника", max_length=255)
    source_row = models.PositiveIntegerField("Строка источника")
    source_item_number = models.CharField("Номер пункта источника", max_length=64, blank=True)
    record_role = models.CharField("Роль записи", max_length=40, choices=RecordRole.choices)
    domain = models.CharField("Предметный контур", max_length=64)
    asset_type_code = models.SlugField("Предложенный тип", max_length=96)
    asset_type_name = models.CharField("Предложенный тип по-русски", max_length=255)
    source_category_raw = models.CharField("Исходная категория", max_length=1000, blank=True)
    dispatcher_name_raw = models.CharField("Исходное диспетчерское наименование", max_length=1000)
    display_name_normalized = models.CharField("Нормализованное отображение", max_length=1000)
    comparison_key = models.CharField("Ключ сравнения", max_length=1000)
    energy_facility_raw = models.CharField("Энергообъект источника", max_length=500)
    voltage_context_raw = models.CharField("Контекст напряжения", max_length=255, blank=True)
    nominal_voltage_kv = models.DecimalField(
        "Номинальное напряжение, кВ",
        max_digits=9,
        decimal_places=3,
        null=True,
        blank=True,
    )
    voltage_basis = models.CharField("Основание напряжения", max_length=64, blank=True)
    parent_raw = models.CharField("Исходный родитель", max_length=1000, blank=True)
    hierarchy_path_raw = models.TextField("Исходный путь иерархии", blank=True)
    external_key = models.CharField("Стабильный внешний ключ", max_length=128)
    parent_external_key = models.CharField("Внешний ключ родителя", max_length=128, blank=True)
    logical_key = models.CharField("Ключ логического объекта", max_length=128)
    management_raw = models.TextField("Исходное управление", blank=True)
    conduct_raw = models.TextField("Исходное ведение", blank=True)
    note_raw = models.TextField("Исходное примечание", blank=True)
    source_flags = models.JSONField("Исходные признаки", default=dict)
    classification_confidence = models.CharField("Уверенность классификации", max_length=16)
    hierarchy_confidence = models.CharField("Уверенность иерархии", max_length=16)
    import_disposition = models.CharField("Предложенное действие", max_length=64)
    duplicate_group = models.CharField("Группа дублей", max_length=128, blank=True)
    related_primary_asset_raw = models.CharField(
        "Связанное первичное оборудование",
        max_length=1000,
        blank=True,
    )
    relation_basis = models.CharField("Основание связи", max_length=255, blank=True)
    source_fact_notes = models.TextField("Пояснение аналитического источника", blank=True)
    row_fingerprint = models.CharField("SHA-256 содержательной строки", max_length=64)
    diff_state = models.CharField(
        "Изменение относительно предыдущей редакции",
        max_length=16,
        choices=DiffState.choices,
        default=DiffState.ADDED,
    )
    initial_review_status = models.CharField(
        "Исходное состояние проверки",
        max_length=24,
        choices=ReviewStatus.choices,
    )
    review_status = models.CharField(
        "Состояние проверки",
        max_length=24,
        choices=ReviewStatus.choices,
        db_index=True,
    )
    review_decision = models.CharField(
        "Решение",
        max_length=24,
        choices=ReviewDecision.choices,
        default=ReviewDecision.NONE,
    )
    merge_target = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="merged_source_occurrences",
        verbose_name="Объединить со строкой",
    )
    review_note = models.TextField("Комментарий проверки", blank=True)
    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="reviewed_power_system_occurrences",
        verbose_name="Проверил",
    )
    reviewed_at = models.DateTimeField("Проверено", null=True, blank=True)
    published_asset = models.ForeignKey(
        "equipment.EquipmentAsset",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="source_occurrences",
        verbose_name="Опубликованный объект",
    )
    publication_result = models.JSONField("Результат публикации", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("source_sheet", "source_row", "occurrence_id")
        constraints = [
            models.UniqueConstraint(
                fields=("source_revision", "occurrence_id"),
                name="uniq_ps_occurrence_id",
            ),
            models.UniqueConstraint(
                fields=("source_revision", "external_key"),
                name="uniq_ps_external_key",
            ),
        ]
        indexes = [
            models.Index(
                fields=("source_revision", "review_status", "source_sheet", "source_row"),
                name="ps_occurrence_review_idx",
            ),
            models.Index(
                fields=("source_revision", "logical_key"),
                name="ps_occurrence_logical_idx",
            ),
            models.Index(
                fields=("source_revision", "comparison_key"),
                name="ps_occurrence_compare_idx",
            ),
        ]
        verbose_name = "исходная строка объекта энергосистемы"
        verbose_name_plural = "исходные строки объектов энергосистемы"

    def __str__(self) -> str:
        return f"{self.occurrence_id} · {self.dispatcher_name_raw}"

    @property
    def effective_logical_key(self) -> str:
        if self.review_decision == self.ReviewDecision.MERGE_WITH and self.merge_target_id:
            return self.merge_target.effective_logical_key
        if self.review_decision == self.ReviewDecision.ACCEPT_AS_NEW:
            has_merged_sources = self.merged_source_occurrences.filter(
                review_decision=self.ReviewDecision.MERGE_WITH,
            ).exists()
            if not has_merged_sources:
                return f"{self.logical_key}:{self.occurrence_id}"
        return self.logical_key

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if len(self.row_fingerprint) != 64:
            errors["row_fingerprint"] = "Для строки требуется SHA-256."
        if self.review_decision == self.ReviewDecision.NONE:
            if self.merge_target_id or self.reviewed_by_id or self.reviewed_at or self.review_note:
                errors["review_decision"] = "Ожидающая строка не должна содержать реквизиты решения."
        else:
            if not self.reviewed_by_id or not self.reviewed_at:
                errors["reviewed_by"] = "Для решения нужны сотрудник и время."
        if self.review_decision == self.ReviewDecision.MERGE_WITH:
            if not self.merge_target_id:
                errors["merge_target"] = "Укажите строку, с которой нужно объединить объект."
            elif self.merge_target_id == self.pk:
                errors["merge_target"] = "Строку нельзя объединить с самой собой."
            elif self.merge_target.source_revision_id != self.source_revision_id:
                errors["merge_target"] = "Целевая строка относится к другой редакции."
        elif self.merge_target_id:
            errors["merge_target"] = "Целевая строка допустима только для решения «объединить»."
        if self.reviewed_by_id and self.source_revision_id:
            if self.reviewed_by.organization_id != self.source_revision.organization_id:
                errors["reviewed_by"] = "Проверяющий относится к другой организации."
        if self.review_status == self.ReviewStatus.PUBLISHED and not self.publication_result:
            errors["publication_result"] = "Опубликованная строка требует результата."
        if self.published_asset_id and self.source_revision_id:
            if self.published_asset.organization_id != self.source_revision.organization_id:
                errors["published_asset"] = "Оборудование относится к другой организации."
        if not isinstance(self.source_flags, dict):
            errors["source_flags"] = "Исходные признаки должны храниться JSON-объектом."
        if not isinstance(self.publication_result, dict):
            errors["publication_result"] = "Результат должен храниться JSON-объектом."
        if errors:
            raise ValidationError(errors)


class PowerSystemAuthorityOccurrence(models.Model):
    class AuthorityKind(models.TextChoices):
        OPERATIONAL_MANAGEMENT = "OPERATIONAL_MANAGEMENT", "Оперативное управление"
        OPERATIONAL_CONDUCT = "OPERATIONAL_CONDUCT", "Оперативное ведение"

    class AssignmentStatus(models.TextChoices):
        ASSIGNED = "ASSIGNED", "Назначено"
        EXPLICIT_NONE = "EXPLICIT_NONE", "Явно отсутствует"
        MISSING = "MISSING", "Не заполнено"

    class ConductMode(models.TextChoices):
        OPERATIONAL = "OPERATIONAL", "Оперативное ведение"
        INFORMATIONAL = "INFORMATIONAL", "Информационное ведение"
        UNKNOWN = "UNKNOWN", "Не установлено"

    class PublicationStatus(models.TextChoices):
        PENDING = "PENDING", "Ожидает"
        PUBLISHED = "PUBLISHED", "Опубликовано"
        SKIPPED = "SKIPPED", "Не создаёт назначения"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Требует проверки"

    source_revision = models.ForeignKey(
        PowerSystemSourceRevision,
        on_delete=models.CASCADE,
        related_name="authority_occurrences",
        verbose_name="Редакция источника",
    )
    asset_occurrence = models.ForeignKey(
        PowerSystemAssetOccurrence,
        on_delete=models.CASCADE,
        related_name="authority_occurrences",
        verbose_name="Строка объекта",
    )
    sequence = models.PositiveIntegerField("Порядок в ячейке")
    source_sheet = models.CharField("Лист источника", max_length=255)
    source_row = models.PositiveIntegerField("Строка источника")
    dispatcher_name_raw = models.CharField("Диспетчерское наименование", max_length=1000)
    authority_kind = models.CharField("Вид полномочия", max_length=32, choices=AuthorityKind.choices)
    assignment_status = models.CharField(
        "Состояние назначения",
        max_length=20,
        choices=AssignmentStatus.choices,
    )
    authority_subject_raw = models.CharField("Исходный субъект", max_length=1000, blank=True)
    authority_subject_normalized = models.CharField(
        "Предложенный субъект",
        max_length=1000,
        blank=True,
    )
    normalization_status = models.CharField("Состояние нормализации", max_length=40, blank=True)
    source_cell_raw = models.TextField("Исходная ячейка", blank=True)
    conduct_mode = models.CharField(
        "Режим ведения",
        max_length=16,
        choices=ConductMode.choices,
        default=ConductMode.UNKNOWN,
    )
    informational_basis = models.CharField("Основание режима ведения", max_length=255, blank=True)
    row_fingerprint = models.CharField("SHA-256 строки", max_length=64)
    publication_status = models.CharField(
        "Результат публикации",
        max_length=20,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PENDING,
    )
    published_target_model = models.CharField("Опубликованная модель", max_length=128, blank=True)
    published_target_id = models.CharField("Идентификатор записи", max_length=128, blank=True)
    publication_note = models.TextField("Комментарий публикации", blank=True)

    class Meta:
        ordering = ("asset_occurrence", "authority_kind", "sequence")
        constraints = [
            models.UniqueConstraint(
                fields=("asset_occurrence", "authority_kind", "sequence"),
                name="uniq_ps_authority_seq",
            )
        ]
        indexes = [
            models.Index(
                fields=("source_revision", "authority_kind", "assignment_status"),
                name="ps_authority_kind_idx",
            )
        ]
        verbose_name = "исходное назначение управления или ведения"
        verbose_name_plural = "исходные назначения управления и ведения"

    def __str__(self) -> str:
        return f"{self.asset_occurrence.occurrence_id} · {self.get_authority_kind_display()}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.asset_occurrence_id and self.source_revision_id:
            if self.asset_occurrence.source_revision_id != self.source_revision_id:
                errors["asset_occurrence"] = "Строка объекта относится к другой редакции."
        if self.assignment_status == self.AssignmentStatus.ASSIGNED and not self.authority_subject_raw:
            errors["authority_subject_raw"] = "Для назначения требуется субъект."
        if self.authority_kind == self.AuthorityKind.OPERATIONAL_MANAGEMENT:
            if self.conduct_mode != self.ConductMode.UNKNOWN:
                errors["conduct_mode"] = "Режим ведения не применяется к управлению."
        if len(self.row_fingerprint) != 64:
            errors["row_fingerprint"] = "Для строки требуется SHA-256."
        if errors:
            raise ValidationError(errors)


class PowerSystemAliasProposal(models.Model):
    class ReviewStatus(models.TextChoices):
        AUTO_SAFE = "AUTO_SAFE", "Безопасен для публикации"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Требует проверки"
        BLOCKED = "BLOCKED", "Автоприменение запрещено"

    class PublicationStatus(models.TextChoices):
        PENDING = "PENDING", "Ожидает"
        PUBLISHED = "PUBLISHED", "Опубликован"
        SKIPPED = "SKIPPED", "Не опубликован"

    source_revision = models.ForeignKey(
        PowerSystemSourceRevision,
        on_delete=models.CASCADE,
        related_name="alias_proposals",
        verbose_name="Редакция источника",
    )
    asset_occurrence = models.ForeignKey(
        PowerSystemAssetOccurrence,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="alias_proposals",
        verbose_name="Строка объекта",
    )
    alias_scope = models.CharField("Область алиаса", max_length=40)
    occurrence_id_raw = models.CharField("Исходная ссылка", max_length=128, blank=True)
    parent_context_raw = models.CharField("Контекст родителя", max_length=1000, blank=True)
    alias_raw = models.CharField("Алиас", max_length=1000)
    target_name_raw = models.CharField("Целевое имя", max_length=1000)
    alias_kind = models.CharField("Вид алиаса", max_length=64)
    normalization_rule = models.CharField("Правило нормализации", max_length=500, blank=True)
    confidence = models.CharField("Уверенность", max_length=16)
    proposal_status = models.CharField("Статус предложения", max_length=40)
    note = models.TextField("Примечание", blank=True)
    row_fingerprint = models.CharField("SHA-256 строки", max_length=64)
    review_status = models.CharField(
        "Состояние проверки",
        max_length=20,
        choices=ReviewStatus.choices,
    )
    publication_status = models.CharField(
        "Результат публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.PENDING,
    )
    published_alias = models.ForeignKey(
        "equipment.EquipmentAlias",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="source_alias_proposals",
        verbose_name="Опубликованный алиас",
    )

    class Meta:
        ordering = ("alias_scope", "alias_raw", "id")
        constraints = [
            models.UniqueConstraint(
                fields=(
                    "source_revision",
                    "alias_scope",
                    "occurrence_id_raw",
                    "alias_raw",
                    "target_name_raw",
                ),
                name="uniq_ps_alias_proposal",
            )
        ]
        verbose_name = "предложение алиаса объекта энергосистемы"
        verbose_name_plural = "предложения алиасов объектов энергосистемы"

    def __str__(self) -> str:
        return f"{self.alias_raw} → {self.target_name_raw}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.asset_occurrence_id and self.source_revision_id:
            if self.asset_occurrence.source_revision_id != self.source_revision_id:
                errors["asset_occurrence"] = "Строка объекта относится к другой редакции."
        if len(self.row_fingerprint) != 64:
            errors["row_fingerprint"] = "Для строки требуется SHA-256."
        if errors:
            raise ValidationError(errors)


class PowerSystemImportIssue(models.Model):
    class Severity(models.TextChoices):
        LOW = "LOW", "Низкая"
        MEDIUM = "MEDIUM", "Средняя"
        HIGH = "HIGH", "Высокая"
        CRITICAL = "CRITICAL", "Критическая"

    class Status(models.TextChoices):
        OPEN = "OPEN", "Открыта"
        RESOLVED = "RESOLVED", "Разрешена"
        ACCEPTED_RISK = "ACCEPTED_RISK", "Риск принят"

    source_revision = models.ForeignKey(
        PowerSystemSourceRevision,
        on_delete=models.CASCADE,
        related_name="issues",
        verbose_name="Редакция источника",
    )
    issue_code = models.CharField("Код проблемы", max_length=96)
    severity = models.CharField("Важность", max_length=16, choices=Severity.choices)
    category = models.CharField("Категория", max_length=64)
    source_sheet = models.CharField("Лист источника", max_length=500, blank=True)
    source_rows = models.CharField("Строки источника", max_length=500, blank=True)
    evidence = models.TextField("Наблюдение")
    import_risk = models.TextField("Риск импорта")
    recommended_handling = models.TextField("Рекомендуемая обработка")
    blocks_automatic_import = models.BooleanField("Блокирует автоматическую публикацию")
    status = models.CharField("Состояние", max_length=20, choices=Status.choices)
    resolution_note = models.TextField("Решение", blank=True)
    resolved_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="resolved_power_system_issues",
        verbose_name="Решил",
    )
    resolved_at = models.DateTimeField("Решено", null=True, blank=True)
    row_fingerprint = models.CharField("SHA-256 строки", max_length=64)

    class Meta:
        ordering = ("-severity", "issue_code")
        constraints = [
            models.UniqueConstraint(
                fields=("source_revision", "issue_code"),
                name="uniq_power_system_issue_code",
            )
        ]
        verbose_name = "проблема импорта объектов энергосистемы"
        verbose_name_plural = "проблемы импорта объектов энергосистемы"

    def __str__(self) -> str:
        return f"{self.issue_code} · {self.get_severity_display()}"


class PowerSystemPublication(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    source_revision = models.ForeignKey(
        PowerSystemSourceRevision,
        on_delete=models.PROTECT,
        related_name="publications",
        verbose_name="Редакция источника",
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="power_system_publications",
        verbose_name="Опубликовал",
    )
    schema_version = models.CharField(
        "Версия схемы",
        max_length=64,
        default="eod.power-system.publication.v1",
    )
    canonical_json = models.TextField("Канонический снимок публикации")
    digest = models.CharField("SHA-256 публикации", max_length=64, unique=True)
    result_summary = models.JSONField("Итоги публикации", default=dict)
    created_at = models.DateTimeField("Опубликовано", auto_now_add=True)

    objects = ImmutableAuditManager()

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "публикация объектов энергосистемы"
        verbose_name_plural = "публикации объектов энергосистемы"

    def __str__(self) -> str:
        return f"{self.source_revision.original_filename} · {self.digest[:12]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Снимок публикации объектов энергосистемы неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление публикации объектов энергосистемы запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.source_revision_id and self.actor_id:
            if self.source_revision.organization_id != self.actor.organization_id:
                errors["actor"] = "Публикующий сотрудник относится к другой организации."
        if len(self.digest) != 64:
            errors["digest"] = "Для публикации требуется SHA-256."


class PersonnelSourceRevision(models.Model):
    class Status(models.TextChoices):
        STAGED = "STAGED", "Подготовлена к проверке"
        PARTIALLY_PUBLISHED = "PARTIALLY_PUBLISHED", "Опубликована частично"
        PUBLISHED = "PUBLISHED", "Опубликована"
        DISCARDED = "DISCARDED", "Убрана из рабочего списка"

    class LayoutVersion(models.TextChoices):
        CURRENT_28_COLUMNS = "CURRENT_28_COLUMNS", "Текущая матрица с подразделением"
        LEGACY_22_COLUMNS = "LEGACY_22_COLUMNS", "Ранняя матрица без отдельного подразделения"

    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="personnel_source_revisions",
        verbose_name="Организация",
    )
    data_profile = models.ForeignKey(
        DataProfile,
        on_delete=models.PROTECT,
        related_name="personnel_source_revisions",
        verbose_name="Профиль данных",
    )
    uploaded_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="uploaded_personnel_revisions",
        verbose_name="Загрузил",
    )
    source_reference = models.CharField("Источник или основание", max_length=1000)
    effective_from = models.DateField("Действует с")
    original_filename = models.CharField("Имя XLSX", max_length=255)
    file_size = models.PositiveBigIntegerField("Размер XLSX, байт")
    file_sha256 = models.CharField("SHA-256 XLSX", max_length=64)
    sheet_name = models.CharField("Лист", max_length=255)
    layout_version = models.CharField(
        "Версия структуры",
        max_length=32,
        choices=LayoutVersion.choices,
    )
    document_date = models.DateField("Дата документа", null=True, blank=True)
    document_number = models.CharField("Номер документа", max_length=255, blank=True)
    manifest = models.JSONField("Манифест разбора", default=dict)
    footnotes = models.JSONField("Сноски источника", default=dict)
    total_people = models.PositiveIntegerField("Работников", default=0)
    total_authority_cells = models.PositiveIntegerField("Ячеек полномочий", default=0)
    ready_rows = models.PositiveIntegerField("Готовых строк", default=0)
    review_rows = models.PositiveIntegerField("Строк на проверке", default=0)
    blocked_rows = models.PositiveIntegerField("Заблокированных строк", default=0)
    publishable_grants = models.PositiveIntegerField("Публикуемых прав", default=0)
    ambiguous_cells = models.PositiveIntegerField("Неоднозначных ячеек", default=0)
    status = models.CharField(
        "Состояние",
        max_length=24,
        choices=Status.choices,
        default=Status.STAGED,
        db_index=True,
    )
    publication_digest = models.CharField(
        "SHA-256 публикации",
        max_length=64,
        blank=True,
        editable=False,
    )
    published_at = models.DateTimeField("Опубликовано", null=True, blank=True)
    published_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_personnel_revisions",
        verbose_name="Опубликовал",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)
    discarded_at = models.DateTimeField("Убрано из рабочего списка", null=True, blank=True)

    class Meta:
        ordering = ("-created_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "file_sha256"),
                name="uniq_personnel_source_sha_org",
            )
        ]
        indexes = [
            models.Index(
                fields=("organization", "status", "-created_at"),
                name="personnel_src_status_idx",
            )
        ]
        verbose_name = "редакция источника персонала и прав"
        verbose_name_plural = "редакции источников персонала и прав"

    def __str__(self) -> str:
        return f"{self.original_filename} · {self.get_status_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.original_filename = self.original_filename.strip()
        self.file_sha256 = self.file_sha256.strip().lower()
        self.source_reference = self.source_reference.strip()
        self.document_number = self.document_number.strip()
        self.sheet_name = self.sheet_name.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            "Физическое удаление редакции персонала запрещено. Используйте удаление из рабочего списка."
        )

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.data_profile_id and self.organization_id:
            if self.data_profile.organization_id != self.organization_id:
                errors["data_profile"] = "Профиль данных относится к другой организации."
            if (
                self.data_profile.code != "local-validation"
                or self.data_profile.kind != DataProfile.Kind.LOCAL_VALIDATION
                or not self.data_profile.allows_real_personal_data
                or self.data_profile.export_policy != DataProfile.ExportPolicy.PROHIBITED
            ):
                errors["data_profile"] = (
                    "Матрица работников допускается только в неэкспортируемом "
                    "профиле local-validation."
                )
        if self.uploaded_by_id and self.organization_id:
            if self.uploaded_by.organization_id != self.organization_id:
                errors["uploaded_by"] = "Загрузивший сотрудник относится к другой организации."
        if self.published_by_id and self.organization_id:
            if self.published_by.organization_id != self.organization_id:
                errors["published_by"] = "Публикующий сотрудник относится к другой организации."
        if len(self.file_sha256.strip()) != 64:
            errors["file_sha256"] = "Для XLSX требуется SHA-256."
        if not isinstance(self.manifest, dict):
            errors["manifest"] = "Манифест должен храниться JSON-объектом."
        if not isinstance(self.footnotes, dict):
            errors["footnotes"] = "Сноски должны храниться JSON-объектом."
        if self.status in {self.Status.PUBLISHED, self.Status.PARTIALLY_PUBLISHED}:
            if not self.published_at or not self.published_by_id or len(self.publication_digest) != 64:
                errors["status"] = "Публикация требует автора, времени и SHA-256."
        elif self.published_at or self.published_by_id or self.publication_digest:
            errors["status"] = "Реквизиты публикации допустимы только после публикации."
        if self.status == self.Status.DISCARDED and self.discarded_at is None:
            errors["discarded_at"] = "Для убранной редакции требуется время операции."
        if errors:
            raise ValidationError(errors)


class PersonnelSourceRow(models.Model):
    class MatchKind(models.TextChoices):
        NONE = "NONE", "Совпадение не найдено"
        EXACT = "EXACT", "Однозначное точное совпадение"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Совпадение требует проверки"

    class ReviewStatus(models.TextChoices):
        READY = "READY", "Готова"
        REVIEW_REQUIRED = "REVIEW_REQUIRED", "Требует проверки"
        BLOCKED = "BLOCKED", "Заблокирована"
        PUBLISHED = "PUBLISHED", "Опубликована"
        EXCLUDED = "EXCLUDED", "Исключена"

    source_revision = models.ForeignKey(
        PersonnelSourceRevision,
        on_delete=models.PROTECT,
        related_name="person_rows",
        verbose_name="Редакция источника",
    )
    source_row_number = models.PositiveIntegerField("Строка XLSX")
    source_sequence = models.PositiveIntegerField("Номер по источнику")
    full_name_raw = models.CharField("ФИО из источника", max_length=500)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    first_name = models.CharField("Имя", max_length=150, blank=True)
    middle_name = models.CharField("Отчество", max_length=150, blank=True)
    position_raw = models.CharField("Должность из источника", max_length=500)
    division_raw = models.CharField("Подразделение из источника", max_length=500, blank=True)
    personnel_category_raw = models.CharField("Категория персонала", max_length=128, blank=True)
    electrical_safety_raw = models.CharField("Группа и класс напряжения", max_length=500, blank=True)
    electrical_safety_group = models.CharField("Группа", max_length=16, blank=True)
    voltage_scope = models.CharField("Класс напряжения", max_length=255, blank=True)
    installation_scope_raw = models.TextField("Область электроустановок", blank=True)
    rza_category_raw = models.CharField("Категория РЗА", max_length=128, blank=True)
    matched_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="matched_personnel_source_rows",
        verbose_name="Предполагаемый сотрудник",
    )
    match_kind = models.CharField(
        "Результат сопоставления",
        max_length=24,
        choices=MatchKind.choices,
        default=MatchKind.NONE,
    )
    review_status = models.CharField(
        "Состояние проверки",
        max_length=24,
        choices=ReviewStatus.choices,
        db_index=True,
    )
    issues = models.JSONField("Проблемы строки", default=list, blank=True)
    fingerprint = models.CharField("SHA-256 строки", max_length=64)
    published_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_personnel_source_rows",
        verbose_name="Опубликованный сотрудник",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ("source_revision", "source_row_number")
        constraints = [
            models.UniqueConstraint(
                fields=("source_revision", "source_row_number"),
                name="uniq_personnel_source_row",
            )
        ]
        verbose_name = "строка источника персонала"
        verbose_name_plural = "строки источника персонала"

    def __str__(self) -> str:
        return f"Строка {self.source_row_number}: {self.full_name_raw}"

    @property
    def full_name(self) -> str:
        return " ".join(part for part in (self.last_name, self.first_name, self.middle_name) if part)

    def clean(self) -> None:
        super().clean()
        if not isinstance(self.issues, list):
            raise ValidationError({"issues": "Проблемы должны храниться JSON-массивом."})
        if len(self.fingerprint.strip()) != 64:
            raise ValidationError({"fingerprint": "Для строки требуется SHA-256."})
        if self.matched_employee_id and self.source_revision_id:
            if self.matched_employee.organization_id != self.source_revision.organization_id:
                raise ValidationError({"matched_employee": "Сотрудник относится к другой организации."})
        if self.published_employee_id and self.source_revision_id:
            if self.published_employee.organization_id != self.source_revision.organization_id:
                raise ValidationError({"published_employee": "Сотрудник относится к другой организации."})


class PersonnelAuthorityCell(models.Model):
    class GrantState(models.TextChoices):
        GRANTED = "GRANTED", "Право предоставлено"
        NOT_GRANTED = "NOT_GRANTED", "Право не предоставлено"
        BLANK = "BLANK", "Значение отсутствует"
        QUALIFIED = "QUALIFIED", "Право с квалификатором"
        AMBIGUOUS = "AMBIGUOUS", "Неоднозначное значение"

    person_row = models.ForeignKey(
        PersonnelSourceRow,
        on_delete=models.PROTECT,
        related_name="authority_cells",
        verbose_name="Строка работника",
    )
    right_definition = models.ForeignKey(
        "organizations.OperationalRightDefinition",
        on_delete=models.PROTECT,
        related_name="source_cells",
        verbose_name="Вид права",
    )
    source_column = models.CharField("Колонка XLSX", max_length=8)
    source_header = models.CharField("Заголовок источника", max_length=500)
    raw_marker = models.CharField("Исходная отметка", max_length=500, blank=True)
    grant_state = models.CharField(
        "Состояние",
        max_length=16,
        choices=GrantState.choices,
    )
    qualifier = models.CharField("Квалификатор", max_length=500, blank=True)
    footnote_numbers = models.JSONField("Номера сносок", default=list, blank=True)
    equipment_groups = models.JSONField("Группы оборудования", default=list, blank=True)
    issues = models.JSONField("Проблемы ячейки", default=list, blank=True)
    is_publishable = models.BooleanField("Можно опубликовать автоматически", default=False)

    class Meta:
        ordering = ("person_row", "right_definition__display_order")
        constraints = [
            models.UniqueConstraint(
                fields=("person_row", "right_definition"),
                name="uniq_personnel_authority_cell",
            )
        ]
        verbose_name = "ячейка полномочия"
        verbose_name_plural = "ячейки полномочий"

    def __str__(self) -> str:
        return f"{self.person_row.full_name_raw}: {self.right_definition}"

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        for field in ("footnote_numbers", "equipment_groups", "issues"):
            if not isinstance(getattr(self, field), list):
                errors[field] = "Значение должно храниться JSON-массивом."
        if self.is_publishable and self.grant_state not in {
            self.GrantState.GRANTED,
            self.GrantState.QUALIFIED,
        }:
            errors["is_publishable"] = "Публикуются только положительные однозначные отметки."
        if errors:
            raise ValidationError(errors)


class PersonnelPublication(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    source_revision = models.OneToOneField(
        PersonnelSourceRevision,
        on_delete=models.PROTECT,
        related_name="publication",
        verbose_name="Редакция источника",
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="personnel_publications",
        verbose_name="Опубликовал",
    )
    schema_version = models.CharField(
        "Версия схемы",
        max_length=64,
        default="eod.personnel-authority.publication.v1",
    )
    canonical_json = models.TextField("Канонический снимок публикации")
    digest = models.CharField("SHA-256 публикации", max_length=64, unique=True)
    result_summary = models.JSONField("Итоги публикации", default=dict)
    created_at = models.DateTimeField("Опубликовано", auto_now_add=True)

    objects = ImmutableAuditManager()

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "публикация персонала и полномочий"
        verbose_name_plural = "публикации персонала и полномочий"

    def __str__(self) -> str:
        return f"{self.source_revision.original_filename} · {self.digest[:12]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Снимок публикации персонала неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление публикации персонала запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.source_revision_id and self.actor_id:
            if self.source_revision.organization_id != self.actor.organization_id:
                errors["actor"] = "Публикующий сотрудник относится к другой организации."
        if len(self.digest) != 64:
            errors["digest"] = "Для публикации требуется SHA-256."
        if not isinstance(self.result_summary, dict):
            errors["result_summary"] = "Итоги должны храниться JSON-объектом."
        if errors:
            raise ValidationError(errors)
