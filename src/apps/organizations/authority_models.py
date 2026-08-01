from __future__ import annotations

import uuid
from collections.abc import Mapping
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.utils import timezone

from apps.normatives.evidence import sha256_digest

from .models import (
    Employee,
    EmployeeOperationalRight,
    OperationalRightDefinition,
    Organization,
    Substitution,
)


class AuthorityProtectedQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение authority snapshots запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление authority snapshots запрещено.")


AuthorityProtectedManager = models.Manager.from_queryset(AuthorityProtectedQuerySet)


class AuthorityScopeKind(models.TextChoices):
    ORGANIZATION = "ORGANIZATION", "Организация"
    DIVISION = "DIVISION", "Подразделение"
    WORKPLACE = "WORKPLACE", "Рабочее место"
    OPERATIONAL_AREA = "OPERATIONAL_AREA", "Оперативная область"
    ENERGY_SITE = "ENERGY_SITE", "Энергообъект"
    EQUIPMENT = "EQUIPMENT", "Оборудование"


class AuthorityBasisStatus(models.TextChoices):
    CONFIRMED = "CONFIRMED", "Основание подтверждено"
    VERIFY = "VERIFY", "Основание требует проверки"
    REJECTED = "REJECTED", "Основание отклонено"


class AuthorityDecision(models.TextChoices):
    ALLOW = "ALLOW", "Разрешено"
    DENY = "DENY", "Запрещено"
    VERIFY = "VERIFY", "Требуется проверка"


class ExternalPersonnelRelationKind(models.TextChoices):
    SECONDED = "SECONDED", "Командированный персонал"
    CONTRACTOR = "CONTRACTOR", "Подрядный персонал"
    SYSTEM_OPERATOR = "SYSTEM_OPERATOR", "Персонал системного оператора"


_FORBIDDEN_NORMALIZED_KEY_TOKENS = frozenset(
    {
        "password",
        "passwd",
        "passphrase",
        "secret",
        "token",
        "privatekey",
        "credential",
    }
)


def _normalize_code(value: str) -> str:
    return " ".join(value.split()).upper().replace(" ", "_")


def _normalize_codes(values: object, *, field_name: str) -> list[str]:
    if not isinstance(values, list):
        raise ValidationError({field_name: "Требуется JSON-массив кодов."})
    normalized = sorted(
        {
            _normalize_code(str(value))
            for value in values
            if str(value or "").strip()
        }
    )
    if not normalized:
        raise ValidationError({field_name: "Требуется хотя бы один код."})
    return normalized


def _normalized_key(value: object) -> str:
    return "".join(character for character in str(value).casefold() if character.isalnum())


def _assert_secret_free(value: Any, *, path: str = "snapshot") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalized_key(key)
            if any(token in normalized_key for token in _FORBIDDEN_NORMALIZED_KEY_TOKENS):
                raise ValidationError(
                    {"snapshot": f"Секретное поле запрещено: {path}.{key}."}
                )
            _assert_secret_free(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_secret_free(item, path=f"{path}[{index}]")


def _validate_datetime_window(start, end, *, field_name: str = "valid_until") -> None:
    if timezone.is_naive(start):
        raise ValidationError({"valid_from": "Время должно содержать часовой пояс."})
    if end is not None:
        if timezone.is_naive(end):
            raise ValidationError({field_name: "Время должно содержать часовой пояс."})
        if end < start:
            raise ValidationError({field_name: "Окончание периода раньше его начала."})


def _validate_scope(
    *,
    organization_id: int | None,
    scope_kind: str,
    scope_reference: str,
) -> None:
    if not scope_reference.strip():
        raise ValidationError({"scope_reference": "Структурированная область обязательна."})
    if (
        organization_id
        and scope_kind == AuthorityScopeKind.ORGANIZATION
        and scope_reference.strip() != str(organization_id)
    ):
        raise ValidationError(
            {"scope_reference": "Организационная область относится к другой организации."}
        )


class OperationalAuthorityGrant(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="authority_grants",
        verbose_name="Организация действия",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="structured_authority_grants",
        verbose_name="Лицо, которому предоставлено право",
    )
    right_definition = models.ForeignKey(
        OperationalRightDefinition,
        on_delete=models.PROTECT,
        related_name="structured_grants",
        verbose_name="Вид оперативного права",
    )
    action_code = models.CharField("Код контролируемого действия", max_length=128, db_index=True)
    scope_kind = models.CharField(
        "Вид области",
        max_length=24,
        choices=AuthorityScopeKind.choices,
    )
    scope_reference = models.CharField("Идентификатор области", max_length=255)
    scope_label = models.CharField("Наименование области", max_length=500, blank=True)
    granting_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="granted_operational_authorities",
        verbose_name="Организация, предоставившая право",
    )
    basis_status = models.CharField(
        "Статус основания",
        max_length=16,
        choices=AuthorityBasisStatus.choices,
        default=AuthorityBasisStatus.VERIFY,
    )
    basis_reference = models.CharField("Документ-основание и редакция", max_length=1000)
    source_ids = models.JSONField("Traceable source IDs", default=list)
    source_operational_right = models.ForeignKey(
        EmployeeOperationalRight,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="published_structured_grants",
        verbose_name="Исходный импортированный факт",
    )
    valid_from = models.DateTimeField("Действует с")
    valid_until = models.DateTimeField("Действует по", null=True, blank=True)
    is_active = models.BooleanField("Действующее предоставление", default=True)
    allow_substitution = models.BooleanField("Допускает явное замещение", default=False)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_authority_grants",
        verbose_name="Зафиксировал",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("employee__last_name", "action_code", "scope_kind", "scope_reference")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="authority_grant_valid_window",
            ),
            models.UniqueConstraint(
                fields=(
                    "employee",
                    "action_code",
                    "scope_kind",
                    "scope_reference",
                    "valid_from",
                    "basis_reference",
                ),
                name="uniq_authority_grant_start_basis",
            ),
        ]
        verbose_name = "структурированное оперативное право"
        verbose_name_plural = "структурированные оперативные права"

    def __str__(self) -> str:
        return f"{self.employee}: {self.action_code} · {self.scope_label or self.scope_reference}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.action_code = _normalize_code(self.action_code)
        self.scope_reference = self.scope_reference.strip()
        self.scope_label = " ".join(self.scope_label.split())
        self.basis_reference = self.basis_reference.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        _validate_datetime_window(self.valid_from, self.valid_until)
        _validate_scope(
            organization_id=self.organization_id,
            scope_kind=self.scope_kind,
            scope_reference=self.scope_reference,
        )
        self.source_ids = _normalize_codes(self.source_ids, field_name="source_ids")
        errors: dict[str, str] = {}
        if self.source_operational_right_id:
            source = self.source_operational_right
            if source.employee_id != self.employee_id:
                errors["source_operational_right"] = "Исходный факт относится к другому сотруднику."
            elif source.right_definition_id != self.right_definition_id:
                errors["source_operational_right"] = "Исходный факт относится к другому виду права."
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            errors["created_by"] = "Фиксирующий сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


class ExternalPersonnelEngagement(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="external_engagements",
        verbose_name="Внешний сотрудник",
    )
    home_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="outgoing_external_personnel",
        verbose_name="Направляющая организация",
    )
    host_organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="incoming_external_personnel",
        verbose_name="Принимающая организация",
    )
    relation_kind = models.CharField(
        "Вид внешнего персонала",
        max_length=24,
        choices=ExternalPersonnelRelationKind.choices,
    )
    scope_kind = models.CharField(
        "Вид области допуска",
        max_length=24,
        choices=AuthorityScopeKind.choices,
    )
    scope_reference = models.CharField("Идентификатор области допуска", max_length=255)
    scope_label = models.CharField("Наименование области допуска", max_length=500, blank=True)
    valid_from = models.DateTimeField("Допущен с")
    valid_until = models.DateTimeField("Допущен по", null=True, blank=True)
    basis_status = models.CharField(
        "Статус основания",
        max_length=16,
        choices=AuthorityBasisStatus.choices,
        default=AuthorityBasisStatus.VERIFY,
    )
    basis_reference = models.CharField("Основание внешнего допуска", max_length=1000)
    source_ids = models.JSONField("Traceable source IDs", default=list)
    is_active = models.BooleanField("Действующий внешний допуск", default=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_external_engagements",
        verbose_name="Зафиксировал",
    )
    created_at = models.DateTimeField("Создан", auto_now_add=True)

    class Meta:
        ordering = ("host_organization__name", "employee__last_name", "valid_from")
        constraints = [
            models.CheckConstraint(
                condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")),
                name="external_engagement_valid_window",
            ),
            models.CheckConstraint(
                condition=~Q(home_organization=F("host_organization")),
                name="external_engagement_distinct_orgs",
            ),
            models.UniqueConstraint(
                fields=(
                    "employee",
                    "host_organization",
                    "scope_kind",
                    "scope_reference",
                    "valid_from",
                ),
                name="uniq_external_engagement_start",
            ),
        ]
        verbose_name = "допуск внешнего персонала"
        verbose_name_plural = "допуски внешнего персонала"

    def __str__(self) -> str:
        return f"{self.employee} → {self.host_organization}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.scope_reference = self.scope_reference.strip()
        self.scope_label = " ".join(self.scope_label.split())
        self.basis_reference = self.basis_reference.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        _validate_datetime_window(self.valid_from, self.valid_until)
        _validate_scope(
            organization_id=self.host_organization_id,
            scope_kind=self.scope_kind,
            scope_reference=self.scope_reference,
        )
        self.source_ids = _normalize_codes(self.source_ids, field_name="source_ids")
        errors: dict[str, str] = {}
        if self.employee_id and self.employee.organization_id != self.home_organization_id:
            errors["home_organization"] = "Направляющая организация не совпадает с работодателем."
        if self.created_by_id and self.created_by.organization_id != self.host_organization_id:
            errors["created_by"] = "Фиксирующий сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


class OperationalAuthoritySubstitution(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    substitution = models.ForeignKey(
        Substitution,
        on_delete=models.PROTECT,
        related_name="authority_scopes",
        verbose_name="Базовое замещение",
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="authority_substitutions",
        verbose_name="Организация",
    )
    action_codes = models.JSONField("Явно разрешённые действия", default=list)
    scope_kind = models.CharField(
        "Вид области",
        max_length=24,
        choices=AuthorityScopeKind.choices,
    )
    scope_reference = models.CharField("Идентификатор области", max_length=255)
    scope_label = models.CharField("Наименование области", max_length=500, blank=True)
    basis_status = models.CharField(
        "Статус основания",
        max_length=16,
        choices=AuthorityBasisStatus.choices,
        default=AuthorityBasisStatus.VERIFY,
    )
    basis_reference = models.CharField("Документ-основание и редакция", max_length=1000)
    source_ids = models.JSONField("Traceable source IDs", default=list)
    is_active = models.BooleanField("Действующее ограничение замещения", default=True)
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="created_authority_substitutions",
        verbose_name="Зафиксировал",
    )
    created_at = models.DateTimeField("Создано", auto_now_add=True)

    class Meta:
        ordering = ("-substitution__valid_from", "substitution__substitute_employee__last_name")
        constraints = [
            models.UniqueConstraint(
                fields=("substitution", "scope_kind", "scope_reference"),
                name="uniq_authority_substitution_scope",
            )
        ]
        verbose_name = "область оперативных прав при замещении"
        verbose_name_plural = "области оперативных прав при замещении"

    def __str__(self) -> str:
        return f"{self.substitution}: {', '.join(self.action_codes)}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        self.scope_reference = self.scope_reference.strip()
        self.scope_label = " ".join(self.scope_label.split())
        self.basis_reference = self.basis_reference.strip()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        _validate_scope(
            organization_id=self.organization_id,
            scope_kind=self.scope_kind,
            scope_reference=self.scope_reference,
        )
        self.action_codes = _normalize_codes(self.action_codes, field_name="action_codes")
        self.source_ids = _normalize_codes(self.source_ids, field_name="source_ids")
        errors: dict[str, str] = {}
        if (
            self.substitution_id
            and self.substitution.replaced_employee.organization_id != self.organization_id
        ):
            errors["organization"] = "Замещение относится к другой организации."
        if self.created_by_id and self.created_by.organization_id != self.organization_id:
            errors["created_by"] = "Фиксирующий сотрудник относится к другой организации."
        if errors:
            raise ValidationError(errors)


class AuthorityEvaluationRecord(models.Model):
    SCHEMA_VERSION = "eod.personnel-authority.evaluation.v1"

    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="authority_evaluations",
        verbose_name="Организация действия",
    )
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="authority_evaluations",
        verbose_name="Проверяемое лицо",
    )
    action_code = models.CharField("Код действия", max_length=128, db_index=True)
    occurred_at = models.DateTimeField("Момент действия", db_index=True)
    scope_kind = models.CharField(
        "Вид области",
        max_length=24,
        choices=AuthorityScopeKind.choices,
    )
    scope_reference = models.CharField("Идентификатор области", max_length=255)
    scope_label = models.CharField("Наименование области", max_length=500, blank=True)
    subject_type = models.CharField("Тип предметного объекта", max_length=128)
    subject_id = models.CharField("Идентификатор предметного объекта", max_length=255)
    decision = models.CharField(
        "Результат",
        max_length=16,
        choices=AuthorityDecision.choices,
        db_index=True,
    )
    reasons = models.JSONField("Коды причин", default=list)
    matched_grant = models.ForeignKey(
        OperationalAuthorityGrant,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="evaluation_records",
        verbose_name="Использованное предоставление права",
    )
    snapshot = models.JSONField("Неизменяемый authority snapshot")
    digest = models.CharField("SHA-256 authority snapshot", max_length=64, unique=True, editable=False)
    previous_evaluation = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="corrections",
        verbose_name="Предыдущий результат",
    )
    recorded_by = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="recorded_authority_evaluations",
        verbose_name="Зафиксировал",
    )
    created_at = models.DateTimeField("Зафиксировано", auto_now_add=True)

    objects = AuthorityProtectedManager()

    class Meta:
        ordering = ("-occurred_at", "-id")
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "subject_type", "subject_id", "occurred_at", "digest"),
                name="uniq_authority_evaluation_fact",
            )
        ]
        verbose_name = "результат проверки оперативного полномочия"
        verbose_name_plural = "результаты проверки оперативных полномочий"

    def __str__(self) -> str:
        return f"{self.actor}: {self.action_code} → {self.decision}"

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError(
                "Authority evaluation неизменяема; создайте связанный новый результат."
            )
        self.action_code = _normalize_code(self.action_code)
        self.scope_reference = self.scope_reference.strip()
        self.scope_label = " ".join(self.scope_label.split())
        self.subject_type = _normalize_code(self.subject_type)
        self.subject_id = self.subject_id.strip()
        self.reasons = _normalize_codes(self.reasons, field_name="reasons")
        self.digest = sha256_digest(self.canonical_payload())
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление authority evaluation запрещено.")

    def clean(self) -> None:
        super().clean()
        if timezone.is_naive(self.occurred_at):
            raise ValidationError({"occurred_at": "Время должно содержать часовой пояс."})
        _validate_scope(
            organization_id=self.organization_id,
            scope_kind=self.scope_kind,
            scope_reference=self.scope_reference,
        )
        self.reasons = _normalize_codes(self.reasons, field_name="reasons")
        if not isinstance(self.snapshot, dict):
            raise ValidationError({"snapshot": "Authority snapshot должен быть JSON-объектом."})
        _assert_secret_free(self.snapshot)
        errors: dict[str, str] = {}
        if self.matched_grant_id and self.matched_grant.organization_id != self.organization_id:
            errors["matched_grant"] = "Предоставление права относится к другой организации."
        if self.recorded_by_id and self.recorded_by.organization_id != self.organization_id:
            errors["recorded_by"] = "Фиксирующий сотрудник относится к другой организации."
        if self.previous_evaluation_id:
            previous = self.previous_evaluation
            if previous.organization_id != self.organization_id:
                errors["previous_evaluation"] = "Предыдущий результат относится к другой организации."
            elif previous.subject_type != self.subject_type or previous.subject_id != self.subject_id:
                errors["previous_evaluation"] = "Предыдущий результат относится к другому объекту."
        expected_digest = sha256_digest(self.canonical_payload())
        if self.digest and self.digest != expected_digest:
            errors["digest"] = "Digest не соответствует canonical authority payload."
        if errors:
            raise ValidationError(errors)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": self.SCHEMA_VERSION,
            "decision": self.decision,
            "reasons": self.reasons,
            "matched_grant_id": (
                str(self.matched_grant.public_id) if self.matched_grant_id else ""
            ),
            "snapshot": self.snapshot,
        }
