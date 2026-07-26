from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.operational_documents.models import (
    OperationalDocumentRecord,
    OperationalDocumentRecordRevision,
)
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee, Organization, Workplace


DEFECT_DOCUMENT_TYPE_CODE = "journal-equipment-defects"


class ProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение данных журнала дефектов запрещено.")

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление данных журнала дефектов запрещено.")


class ProtectedManager(models.Manager.from_queryset(ProtectedQuerySet)):
    pass


class EquipmentDefectVolume(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="equipment_defect_volumes",
        verbose_name="Организация",
    )
    workplace = models.ForeignKey(
        Workplace,
        on_delete=models.PROTECT,
        related_name="equipment_defect_volumes",
        verbose_name="Рабочее место",
    )
    sequence_number = models.PositiveIntegerField("Номер тома")
    organization_name_snapshot = models.CharField(
        "Наименование организации",
        max_length=500,
        editable=False,
    )
    workplace_name_snapshot = models.CharField(
        "Наименование ВЭС / ПС",
        max_length=500,
        editable=False,
    )
    division_name_snapshot = models.CharField(
        "Наименование ЦОТУиЭ ВЭС",
        max_length=500,
        blank=True,
        editable=False,
    )
    started_on = models.DateField("Дата начала")
    closed_on = models.DateField("Дата окончания", null=True, blank=True)
    accepts_new_records = models.BooleanField("Принимает новые записи", default=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_equipment_defect_volumes",
        verbose_name="Создал том",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("organization", "workplace", "-sequence_number")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "workplace", "sequence_number"),
                name="uniq_defect_volume_number",
            ),
            models.UniqueConstraint(
                fields=("organization", "workplace"),
                condition=Q(accepts_new_records=True),
                name="uniq_open_defect_volume",
            ),
            models.CheckConstraint(
                condition=Q(sequence_number__gte=1),
                name="defect_volume_number_positive",
            ),
            models.CheckConstraint(
                condition=Q(closed_on__isnull=True) | Q(closed_on__gte=models.F("started_on")),
                name="defect_volume_dates_valid",
            ),
        ]
        verbose_name = "том журнала дефектов"
        verbose_name_plural = "тома журнала дефектов"

    def __str__(self) -> str:
        return f"{self.workplace_name_snapshot} · том {self.sequence_number}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            original = type(self).objects.get(pk=self.pk)
            protected = (
                "public_id",
                "organization_id",
                "workplace_id",
                "sequence_number",
                "organization_name_snapshot",
                "workplace_name_snapshot",
                "division_name_snapshot",
                "started_on",
                "created_by_id",
                "created_at",
            )
            if any(getattr(original, field) != getattr(self, field) for field in protected):
                raise ValidationError("Идентификационные реквизиты тома неизменяемы.")
            if original.closed_on is not None and (
                self.closed_on != original.closed_on
                or self.accepts_new_records != original.accepts_new_records
            ):
                raise ValidationError("Закрытый том журнала неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление тома журнала запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.workplace_id and self.workplace.organization_id != self.organization_id:
            errors["workplace"] = "Рабочее место относится к другой организации."
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            errors["created_by"] = "Создатель тома относится к другой организации."
        if self.closed_on is not None and self.accepts_new_records:
            errors["accepts_new_records"] = "Закрытый том не может принимать новые записи."
        if errors:
            raise ValidationError(errors)


class EquipmentDefectContext(models.Model):
    record = models.OneToOneField(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="equipment_defect_context",
        verbose_name="Запись журнала дефектов",
    )
    volume = models.ForeignKey(
        EquipmentDefectVolume,
        on_delete=models.PROTECT,
        related_name="defect_contexts",
        verbose_name="Исходный том",
    )
    presentation_key = models.CharField(
        "Ключ презентационных данных",
        max_length=96,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("record__sequence_year", "record__sequence_value")
        verbose_name = "предметный контекст дефекта"
        verbose_name_plural = "предметные контексты дефектов"

    def __str__(self) -> str:
        return self.record.registration_number

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Предметный контекст дефекта неизменяем.")
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление контекста дефекта запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.record_id:
            if self.record.document_type.code != DEFECT_DOCUMENT_TYPE_CODE:
                errors["record"] = "Запись не относится к журналу дефектов оборудования."
            if self.volume_id and self.record.organization_id != self.volume.organization_id:
                errors["volume"] = "Том и запись относятся к разным организациям."
            if self.volume_id and self.record.workplace_id != self.volume.workplace_id:
                errors["volume"] = "Том и запись относятся к разным рабочим местам."
        if errors:
            raise ValidationError(errors)


class DefectActionCode(models.TextChoices):
    REGISTERED = "REGISTERED", "Дефект зарегистрирован"
    DEADLINE_CONFIRMED = "DEADLINE_CONFIRMED", "Срок подтверждён"
    DEADLINE_EXTENDED = "DEADLINE_EXTENDED", "Срок устранения продлен"
    RESOLUTION_CONFIRMED = "RESOLUTION_CONFIRMED", "Устранение подтверждено"
    ACKNOWLEDGED = "ACKNOWLEDGED", "Оперативный персонал ознакомлен"
    CLOSED = "CLOSED", "Дефект закрыт"


class EquipmentDefectActionEvidence(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="equipment_defect_actions",
        verbose_name="Запись журнала дефектов",
    )
    action_code = models.CharField(
        "Действие",
        max_length=32,
        choices=DefectActionCode.choices,
        db_index=True,
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="equipment_defect_actions",
        verbose_name="Сотрудник",
    )
    actor_full_name_snapshot = models.CharField("Ф.И.О.", max_length=500, editable=False)
    actor_position_snapshot = models.CharField("Должность", max_length=500, editable=False)
    actor_division_snapshot = models.CharField("Подразделение", max_length=500, editable=False)
    occurred_at = models.DateTimeField("Время действия", auto_now_add=True, db_index=True)
    record_version = models.PositiveBigIntegerField("Версия записи")
    record_revision = models.ForeignKey(
        OperationalDocumentRecordRevision,
        on_delete=models.PROTECT,
        related_name="equipment_defect_actions",
        verbose_name="Редакция записи",
    )
    previous_deadline = models.DateTimeField("Прежний срок", null=True, blank=True)
    new_deadline = models.DateTimeField("Новый срок", null=True, blank=True)
    result = models.CharField("Результат", max_length=64, default="CONFIRMED")
    comment = models.TextField("Причина или комментарий", blank=True)
    canonical_snapshot = models.JSONField("Канонический снимок")
    sha256 = models.CharField("SHA-256", max_length=64, editable=False)

    objects = ProtectedManager()

    class Meta:
        ordering = ("occurred_at", "pk")
        indexes = [
            models.Index(
                fields=("record", "action_code", "occurred_at"),
                name="defect_action_lookup_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(record_version__gte=1),
                name="defect_action_version_positive",
            )
        ]
        verbose_name = "подтверждение действия по дефекту"
        verbose_name_plural = "подтверждения действий по дефектам"

    def __str__(self) -> str:
        return f"{self.record.registration_number} · {self.get_action_code_display()}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Подтверждение действия неизменяемо.")
        self.comment = self.comment.strip()
        self.result = self.result.strip().upper()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление подтверждения действия запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.record_id:
            if self.record.document_type.code != DEFECT_DOCUMENT_TYPE_CODE:
                errors["record"] = "Запись не относится к журналу дефектов оборудования."
            if self.actor_id and self.actor.organization_id != self.record.organization_id:
                errors["actor"] = "Сотрудник относится к другой организации."
            if self.record_revision_id and self.record_revision.record_id != self.record_id:
                errors["record_revision"] = "Редакция относится к другой записи."
        if self.record_revision_id and self.record_revision.revision_number != self.record_version:
            errors["record_version"] = "Номер версии не соответствует зафиксированной редакции."
        if len(self.sha256) != 64:
            errors["sha256"] = "Требуется SHA-256 подтверждения действия."
        if self.action_code == DefectActionCode.DEADLINE_EXTENDED:
            if self.previous_deadline is None or self.new_deadline is None:
                errors["new_deadline"] = "Продление должно сохранять прежний и новый срок."
            elif self.new_deadline <= self.previous_deadline:
                errors["new_deadline"] = "Новый срок должен быть позже прежнего."
            if not self.comment:
                errors["comment"] = "Для продления требуется причина или комментарий."
        if errors:
            raise ValidationError(errors)


class EquipmentDefectOperationalLogLink(models.Model):
    record = models.OneToOneField(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="equipment_defect_operational_log_link",
        verbose_name="Дефект",
    )
    operational_log_entry = models.ForeignKey(
        OperationalLogEntry,
        on_delete=models.PROTECT,
        related_name="equipment_defect_links",
        verbose_name="Запись оперативного журнала",
    )
    entry_sequence_snapshot = models.PositiveBigIntegerField("Номер исходной записи")
    entry_event_at_snapshot = models.DateTimeField("Время исходного события")
    entry_content_snapshot = models.TextField("Краткое содержание исходной записи")
    entry_digest_snapshot = models.CharField("SHA-256 исходной записи", max_length=64)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="created_equipment_defect_operational_log_links",
        verbose_name="Создал связь",
    )
    created_at = models.DateTimeField("Создана", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("operational_log_entry__journal", "entry_sequence_snapshot")
        verbose_name = "связь дефекта с оперативным журналом"
        verbose_name_plural = "связи дефектов с оперативным журналом"

    def __str__(self) -> str:
        return f"{self.record.registration_number} ← запись № {self.entry_sequence_snapshot}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Снимок связи с оперативным журналом неизменяем.")
        self.entry_content_snapshot = self.entry_content_snapshot.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление связи с оперативным журналом запрещено.")

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        if self.record_id and self.record.document_type.code != DEFECT_DOCUMENT_TYPE_CODE:
            errors["record"] = "Запись не относится к журналу дефектов оборудования."
        if self.record_id and self.operational_log_entry_id:
            if self.record.organization_id != self.operational_log_entry.journal.organization_id:
                errors["operational_log_entry"] = "Записи относятся к разным организациям."
        if self.record_id and self.created_by_id:
            if self.record.organization_id != self.created_by.organization_id:
                errors["created_by"] = "Создатель связи относится к другой организации."
        if len(self.entry_digest_snapshot) != 64:
            errors["entry_digest_snapshot"] = "Требуется SHA-256 исходной записи."
        if errors:
            raise ValidationError(errors)
