from __future__ import annotations

import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from .models import Employee, Organization


class OrganizationRelationKind(models.TextChoices):
    OWN = "OWN", "Собственная организация"
    DISPATCH_CENTER = "DISPATCH_CENTER", "Диспетчерский центр"
    RELATED_GRID = "RELATED_GRID", "Смежная сетевая организация"
    RELATED_SITE = "RELATED_SITE", "Смежный энергообъект"
    COMMERCIAL_DISPATCH = "COMMERCIAL_DISPATCH", "Коммерческий диспетчерский центр"
    CONTRACTOR = "CONTRACTOR", "Подрядная организация"
    OTHER = "OTHER", "Иная внешняя организация"


class OrganizationOperationalProfile(models.Model):
    organization = models.OneToOneField(
        Organization,
        on_delete=models.PROTECT,
        related_name="operational_profile",
        verbose_name="Организация",
    )
    relation_kind = models.CharField(
        "Вид отношения",
        max_length=32,
        choices=OrganizationRelationKind.choices,
        default=OrganizationRelationKind.OWN,
    )
    directory_scope = models.TextField("Область включения в справочник", blank=True)
    is_active = models.BooleanField("Действующий профиль", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    class Meta:
        verbose_name = "операционный профиль организации"
        verbose_name_plural = "операционные профили организаций"

    def __str__(self) -> str:
        return f"{self.organization}: {self.get_relation_kind_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.directory_scope = " ".join(self.directory_scope.split())
        self.full_clean()
        super().save(*args, **kwargs)


class EmployeeContactProfile(models.Model):
    employee = models.OneToOneField(
        Employee,
        on_delete=models.PROTECT,
        related_name="contact_profile",
        verbose_name="Сотрудник",
    )
    primary_phone = models.CharField("Основной телефон", max_length=100, blank=True)
    operational_phone = models.CharField("Оперативный телефон", max_length=100, blank=True)
    email = models.EmailField("Электронная почта", blank=True)
    availability_schedule = models.CharField("Часы работы", max_length=255, blank=True)
    is_round_the_clock = models.BooleanField("Круглосуточный контакт", default=False)
    note = models.TextField("Примечание", blank=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    class Meta:
        verbose_name = "контактный профиль сотрудника"
        verbose_name_plural = "контактные профили сотрудников"

    def __str__(self) -> str:
        return f"Контакты: {self.employee}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.primary_phone = " ".join(self.primary_phone.split())
        self.operational_phone = " ".join(self.operational_phone.split())
        self.email = self.email.strip().lower()
        self.availability_schedule = " ".join(self.availability_schedule.split())
        self.note = self.note.strip()
        self.full_clean()
        super().save(*args, **kwargs)


class SpecialQualificationKind(models.TextChoices):
    HEIGHT = "HEIGHT", "Группа допуска к работам на высоте"
    RZA = "RZA", "Категория допуска по РЗА"
    LIVE_WORK = "LIVE_WORK", "Допуск к работам под напряжением"
    OTHER = "OTHER", "Иная специальная квалификация"


class EmployeeSpecialQualification(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="special_qualifications",
        verbose_name="Сотрудник",
    )
    kind = models.CharField(
        "Вид квалификации",
        max_length=24,
        choices=SpecialQualificationKind.choices,
    )
    level = models.CharField("Уровень или категория", max_length=64)
    scope_text = models.TextField("Область действия", blank=True)
    valid_from = models.DateField("Действует с")
    valid_until = models.DateField("Действует по", null=True, blank=True)
    basis_reference = models.CharField("Документ-основание", max_length=1000)
    source_file_sha256 = models.CharField("SHA-256 исходного файла", max_length=64, blank=True)
    source_row_number = models.PositiveIntegerField("Строка исходного файла", null=True, blank=True)
    is_active = models.BooleanField("Действующая квалификация", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    class Meta:
        ordering = ("employee__last_name", "kind", "-valid_from", "-id")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="employee_special_qualification_valid_window",
            ),
            models.UniqueConstraint(
                fields=("employee", "kind", "level", "valid_from", "basis_reference"),
                name="uniq_employee_special_qualification_start_basis",
            ),
        ]
        verbose_name = "специальная квалификация сотрудника"
        verbose_name_plural = "специальные квалификации сотрудников"

    def __str__(self) -> str:
        return f"{self.employee}: {self.get_kind_display()} — {self.level}"

    def clean(self) -> None:
        super().clean()
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError({"valid_until": "Окончание периода раньше начала."})
        if self.source_file_sha256 and len(self.source_file_sha256.strip()) != 64:
            raise ValidationError({"source_file_sha256": "Требуется SHA-256 или пустое значение."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.level = " ".join(self.level.split())
        self.scope_text = " ".join(self.scope_text.split())
        self.basis_reference = self.basis_reference.strip()
        self.source_file_sha256 = self.source_file_sha256.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)


class ExternalOperationalRelationKind(models.TextChoices):
    DISPATCH = "DISPATCH", "Диспетчерский персонал"
    OPERATIONAL = "OPERATIONAL", "Оперативный персонал"
    MANAGEMENT = "MANAGEMENT", "Руководство"
    CONTROL_CENTER = "CONTROL_CENTER", "Персонал центра управления сетями"
    COMMERCIAL_DISPATCH = "COMMERCIAL_DISPATCH", "Коммерческий диспетчер"
    RELATED_SITE = "RELATED_SITE", "Персонал смежного энергообъекта"


class ExternalOperationalContact(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="external_operational_contacts",
        verbose_name="Сотрудник внешней организации",
    )
    host_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="external_operational_directory",
        verbose_name="Организация, ведущая справочник",
    )
    relation_kind = models.CharField(
        "Роль во взаимодействии",
        max_length=32,
        choices=ExternalOperationalRelationKind.choices,
    )
    operational_scope = models.TextField("Область взаимодействия", blank=True)
    authority_summary = models.TextField("Полномочия во взаимодействии", blank=True)
    valid_from = models.DateField("Действует с")
    valid_until = models.DateField("Действует по", null=True, blank=True)
    basis_reference = models.CharField("Документ-основание", max_length=1000)
    is_active = models.BooleanField("Действующая запись", default=True)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)

    class Meta:
        ordering = (
            "employee__organization__name",
            "relation_kind",
            "employee__last_name",
        )
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="external_operational_contact_valid_window",
            ),
            models.UniqueConstraint(
                fields=("employee", "host_organization", "relation_kind", "valid_from"),
                name="uniq_external_operational_contact_start",
            ),
        ]
        verbose_name = "внешний оперативный контакт"
        verbose_name_plural = "внешние оперативные контакты"

    def __str__(self) -> str:
        return f"{self.employee} → {self.host_organization}: {self.get_relation_kind_display()}"

    def clean(self) -> None:
        super().clean()
        if self.valid_until and self.valid_until < self.valid_from:
            raise ValidationError({"valid_until": "Окончание периода раньше начала."})
        if self.employee_id and self.employee.organization_id == self.host_organization_id:
            raise ValidationError({"host_organization": "Для штатного сотрудника используется матрица прав."})

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.operational_scope = " ".join(self.operational_scope.split())
        self.authority_summary = " ".join(self.authority_summary.split())
        self.basis_reference = self.basis_reference.strip()
        self.full_clean()
        super().save(*args, **kwargs)


class PersonnelImportKind(models.TextChoices):
    INTERNAL_MATRIX = "INTERNAL_MATRIX", "Матрица штатного персонала"
    EXTERNAL_DIRECTORY = "EXTERNAL_DIRECTORY", "Внешний оперативный справочник"


class PersonnelImportStatus(models.TextChoices):
    PREVIEW = "PREVIEW", "Предварительный просмотр"
    PUBLISHED = "PUBLISHED", "Опубликовано"
    REJECTED = "REJECTED", "Отклонено"


class PersonnelImportBatch(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    target_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="personnel_import_batches",
        verbose_name="Организация-держатель справочника",
    )
    source_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="outgoing_personnel_import_batches",
        verbose_name="Организация-источник",
    )
    import_kind = models.CharField(
        "Вид импорта",
        max_length=32,
        choices=PersonnelImportKind.choices,
    )
    status = models.CharField(
        "Состояние",
        max_length=16,
        choices=PersonnelImportStatus.choices,
        default=PersonnelImportStatus.PREVIEW,
    )
    uploaded_name = models.CharField("Имя файла", max_length=255)
    file_sha256 = models.CharField("SHA-256 файла", max_length=64, unique=True)
    sheet_name = models.CharField("Лист", max_length=255, blank=True)
    source_reference = models.CharField("Документ-основание", max_length=1000)
    effective_from = models.DateField("Действует с")
    preview = models.JSONField("Результат предварительного просмотра", default=dict)
    validation_errors = models.JSONField("Ошибки проверки", default=list)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="uploaded_personnel_import_batches",
        verbose_name="Загрузил",
    )
    published_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_personnel_import_batches",
        verbose_name="Опубликовал",
    )
    created_at = models.DateTimeField("Загружен", auto_now_add=True)
    published_at = models.DateTimeField("Опубликован", null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "пакет импорта персонала"
        verbose_name_plural = "пакеты импорта персонала"

    def __str__(self) -> str:
        return f"{self.uploaded_name}: {self.get_status_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.uploaded_name = self.uploaded_name.strip()
        self.file_sha256 = self.file_sha256.strip().lower()
        self.source_reference = self.source_reference.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if len(self.file_sha256) != 64:
            raise ValidationError({"file_sha256": "Требуется SHA-256 загруженного файла."})
        if self.status == PersonnelImportStatus.PUBLISHED and not self.published_at:
            raise ValidationError({"published_at": "Для опубликованного пакета требуется дата публикации."})

    def mark_published(self, user) -> None:
        self.status = PersonnelImportStatus.PUBLISHED
        self.published_by = user
        self.published_at = timezone.now()
        self.save(update_fields=("status", "published_by", "published_at"))


class PersonnelChangeAction(models.TextChoices):
    CREATE = "CREATE", "Создание карточки"
    UPDATE = "UPDATE", "Изменение карточки"
    DEACTIVATE = "DEACTIVATE", "Деактивация карточки"
    QUALIFICATION = "QUALIFICATION", "Изменение квалификации"
    RIGHT = "RIGHT", "Изменение права"
    IMPORT_PREVIEW = "IMPORT_PREVIEW", "Предварительный просмотр импорта"
    IMPORT_PUBLISH = "IMPORT_PUBLISH", "Публикация импорта"


class PersonnelChangeRecord(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="change_records",
        verbose_name="Сотрудник",
    )
    batch = models.ForeignKey(
        PersonnelImportBatch,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="change_records",
        verbose_name="Пакет импорта",
    )
    action = models.CharField("Действие", max_length=24, choices=PersonnelChangeAction.choices)
    reason = models.CharField("Основание изменения", max_length=1000)
    before_snapshot = models.JSONField("Состояние до изменения", default=dict)
    after_snapshot = models.JSONField("Состояние после изменения", default=dict)
    changed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="personnel_change_records",
        verbose_name="Изменил",
    )
    created_at = models.DateTimeField("Зафиксировано", auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-id")
        verbose_name = "запись изменения персонала"
        verbose_name_plural = "записи изменений персонала"

    def __str__(self) -> str:
        subject = self.employee.full_name if self.employee_id else self.batch
        return f"{subject}: {self.get_action_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Записи истории изменений неизменяемы.")
        self.reason = self.reason.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление истории изменений запрещено.")
