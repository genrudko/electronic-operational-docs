from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import models

from apps.operational_documents.models import OperationalDocumentRecord
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee

from .base import ProtectedManager
from .context import DEFECT_DOCUMENT_TYPE_CODE


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
