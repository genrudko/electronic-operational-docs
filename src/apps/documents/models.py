from __future__ import annotations

import json
import uuid
from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.organizations.models import Employee, Organization


class ImmutableQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение документарных записей запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление документарных записей запрещено.")


ImmutableManager = models.Manager.from_queryset(ImmutableQuerySet)


class DocumentType(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="document_types",
        verbose_name="Организация",
    )
    code = models.SlugField("Код", max_length=64)
    name = models.CharField("Наименование", max_length=255)
    number_prefix = models.CharField("Префикс номера", max_length=24)
    number_width = models.PositiveSmallIntegerField("Разрядность номера", default=6)
    is_active = models.BooleanField("Действующий", default=True)
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("organization__name", "name")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_document_type_code_per_org",
            ),
            models.UniqueConstraint(
                fields=("organization", "number_prefix"),
                name="uniq_document_prefix_per_org",
            ),
            models.CheckConstraint(
                condition=Q(number_width__gte=3) & Q(number_width__lte=12),
                name="document_type_number_width_range",
            ),
        ]
        verbose_name = "тип документа"
        verbose_name_plural = "типы документов"

    def __str__(self) -> str:
        return f"{self.organization}: {self.name}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.code = self.code.strip().lower()
        self.number_prefix = self.number_prefix.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        self.code = self.code.strip().lower()
        self.number_prefix = self.number_prefix.strip().upper()
        if not self.number_prefix:
            raise ValidationError({"number_prefix": "Префикс номера обязателен."})


class DocumentNumberSequence(models.Model):
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="document_number_sequences",
        verbose_name="Организация",
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name="number_sequences",
        verbose_name="Тип документа",
    )
    year = models.PositiveSmallIntegerField("Год")
    last_value = models.PositiveIntegerField("Последнее значение", default=0)
    updated_at = models.DateTimeField("Изменён", auto_now=True)

    class Meta:
        ordering = ("organization__name", "document_type__name", "year")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "document_type", "year"),
                name="uniq_document_sequence_per_type_year",
            )
        ]
        verbose_name = "серверный нумератор"
        verbose_name_plural = "серверные нумераторы"

    def __str__(self) -> str:
        return f"{self.document_type} · {self.year}: {self.last_value}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if (
            self.document_type_id
            and self.organization_id
            and self.document_type.organization_id != self.organization_id
        ):
            raise ValidationError({"document_type": "Тип документа относится к другой организации."})


class Document(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        REGISTERED = "REGISTERED", "Зарегистрирован"

    public_id = models.UUIDField("Публичный идентификатор", default=uuid.uuid4, unique=True, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="Организация",
    )
    document_type = models.ForeignKey(
        DocumentType,
        on_delete=models.PROTECT,
        related_name="documents",
        verbose_name="Тип документа",
    )
    title = models.CharField("Заголовок", max_length=500)
    status = models.CharField(
        "Статус",
        max_length=24,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    current_version = models.ForeignKey(
        "DocumentVersion",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="+",
        verbose_name="Текущая версия",
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_documents",
        verbose_name="Автор черновика",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)
    updated_at = models.DateTimeField("Изменён", auto_now=True)
    registration_year = models.PositiveSmallIntegerField("Год регистрации", null=True, blank=True)
    sequence_number = models.PositiveIntegerField("Порядковый номер", null=True, blank=True)
    registration_number = models.CharField("Регистрационный номер", max_length=96, blank=True)
    registered_at = models.DateTimeField("Зарегистрирован", null=True, blank=True)
    registered_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registered_documents",
        verbose_name="Зарегистрировал",
    )

    objects = ImmutableManager()

    class Meta:
        ordering = ("-created_at", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "document_type", "registration_year", "sequence_number"),
                condition=Q(sequence_number__isnull=False),
                name="uniq_document_number_components",
            ),
            models.UniqueConstraint(
                fields=("organization", "registration_number"),
                condition=~Q(registration_number=""),
                name="uniq_document_registration_number",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="DRAFT",
                        registration_year__isnull=True,
                        sequence_number__isnull=True,
                        registration_number="",
                        registered_at__isnull=True,
                        registered_by__isnull=True,
                    )
                    | (
                        Q(
                            status="REGISTERED",
                            registration_year__isnull=False,
                            sequence_number__isnull=False,
                            registered_at__isnull=False,
                            registered_by__isnull=False,
                        )
                        & ~Q(registration_number="")
                    )
                ),
                name="document_registration_state_consistent",
            ),
        ]
        indexes = [
            models.Index(fields=("organization", "status", "created_at")),
            models.Index(fields=("registration_number",)),
        ]
        verbose_name = "документ"
        verbose_name_plural = "документы"

    def __str__(self) -> str:
        identity = self.registration_number or f"черновик {self.public_id}"
        return f"{identity}: {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == self.Status.REGISTERED:
                raise ValidationError("Зарегистрированный документ неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление документа запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.document_type_id and self.document_type.organization_id != self.organization_id:
            errors["document_type"] = "Тип документа относится к другой организации."
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            errors["created_by"] = "Автор относится к другой организации."
        if self.registered_by_id and self.registered_by.organization_id != self.organization_id:
            errors["registered_by"] = "Регистратор относится к другой организации."
        if self.current_version_id:
            if not self.pk:
                errors["current_version"] = "Текущую версию можно назначить только сохранённому документу."
            elif self.current_version.document_id != self.pk:
                errors["current_version"] = "Текущая версия относится к другому документу."
        if errors:
            raise ValidationError(errors)


class DocumentVersion(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Черновик"
        REGISTERED = "REGISTERED", "Зафиксирована при регистрации"

    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="versions",
        verbose_name="Документ",
    )
    version_number = models.PositiveIntegerField("Номер версии")
    status = models.CharField(
        "Статус",
        max_length=24,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
    )
    title = models.CharField("Заголовок", max_length=500)
    content = models.JSONField("Содержимое", default=dict)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_document_versions",
        verbose_name="Создал",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)
    registered_at = models.DateTimeField("Зафиксирована", null=True, blank=True)
    registered_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="registered_document_versions",
        verbose_name="Зафиксировал",
    )

    objects = ImmutableManager()

    class Meta:
        ordering = ("document", "version_number")
        constraints = [
            models.UniqueConstraint(
                fields=("document", "version_number"),
                name="uniq_document_version_number",
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        status="DRAFT",
                        registered_at__isnull=True,
                        registered_by__isnull=True,
                    )
                    | Q(
                        status="REGISTERED",
                        registered_at__isnull=False,
                        registered_by__isnull=False,
                    )
                ),
                name="document_version_registration_state_consistent",
            ),
        ]
        verbose_name = "версия документа"
        verbose_name_plural = "версии документов"

    def __str__(self) -> str:
        return f"{self.document} · версия {self.version_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            if original.status == self.Status.REGISTERED:
                raise ValidationError("Зарегистрированная версия неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление версии документа запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.document_id:
            organization_id = self.document.organization_id
            if self.created_by_id and self.created_by.organization_id != organization_id:
                errors["created_by"] = "Автор версии относится к другой организации."
            if self.registered_by_id and self.registered_by.organization_id != organization_id:
                errors["registered_by"] = "Регистратор относится к другой организации."
        if not isinstance(self.content, dict):
            errors["content"] = "Содержимое версии должно быть JSON-объектом."
        if errors:
            raise ValidationError(errors)



class SignedSnapshot(models.Model):
    class Purpose(models.TextChoices):
        REGISTRATION = "REGISTRATION", "Регистрация документа"

    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="signed_snapshots",
        verbose_name="Документ",
    )
    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.PROTECT,
        related_name="signed_snapshots",
        verbose_name="Версия документа",
    )
    purpose = models.CharField("Назначение", max_length=32, choices=Purpose.choices)
    schema_version = models.CharField(
        "Версия схемы снимка",
        max_length=64,
        default="eod.document.registration.v1",
        editable=False,
    )
    canonical_json = models.TextField("Каноническое JSON-представление", editable=False)
    hash_algorithm = models.CharField(
        "Алгоритм контрольной суммы",
        max_length=16,
        default="SHA-256",
        editable=False,
    )
    digest = models.CharField("SHA-256", max_length=64, db_index=True, editable=False)
    created_at = models.DateTimeField("Создан", default=timezone.now, editable=False)

    objects = ImmutableManager()

    class Meta:
        ordering = ("-created_at", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("document_version", "purpose"),
                name="uniq_signed_snapshot_per_version_purpose",
            )
        ]
        verbose_name = "подписываемый снимок"
        verbose_name_plural = "подписываемые снимки"

    def __str__(self) -> str:
        return f"{self.document} · {self.get_purpose_display()} · {self.digest[:12]}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Подписываемый снимок неизменяем.")
        self.digest = self.digest.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление подписываемого снимка запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.document_id and self.document_version_id:
            if self.document_version.document_id != self.document_id:
                errors["document_version"] = "Версия относится к другому документу."
        try:
            parsed = json.loads(self.canonical_json)
        except (TypeError, ValueError):
            errors["canonical_json"] = "Снимок должен содержать корректный JSON."
        else:
            if not isinstance(parsed, dict):
                errors["canonical_json"] = "Корневое значение снимка должно быть JSON-объектом."
        if self.hash_algorithm != "SHA-256":
            errors["hash_algorithm"] = "Поддерживается только SHA-256."
        if len(self.digest) != 64 or any(ch not in "0123456789abcdef" for ch in self.digest):
            errors["digest"] = "Контрольная сумма должна быть SHA-256 в нижнем hex-регистре."
        if errors:
            raise ValidationError(errors)


class DocumentSignature(models.Model):
    class ConfirmationMethod(models.TextChoices):
        PASSWORD_REAUTH = "PASSWORD_REAUTH", "Повторная аутентификация паролем"
        LEGACY_MIGRATION = "LEGACY_MIGRATION", "Перенос ранее зарегистрированного документа"
        DEMO_SEED = "DEMO_SEED", "Демонстрационное создание"

    snapshot = models.OneToOneField(
        SignedSnapshot,
        on_delete=models.PROTECT,
        related_name="signature",
        verbose_name="Подписываемый снимок",
    )
    purpose = models.CharField(
        "Назначение",
        max_length=32,
        choices=SignedSnapshot.Purpose.choices,
    )
    confirmation_method = models.CharField(
        "Способ подтверждения",
        max_length=32,
        choices=ConfirmationMethod.choices,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="document_signatures",
        verbose_name="Учётная запись",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="document_signatures",
        verbose_name="Сотрудник",
    )
    username_snapshot = models.CharField("Имя пользователя на момент подтверждения", max_length=150)
    full_name_snapshot = models.CharField("Ф.И.О. на момент подтверждения", max_length=500)
    position_snapshot = models.CharField("Должность на момент подтверждения", max_length=500, blank=True)
    division_snapshot = models.CharField("Подразделение на момент подтверждения", max_length=500, blank=True)
    workplace_snapshot = models.CharField("Рабочее место на момент подтверждения", max_length=500, blank=True)
    roles_snapshot = models.JSONField("Полномочия на момент подтверждения", default=list, blank=True)
    signed_at = models.DateTimeField("Серверное время подтверждения", default=timezone.now, editable=False)
    checksum_algorithm = models.CharField(
        "Алгоритм контрольной суммы записи",
        max_length=16,
        default="SHA-256",
        editable=False,
    )
    checksum = models.CharField("Контрольная сумма записи подписи", max_length=64, editable=False)

    objects = ImmutableManager()

    class Meta:
        ordering = ("-signed_at", "-pk")
        verbose_name = "системное подтверждение"
        verbose_name_plural = "системные подтверждения"

    def __str__(self) -> str:
        identity = self.full_name_snapshot or self.username_snapshot or "неизвестный подписант"
        return f"{identity} · {self.get_confirmation_method_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Запись системного подтверждения неизменяема.")
        self.checksum = self.checksum.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление системного подтверждения запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.snapshot_id and self.purpose != self.snapshot.purpose:
            errors["purpose"] = "Назначение подписи не совпадает с назначением снимка."
        if self.confirmation_method == self.ConfirmationMethod.PASSWORD_REAUTH:
            if not self.user_id:
                errors["user"] = "Для повторной аутентификации обязательна учётная запись."
            if not self.employee_id:
                errors["employee"] = "Для повторной аутентификации обязателен сотрудник."
        if not isinstance(self.roles_snapshot, list):
            errors["roles_snapshot"] = "Снимок полномочий должен быть JSON-массивом."
        if self.checksum_algorithm != "SHA-256":
            errors["checksum_algorithm"] = "Поддерживается только SHA-256."
        if len(self.checksum) != 64 or any(ch not in "0123456789abcdef" for ch in self.checksum):
            errors["checksum"] = "Контрольная сумма должна быть SHA-256 в нижнем hex-регистре."
        if errors:
            raise ValidationError(errors)

class DocumentLink(models.Model):
    class LinkType(models.TextChoices):
        RELATED = "RELATED", "Связанный документ"
        BASED_ON = "BASED_ON", "Создан на основании"
        CORRECTS = "CORRECTS", "Исправляет"
        SUPERSEDES = "SUPERSEDES", "Заменяет"

    source_document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="outgoing_links",
        verbose_name="Исходный документ",
    )
    target_document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        related_name="incoming_links",
        verbose_name="Связанный документ",
    )
    link_type = models.CharField("Тип связи", max_length=24, choices=LinkType.choices)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_document_links",
        verbose_name="Создал связь",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    objects = ImmutableManager()

    class Meta:
        ordering = ("source_document", "link_type", "created_at")
        constraints = [
            models.UniqueConstraint(
                fields=("source_document", "target_document", "link_type"),
                name="uniq_typed_document_link",
            ),
            models.CheckConstraint(
                condition=~Q(source_document=models.F("target_document")),
                name="document_link_not_self",
            ),
        ]
        verbose_name = "связь документов"
        verbose_name_plural = "связи документов"

    def __str__(self) -> str:
        return f"{self.source_document} → {self.target_document} ({self.get_link_type_display()})"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Существующая связь документов неизменяема.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление связи документов запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.source_document_id == self.target_document_id:
            errors["target_document"] = "Документ нельзя связать с самим собой."
        if self.source_document_id and self.target_document_id:
            if self.source_document.organization_id != self.target_document.organization_id:
                errors["target_document"] = "Связанные документы относятся к разным организациям."
            if self.created_by_id and self.created_by.organization_id != self.source_document.organization_id:
                errors["created_by"] = "Создатель связи относится к другой организации."
        if errors:
            raise ValidationError(errors)


class AuditEvent(models.Model):
    class EventType(models.TextChoices):
        DOCUMENT_CREATED = "DOCUMENT_CREATED", "Создан черновик"
        DRAFT_UPDATED = "DRAFT_UPDATED", "Черновик изменён"
        DOCUMENT_REGISTERED = "DOCUMENT_REGISTERED", "Документ зарегистрирован"
        DOCUMENT_SIGNATURE_CREATED = "DOCUMENT_SIGNATURE_CREATED", "Создано системное подтверждение"
        LEGACY_SIGNATURE_MIGRATED = "LEGACY_SIGNATURE_MIGRATED", "Создан признак перенесённого документа"
        DOCUMENT_LINK_CREATED = "DOCUMENT_LINK_CREATED", "Создана связь документов"

    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="document_audit_events",
        verbose_name="Организация",
    )
    event_type = models.CharField("Событие", max_length=40, choices=EventType.choices, db_index=True)
    occurred_at = models.DateTimeField("Серверное время", default=timezone.now, editable=False, db_index=True)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="document_audit_events",
        verbose_name="Учётная запись",
    )
    actor_employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="document_audit_events",
        verbose_name="Сотрудник",
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Документ",
    )
    document_version = models.ForeignKey(
        DocumentVersion,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="audit_events",
        verbose_name="Версия документа",
    )
    entity_type = models.CharField("Тип сущности", max_length=64)
    entity_id = models.CharField("Идентификатор сущности", max_length=64)
    payload = models.JSONField("Данные события", default=dict, blank=True)

    objects = ImmutableManager()

    class Meta:
        ordering = ("-occurred_at", "-pk")
        indexes = [
            models.Index(fields=("organization", "occurred_at")),
            models.Index(fields=("entity_type", "entity_id")),
        ]
        verbose_name = "событие аудита"
        verbose_name_plural = "события аудита"

    def __str__(self) -> str:
        return f"{self.get_event_type_display()} · {self.occurred_at:%d.%m.%Y %H:%M:%S}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Событие аудита неизменяемо.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление события аудита запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.actor_employee_id and self.actor_employee.organization_id != self.organization_id:
            errors["actor_employee"] = "Сотрудник относится к другой организации."
        if self.document_id and self.document.organization_id != self.organization_id:
            errors["document"] = "Документ относится к другой организации."
        if self.document_version_id:
            if not self.document_id:
                errors["document_version"] = "Для версии должен быть указан документ."
            elif self.document_version.document_id != self.document_id:
                errors["document_version"] = "Версия относится к другому документу."
        if not isinstance(self.payload, dict):
            errors["payload"] = "Данные события должны быть JSON-объектом."
        if errors:
            raise ValidationError(errors)
