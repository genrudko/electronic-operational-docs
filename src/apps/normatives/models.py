from __future__ import annotations

from datetime import date
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.organizations.models import Employee, Organization


def validate_window(start: date, end: date | None, field: str = "effective_until") -> None:
    if end is not None and end < start:
        raise ValidationError({field: "Дата окончания не может быть раньше даты начала."})


def windows_overlap(
    first_start: date,
    first_end: date | None,
    second_start: date,
    second_end: date | None,
) -> bool:
    return first_start <= (second_end or date.max) and second_start <= (first_end or date.max)


class ProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение версионируемых нормативных записей запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление нормативных записей запрещено.")


ProtectedManager = models.Manager.from_queryset(ProtectedQuerySet)


class PublicationStatus(models.TextChoices):
    DRAFT = "DRAFT", "Черновик"
    PUBLISHED = "PUBLISHED", "Опубликована"


class NormativeDocument(models.Model):
    class Scope(models.TextChoices):
        FEDERAL = "FEDERAL", "Федеральный нормативный документ"
        INDUSTRY = "INDUSTRY", "Отраслевой нормативный документ"
        LOCAL = "LOCAL", "Локальный документ организации"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="normative_documents",
        verbose_name="Организация",
    )
    code = models.SlugField("Системный код", max_length=96, unique=True)
    title = models.CharField("Полное наименование", max_length=1000)
    short_title = models.CharField("Краткое наименование", max_length=255, blank=True)
    scope = models.CharField("Уровень документа", max_length=24, choices=Scope.choices)
    issuer = models.CharField("Издатель", max_length=500)
    document_number = models.CharField("Номер документа", max_length=128, blank=True)
    document_date = models.DateField("Дата документа", null=True, blank=True)
    is_active = models.BooleanField("Используется в реестре", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("scope", "short_title", "title")
        verbose_name = "нормативный документ"
        verbose_name_plural = "нормативные документы"

    def __str__(self) -> str:
        return self.short_title or self.title

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        if self.pk and self.revisions.filter(status=PublicationStatus.PUBLISHED).exists():
            original = type(self).objects.get(pk=self.pk)
            protected = (
                "organization_id",
                "code",
                "title",
                "short_title",
                "scope",
                "issuer",
                "document_number",
                "document_date",
            )
            if any(getattr(original, field) != getattr(self, field) for field in protected):
                raise ValidationError(
                    "Реквизиты документа с опубликованной редакцией неизменяемы."
                )
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.scope == self.Scope.LOCAL and not self.organization_id:
            raise ValidationError({"organization": "Для локального документа организация обязательна."})
        if self.scope != self.Scope.LOCAL and self.organization_id:
            raise ValidationError(
                {"organization": "Организация указывается только для локального документа."}
            )


class NormativeRevision(models.Model):
    document = models.ForeignKey(
        NormativeDocument,
        on_delete=models.PROTECT,
        related_name="revisions",
        verbose_name="Нормативный документ",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    status = models.CharField(
        "Статус публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
        db_index=True,
    )
    effective_from = models.DateField("Действует с")
    effective_until = models.DateField("Действует по", null=True, blank=True)
    source_reference = models.CharField("Источник или ссылка на оригинал", max_length=1000, blank=True)
    change_summary = models.TextField("Описание редакции", blank=True)
    approved_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="approved_normative_revisions",
        verbose_name="Опубликовал",
    )
    published_at = models.DateTimeField("Опубликована", null=True, blank=True, editable=False)
    digest = models.CharField("SHA-256 опубликованной редакции", max_length=64, blank=True, editable=False)
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("document", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("document", "revision_number"),
                name="uniq_normative_revision_number",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="DRAFT", published_at__isnull=True, digest="")
                    | (Q(status="PUBLISHED", published_at__isnull=False) & ~Q(digest=""))
                ),
                name="normative_revision_publication_consistent",
            ),
        ]
        verbose_name = "редакция нормативного документа"
        verbose_name_plural = "редакции нормативных документов"

    def __str__(self) -> str:
        return f"{self.document} · редакция № {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == PublicationStatus.PUBLISHED:
                raise ValidationError("Опубликованная редакция нормативного документа неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление редакции нормативного документа запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.effective_from, self.effective_until)
        if self.approved_by_id and self.document.organization_id:
            if self.approved_by.organization_id != self.document.organization_id:
                raise ValidationError(
                    {"approved_by": "Публикующий сотрудник относится к другой организации."}
                )
        if self.status == PublicationStatus.PUBLISHED:
            if not self.published_at:
                raise ValidationError({"published_at": "Для публикации требуется серверное время."})
            if len(self.digest) != 64:
                raise ValidationError({"digest": "Для публикации требуется SHA-256 редакции."})


class NormativeRequirement(models.Model):
    revision = models.ForeignKey(
        NormativeRevision,
        on_delete=models.PROTECT,
        related_name="requirements",
        verbose_name="Редакция",
    )
    code = models.CharField("Код требования", max_length=96)
    clause = models.CharField("Пункт документа", max_length=128)
    title = models.CharField("Краткое содержание", max_length=500)
    requirement_text = models.TextField("Требование")
    applicability_text = models.TextField("Область применимости", blank=True)
    is_mandatory = models.BooleanField("Обязательное требование", default=True)
    display_order = models.PositiveIntegerField("Порядок отображения", default=0)

    objects = ProtectedManager()

    class Meta:
        ordering = ("revision", "display_order", "code")
        constraints = [
            models.UniqueConstraint(
                fields=("revision", "code"),
                name="uniq_requirement_code_per_revision",
            )
        ]
        verbose_name = "нормативное требование"
        verbose_name_plural = "нормативные требования"

    def __str__(self) -> str:
        return f"{self.code}: {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.revision.status == PublicationStatus.PUBLISHED:
            raise ValidationError("Требования опубликованной редакции неизменяемы.")
        self.code = self.code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление нормативного требования запрещено.")


class RequirementTrace(models.Model):
    class ImplementationStatus(models.TextChoices):
        PLANNED = "PLANNED", "Запланировано"
        IMPLEMENTED = "IMPLEMENTED", "Реализовано"
        VERIFIED = "VERIFIED", "Проверено"
        NOT_APPLICABLE = "NOT_APPLICABLE", "Не применяется"

    requirement = models.ForeignKey(
        NormativeRequirement,
        on_delete=models.PROTECT,
        related_name="traces",
        verbose_name="Нормативное требование",
    )
    function_code = models.CharField("Код функции", max_length=128)
    function_name = models.CharField("Функция системы", max_length=500)
    implementation_status = models.CharField(
        "Состояние реализации",
        max_length=24,
        choices=ImplementationStatus.choices,
        default=ImplementationStatus.PLANNED,
    )
    test_reference = models.CharField("Автоматический тест", max_length=500, blank=True)
    acceptance_scenario = models.TextField("Приёмочный сценарий", blank=True)
    notes = models.TextField("Примечание", blank=True)
    created_at = models.DateTimeField("Зафиксировано", default=timezone.now, editable=False)

    objects = ProtectedManager()

    class Meta:
        ordering = ("requirement", "function_code", "-created_at")
        verbose_name = "трассировка требования"
        verbose_name_plural = "трассировки требований"

    def __str__(self) -> str:
        return f"{self.requirement.code} → {self.function_name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Запись трассировки неизменяема; создайте новую запись.")
        self.function_code = self.function_code.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление трассировки запрещено.")


class OrganizationNameRevision(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="name_revisions",
        verbose_name="Организация",
    )
    full_name = models.CharField("Полное наименование", max_length=1000)
    short_name = models.CharField("Краткое наименование", max_length=255, blank=True)
    valid_from = models.DateField("Действует с")
    valid_until = models.DateField("Действует по", null=True, blank=True)
    basis_reference = models.CharField("Документ-основание", max_length=1000, blank=True)
    status = models.CharField(
        "Статус публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
    )
    published_at = models.DateTimeField("Опубликована", null=True, blank=True, editable=False)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_organization_name_revisions",
        verbose_name="Создал",
    )

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization", "-valid_from")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "valid_from"),
                name="uniq_organization_name_revision_start",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="DRAFT", published_at__isnull=True)
                    | Q(status="PUBLISHED", published_at__isnull=False)
                ),
                name="organization_name_publication_consistent",
            ),
        ]
        verbose_name = "историческое наименование организации"
        verbose_name_plural = "исторические наименования организаций"

    def __str__(self) -> str:
        return f"{self.organization} · {self.full_name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == PublicationStatus.PUBLISHED:
                raise ValidationError("Опубликованное наименование организации неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление исторического наименования запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.valid_from, self.valid_until, "valid_until")
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            raise ValidationError({"created_by": "Сотрудник относится к другой организации."})
        conflicts = type(self).objects.filter(organization=self.organization).exclude(pk=self.pk)
        for other in conflicts:
            if windows_overlap(
                self.valid_from,
                self.valid_until,
                other.valid_from,
                other.valid_until,
            ):
                raise ValidationError(
                    {"valid_from": "Период пересекается с другой редакцией наименования."}
                )


class OrganizationConfigurationRevision(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="configuration_revisions",
        verbose_name="Организация",
    )
    revision_number = models.PositiveIntegerField("Номер редакции")
    effective_from = models.DateField("Действует с")
    effective_until = models.DateField("Действует по", null=True, blank=True)
    configuration = models.JSONField("Конфигурация организации", default=dict)
    change_summary = models.TextField("Описание изменений", blank=True)
    status = models.CharField(
        "Статус публикации",
        max_length=16,
        choices=PublicationStatus.choices,
        default=PublicationStatus.DRAFT,
    )
    published_at = models.DateTimeField("Опубликована", null=True, blank=True, editable=False)
    digest = models.CharField(
        "SHA-256 опубликованной конфигурации",
        max_length=64,
        blank=True,
        editable=False,
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_configuration_revisions",
        verbose_name="Создал",
    )

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization", "-revision_number")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "revision_number"),
                name="uniq_organization_configuration_revision",
            ),
            models.CheckConstraint(
                condition=(
                    Q(status="DRAFT", published_at__isnull=True, digest="")
                    | (Q(status="PUBLISHED", published_at__isnull=False) & ~Q(digest=""))
                ),
                name="organization_configuration_publication_consistent",
            ),
        ]
        verbose_name = "редакция конфигурации организации"
        verbose_name_plural = "редакции конфигурации организаций"

    def __str__(self) -> str:
        return f"{self.organization} · конфигурация № {self.revision_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == PublicationStatus.PUBLISHED:
                raise ValidationError("Опубликованная конфигурация организации неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление конфигурации организации запрещено.")

    def clean(self) -> None:
        super().clean()
        validate_window(self.effective_from, self.effective_until)
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            raise ValidationError({"created_by": "Сотрудник относится к другой организации."})
        if not isinstance(self.configuration, dict):
            raise ValidationError({"configuration": "Конфигурация должна быть JSON-объектом."})
        if self.status == PublicationStatus.PUBLISHED:
            if not self.published_at:
                raise ValidationError({"published_at": "Для публикации требуется серверное время."})
            if len(self.digest) != 64:
                raise ValidationError({"digest": "Для публикации требуется SHA-256 конфигурации."})
