from __future__ import annotations

from typing import Any

from django.db import models

from .models import EmployeeOperationalRight


class OperationalRightConditionDetail(models.Model):
    right = models.OneToOneField(
        EmployeeOperationalRight,
        on_delete=models.CASCADE,
        related_name="condition_detail",
        verbose_name="Предоставленное право",
    )
    marker = models.CharField("Индекс условия", max_length=16)
    title = models.CharField("Краткое наименование условия", max_length=500)
    description = models.TextField("Точное содержание условия")
    source_clause = models.CharField(
        "Пункт документа",
        max_length=255,
        blank=True,
    )
    source_reference = models.CharField(
        "Источник условия",
        max_length=1000,
    )
    is_resolved = models.BooleanField(
        "Условие расшифровано",
        default=True,
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)

    class Meta:
        ordering = ("marker", "right__right_definition__display_order")
        verbose_name = "условие предоставленного права"
        verbose_name_plural = "условия предоставленных прав"

    def __str__(self) -> str:
        return f"{self.right}: {self.marker} — {self.title}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.marker = " ".join(self.marker.split())
        self.title = " ".join(self.title.split())
        self.description = " ".join(self.description.split())
        self.source_clause = " ".join(self.source_clause.split())
        self.source_reference = self.source_reference.strip()
        self.full_clean()
        super().save(*args, **kwargs)
