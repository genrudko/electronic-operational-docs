from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from apps.organizations.models import Employee, Organization, Workplace

from .base import ProtectedManager


class EquipmentDefectVolume(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        editable=False,
        unique=True,
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
        editable=False,
        max_length=500,
    )
    workplace_name_snapshot = models.CharField(
        "Наименование ВЭС / ПС",
        editable=False,
        max_length=500,
    )
    division_name_snapshot = models.CharField(
        "Наименование ЦОТУиЭ ВЭС",
        blank=True,
        editable=False,
        max_length=500,
    )
    started_on = models.DateField("Дата начала")
    closed_on = models.DateField("Дата окончания", blank=True, null=True)
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
                condition=Q(accepts_new_records=True),
                fields=("organization", "workplace"),
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
