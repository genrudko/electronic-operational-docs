from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.operational_documents.models import OperationalDocumentRecord

from .base import ProtectedManager
from .volume import EquipmentDefectVolume


DEFECT_DOCUMENT_TYPE_CODE = "journal-equipment-defects"


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
        blank=True,
        default="",
        editable=False,
        max_length=96,
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    objects = ProtectedManager()

    class Meta:
        ordering = ("record__sequence_year", "record__sequence_value")
        constraints = [
            models.UniqueConstraint(
                condition=~Q(presentation_key=""),
                fields=("presentation_key",),
                name="uniq_defect_presentation_key",
            )
        ]
        verbose_name = "предметный контекст дефекта"
        verbose_name_plural = "предметные контексты дефектов"

    def __str__(self) -> str:
        return self.record.registration_number

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Предметный контекст дефекта неизменяем.")
        self.presentation_key = self.presentation_key.strip()
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
