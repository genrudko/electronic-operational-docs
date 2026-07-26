from __future__ import annotations

from typing import Any

from django.core.exceptions import ValidationError
from django.db import models


class ProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение данных журнала дефектов запрещено.")

    def delete(self, *args: Any, **kwargs: Any):
        raise ValidationError("Физическое удаление данных журнала дефектов запрещено.")


class ProtectedManager(models.Manager.from_queryset(ProtectedQuerySet)):
    pass
