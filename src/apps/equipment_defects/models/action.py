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
from apps.organizations.models import Employee

from .base import ProtectedManager
from .context import DEFECT_DOCUMENT_TYPE_CODE


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
        editable=False,
        unique=True,
    )
    record = models.ForeignKey(
        OperationalDocumentRecord,
        on_delete=models.PROTECT,
        related_name="equipment_defect_actions",
        verbose_name="Запись журнала дефектов",
    )
    action_code = models.CharField(
        "Действие",
        choices=DefectActionCode.choices,
        db_index=True,
        max_length=32,
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="equipment_defect_actions",
        verbose_name="Сотрудник",
    )
    actor_full_name_snapshot = models.CharField("Ф.И.О.", editable=False, max_length=500)
    actor_position_snapshot = models.CharField("Должность", editable=False, max_length=500)
    actor_division_snapshot = models.CharField("Подразделение", editable=False, max_length=500)
    occurred_at = models.DateTimeField("Время действия", auto_now_add=True, db_index=True)
    record_version = models.PositiveBigIntegerField("Версия записи")
    record_revision = models.ForeignKey(
        OperationalDocumentRecordRevision,
        on_delete=models.PROTECT,
        related_name="equipment_defect_actions",
        verbose_name="Редакция записи",
    )
    previous_deadline = models.DateTimeField("Прежний срок", blank=True, null=True)
    new_deadline = models.DateTimeField("Новый срок", blank=True, null=True)
    result = models.CharField("Результат", default="CONFIRMED", max_length=64)
    comment = models.TextField("Причина или комментарий", blank=True)
    canonical_snapshot = models.JSONField("Канонический снимок")
    sha256 = models.CharField("SHA-256", editable=False, max_length=64)

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
