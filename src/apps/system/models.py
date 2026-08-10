from __future__ import annotations

import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models


class ModuleScopeType(models.TextChoices):
    ORGANIZATION = "ORGANIZATION", "Организация"
    ENERGY_SITE = "ENERGY_SITE", "Энергообъект"
    WORKPLACE = "WORKPLACE", "Рабочее место"


class ModuleLifecycleState(models.TextChoices):
    AVAILABLE = "AVAILABLE", "Доступен"
    CONFIGURED = "CONFIGURED", "Настроен"
    ACTIVE = "ACTIVE", "Активен"
    READ_ONLY = "READ_ONLY", "Только чтение"
    INACTIVE = "INACTIVE", "Неактивен"
    RETIRED = "RETIRED", "Выведен"


class _ProtectedRegistryQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        del kwargs
        raise ValidationError(
            "Массовое изменение состояния модулей запрещено; используйте lifecycle service."
        )

    def bulk_create(self, objs: Any, *args: Any, **kwargs: Any) -> list[Any]:
        del objs, args, kwargs
        raise ValidationError(
            "Массовое создание правил активации запрещено; используйте lifecycle service."
        )

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError(
            "Физическое удаление состояния модулей запрещено; история должна сохраняться."
        )


ProtectedRegistryManager = models.Manager.from_queryset(_ProtectedRegistryQuerySet)


class ModuleActivationRule(models.Model):
    """One explicit activation-state rule for one stable module and one scope."""

    module_id = models.CharField("Стабильный идентификатор модуля", max_length=64)
    scope_type = models.CharField(
        "Тип области",
        max_length=24,
        choices=ModuleScopeType.choices,
    )
    scope_id = models.PositiveBigIntegerField("Идентификатор области")
    organization_id = models.PositiveBigIntegerField("Идентификатор организации")
    state = models.CharField(
        "Явное состояние",
        max_length=24,
        choices=ModuleLifecycleState.choices,
        default=ModuleLifecycleState.CONFIGURED,
    )
    configuration_ready = models.BooleanField(
        "Конфигурация проверена",
        default=False,
    )
    configuration = models.JSONField("Конфигурация", default=dict, blank=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True)
    updated_at = models.DateTimeField("Изменено", auto_now=True)

    objects = ProtectedRegistryManager()

    class Meta:
        ordering = ("module_id", "organization_id", "scope_type", "scope_id")
        constraints = [
            models.UniqueConstraint(
                fields=("module_id", "scope_type", "scope_id"),
                name="uniq_module_activation_exact_scope",
            ),
        ]
        indexes = [
            models.Index(
                fields=("organization_id", "module_id", "scope_type", "scope_id"),
                name="system_modact_lookup_idx",
            ),
        ]
        verbose_name = "правило активации модуля"
        verbose_name_plural = "правила активации модулей"

    def __str__(self) -> str:
        return f"{self.module_id}:{self.scope_type}:{self.scope_id}={self.state}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        del args, kwargs
        raise ValidationError(
            "Прямое изменение правила активации запрещено; используйте lifecycle service."
        )

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        del args, kwargs
        raise ValidationError(
            "Физическое удаление правила активации запрещено; используйте lifecycle state."
        )

    def clean(self) -> None:
        super().clean()
        from apps.equipment.models import EnergySite
        from apps.organizations.models import Organization, Workplace

        from .module_registry import manifest_for

        errors: dict[str, str] = {}
        try:
            manifest = manifest_for(self.module_id)
        except KeyError:
            errors["module_id"] = "Неизвестный идентификатор модуля."
        else:
            self.module_id = manifest.module_id
            if self.scope_type not in manifest.supported_scopes:
                errors["scope_type"] = "Модуль не поддерживает указанную область активации."

        if not Organization.objects.filter(pk=self.organization_id).exists():
            errors["organization_id"] = "Организация не существует."
        elif self.scope_type == ModuleScopeType.ORGANIZATION:
            if self.scope_id != self.organization_id:
                errors["scope_id"] = "Для ORGANIZATION scope_id должен совпадать с organization_id."
        elif self.scope_type == ModuleScopeType.ENERGY_SITE:
            if not EnergySite.objects.filter(
                pk=self.scope_id,
                organization_id=self.organization_id,
            ).exists():
                errors["scope_id"] = "Энергообъект не относится к указанной организации."
        elif self.scope_type == ModuleScopeType.WORKPLACE:
            if not Workplace.objects.filter(
                pk=self.scope_id,
                organization_id=self.organization_id,
            ).exists():
                errors["scope_id"] = "Рабочее место не относится к указанной организации."
        else:
            errors["scope_type"] = "Неподдерживаемый тип области активации."

        if not isinstance(self.configuration, dict):
            errors["configuration"] = "Конфигурация модуля должна быть JSON-объектом."
        if errors:
            raise ValidationError(errors)


class _AppendOnlyAuditQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        del kwargs
        raise ValidationError("События аудита активации неизменяемы.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("События аудита активации не удаляются.")


AppendOnlyAuditManager = models.Manager.from_queryset(_AppendOnlyAuditQuerySet)


class ModuleActivationAuditEvent(models.Model):
    class Result(models.TextChoices):
        ALLOWED = "ALLOWED", "Разрешено"
        DENIED = "DENIED", "Отклонено"

    module_id = models.CharField("Стабильный идентификатор модуля", max_length=64)
    scope_type = models.CharField(
        "Тип области",
        max_length=24,
        choices=ModuleScopeType.choices,
    )
    scope_id = models.PositiveBigIntegerField("Идентификатор области")
    organization_id = models.PositiveBigIntegerField("Идентификатор организации")
    previous_explicit_state = models.CharField(
        "Предыдущее явное состояние",
        max_length=24,
        blank=True,
    )
    previous_effective_state = models.CharField(
        "Предыдущее эффективное состояние",
        max_length=24,
    )
    requested_new_state = models.CharField("Запрошенное состояние", max_length=24)
    resulting_effective_state = models.CharField(
        "Результирующее эффективное состояние",
        max_length=24,
    )
    actor_identity = models.CharField("Идентификатор инициатора", max_length=255)
    occurred_at = models.DateTimeField("Время события", auto_now_add=True)
    reason = models.CharField("Причина", max_length=1000)
    configuration_validation = models.CharField(
        "Проверка конфигурации",
        max_length=255,
    )
    dependency_validation = models.CharField(
        "Проверка зависимостей",
        max_length=1000,
    )
    result = models.CharField(
        "Результат",
        max_length=16,
        choices=Result.choices,
    )
    denial_reason_code = models.CharField("Код отказа", max_length=128, blank=True)
    correlation_id = models.UUIDField(
        "Корреляционный идентификатор",
        default=uuid.uuid4,
        editable=False,
    )
    manifest_contract_version = models.CharField(
        "Версия manifest contract",
        max_length=32,
    )

    objects = AppendOnlyAuditManager()

    class Meta:
        ordering = ("occurred_at", "pk")
        indexes = [
            models.Index(
                fields=(
                    "module_id",
                    "organization_id",
                    "scope_type",
                    "scope_id",
                    "occurred_at",
                ),
                name="system_modaudit_lookup_idx",
            ),
        ]
        verbose_name = "событие аудита активации модуля"
        verbose_name_plural = "события аудита активации модулей"

    def __str__(self) -> str:
        return (
            f"{self.module_id}:{self.scope_type}:{self.scope_id} "
            f"{self.requested_new_state}={self.result}"
        )

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk is not None:
            raise ValidationError("События аудита активации неизменяемы.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        del args, kwargs
        raise ValidationError("События аудита активации не удаляются.")
