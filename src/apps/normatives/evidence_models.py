# ruff: noqa: DJ012
from __future__ import annotations

import hashlib
import json
import uuid
from typing import Any

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils import timezone

from apps.organizations.models import Employee, Organization

from .evidence import (
    EvidenceConfirmationMethod,
    EvidenceEventContract,
    EvidenceEventType,
    LegalModeDecisionContract,
    LocalActStatus,
    NormativeEvidenceStatus,
    ProductTargetMode,
    ProvenLegalMode,
    canonical_json,
)
from .models import NormativeRevision, PublicationStatus

_ENUM_LABELS: dict[str, str] = {
    "ELECTRONIC_ORIGINAL_TARGET": "Электронный оригинал — целевой режим",
    "ELECTRONIC_ORIGINAL": "Электронный оригинал доказан",
    "HYBRID": "Гибридный режим",
    "PAPER_MIRROR": "Бумажный оригинал с электронной копией",
    "EVIDENCE_EVENT": "Отдельное evidence-событие",
    "REFERENCE_ONLY": "Только справочное использование",
    "POST_DEMO": "После демонстрационного этапа",
    "VERIFY": "Требует проверки",
    "CONFIRMED": "Подтверждено",
    "PARTIAL": "Подтверждено частично",
    "NOT_APPLICABLE": "Не применяется",
    "NOT_REQUIRED": "Не требуется",
    "SIGNATURE": "Подпись / системное подтверждение",
    "ACKNOWLEDGEMENT": "Ознакомление",
    "INSTRUCTION": "Инструктаж",
    "KNOWLEDGE_CHECK": "Проверка знаний",
    "ACTION_CONFIRMATION": "Подтверждение действия",
    "PASSWORD_REAUTH": "Повторная аутентификация паролем",
    "SESSION_AUTH": "Действующая персональная сессия",
    "LEGACY_MIGRATION": "Перенос ранее созданного подтверждения",
    "DEMO_SEED": "Демонстрационное создание",
}


def _choices(enum_type: type[Any]) -> tuple[tuple[str, str], ...]:
    return tuple((item.value, _ENUM_LABELS[item.value]) for item in enum_type)


def _valid_sha256(value: str) -> bool:
    return len(value) == 64 and all(character in "0123456789abcdef" for character in value)


def _parsed_object(value: str, *, field_name: str) -> dict[str, Any]:
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError) as error:
        raise ValidationError({field_name: "Значение должно содержать корректный JSON."}) from error
    if not isinstance(parsed, dict):
        raise ValidationError({field_name: "Корневое значение должно быть JSON-объектом."})
    return parsed


def revision_evidence_code(revision: NormativeRevision | None) -> str:
    if revision is None:
        return ""
    digest = revision.digest.strip().lower()
    return f"{revision.document.code.upper()}:R{revision.revision_number}:{digest}"


def employee_evidence_snapshot(employee: Employee) -> dict[str, Any]:
    username = ""
    if employee.user_id:
        username = employee.user.get_username()
    return {
        "employee_id": employee.pk,
        "username": username,
        "full_name": employee.full_name,
        "position": employee.position.name if employee.position_id else "",
        "division": employee.division.name if employee.division_id else "",
        "workplace": employee.workplace.name if employee.workplace_id else "",
    }


class AppendOnlyQuerySet(models.QuerySet):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Массовое изменение evidence-записей запрещено.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление evidence-записей запрещено.")


AppendOnlyManager = models.Manager.from_queryset(AppendOnlyQuerySet)


class LegalModeDecision(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="legal_mode_decisions",
        verbose_name="Организация",
    )
    code = models.CharField("Код решения", max_length=128, db_index=True)
    module_id = models.CharField("Код модуля", max_length=128, db_index=True)
    subject_label = models.CharField("Предмет решения", max_length=500)
    product_target_mode = models.CharField(
        "Целевой продуктовый режим",
        max_length=40,
        choices=_choices(ProductTargetMode),
    )
    proven_legal_mode = models.CharField(
        "Доказанный правовой режим",
        max_length=32,
        choices=_choices(ProvenLegalMode),
        default=ProvenLegalMode.VERIFY.value,
        db_index=True,
    )
    normative_evidence_status = models.CharField(
        "Статус нормативного evidence",
        max_length=24,
        choices=_choices(NormativeEvidenceStatus),
        default=NormativeEvidenceStatus.VERIFY.value,
    )
    local_act_status = models.CharField(
        "Статус локального акта",
        max_length=24,
        choices=_choices(LocalActStatus),
        default=LocalActStatus.VERIFY.value,
    )
    normative_basis_revision = models.ForeignKey(
        NormativeRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="legal_mode_basis_decisions",
        verbose_name="Нормативная редакция-основание",
    )
    normative_basis_code = models.CharField(
        "Снимок кода нормативного основания",
        max_length=256,
        blank=True,
        editable=False,
    )
    local_act_revision = models.ForeignKey(
        NormativeRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="local_act_legal_mode_decisions",
        verbose_name="Редакция локального акта",
    )
    local_act_revision_code = models.CharField(
        "Снимок кода локального акта",
        max_length=256,
        blank=True,
        editable=False,
    )
    source_ids = models.JSONField("Traceable source IDs", default=list)
    decision_basis = models.TextField("Основание решения", blank=True)
    decision_maker = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="legal_mode_decisions",
        verbose_name="Зафиксировал решение",
    )
    decision_maker_snapshot = models.JSONField("Снимок автора решения", default=dict)
    decided_at = models.DateTimeField(
        "Серверное время решения",
        default=timezone.now,
        editable=False,
        db_index=True,
    )
    supersedes = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="superseded_by",
        verbose_name="Заменяет решение",
    )
    schema_version = models.CharField(
        "Версия схемы",
        max_length=64,
        default="eod.normative.legal-mode-decision-record.v1",
        editable=False,
    )
    canonical_json = models.TextField("Канонический снимок решения", editable=False)
    hash_algorithm = models.CharField(
        "Алгоритм контроля целостности",
        max_length=16,
        default="SHA-256",
        editable=False,
    )
    digest = models.CharField("SHA-256 решения", max_length=64, editable=False, db_index=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True, editable=False)

    objects = AppendOnlyManager()

    class Meta:
        ordering = ("code", "-decided_at", "-pk")
        indexes = [
            models.Index(fields=("organization", "code", "-decided_at"), name="norm_legal_org_code_idx"),
            models.Index(fields=("module_id", "proven_legal_mode"), name="norm_legal_module_idx"),
        ]
        verbose_name = "решение о правовом режиме"
        verbose_name_plural = "решения о правовых режимах"

    def __str__(self) -> str:
        return f"{self.code} · {self.proven_legal_mode} · {self.decided_at:%d.%m.%Y %H:%M}"

    def _contract(self) -> LegalModeDecisionContract:
        return LegalModeDecisionContract(
            code=self.code,
            module_id=self.module_id,
            subject_label=self.subject_label,
            product_target_mode=ProductTargetMode(self.product_target_mode),
            source_ids=tuple(self.source_ids or ()),
            proven_legal_mode=ProvenLegalMode(self.proven_legal_mode),
            normative_evidence_status=NormativeEvidenceStatus(self.normative_evidence_status),
            local_act_status=LocalActStatus(self.local_act_status),
            basis_revision_code=self.normative_basis_code,
            decision_basis=self.decision_basis,
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema_version,
            "public_id": str(self.public_id),
            "organization_id": self.organization_id,
            "decision": self._contract().canonical_payload(),
            "normative_basis": {
                "revision_id": self.normative_basis_revision_id,
                "revision_code": self.normative_basis_code,
            },
            "local_act_basis": {
                "revision_id": self.local_act_revision_id,
                "revision_code": self.local_act_revision_code,
            },
            "decision_maker_id": self.decision_maker_id,
            "decision_maker_snapshot": self.decision_maker_snapshot,
            "decided_at": self.decided_at,
            "supersedes_public_id": (
                str(self.supersedes.public_id) if self.supersedes_id else ""
            ),
        }

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        try:
            self._contract()
        except ValidationError as error:
            if hasattr(error, "message_dict"):
                errors.update(error.message_dict)
            else:
                errors["decision_basis"] = "; ".join(error.messages)

        if not isinstance(self.source_ids, list):
            errors["source_ids"] = "Source IDs должны храниться JSON-массивом."
        if not isinstance(self.decision_maker_snapshot, dict):
            errors["decision_maker_snapshot"] = "Снимок автора должен быть JSON-объектом."
        elif (
            self.decision_maker_id
            and self.decision_maker_snapshot.get("employee_id") != self.decision_maker_id
        ):
            errors["decision_maker_snapshot"] = "Снимок автора относится к другому сотруднику."
        if self.organization_id and self.decision_maker_id:
            if self.decision_maker.organization_id != self.organization_id:
                errors["decision_maker"] = "Автор решения относится к другой организации."

        for field_name, revision in (
            ("normative_basis_revision", self.normative_basis_revision),
            ("local_act_revision", self.local_act_revision),
        ):
            if revision is not None:
                if revision.status != PublicationStatus.PUBLISHED or not _valid_sha256(revision.digest):
                    errors[field_name] = "Основанием может быть только опубликованная редакция с SHA-256."

        if self.normative_basis_revision_id:
            if (
                self.normative_basis_revision.document.scope
                == self.normative_basis_revision.document.Scope.LOCAL
            ):
                errors["normative_basis_revision"] = (
                    "Локальный акт нельзя подменять нормативной редакцией-основанием."
                )
            if self.normative_basis_code != revision_evidence_code(self.normative_basis_revision):
                errors["normative_basis_code"] = "Снимок нормативного основания не совпадает с редакцией."
        elif self.normative_basis_code:
            errors["normative_basis_code"] = "Код основания нельзя хранить без связанной редакции."

        if self.local_act_revision_id:
            local_document = self.local_act_revision.document
            if local_document.scope != local_document.Scope.LOCAL:
                errors["local_act_revision"] = "В этом поле допустим только локальный документ организации."
            if self.organization_id != local_document.organization_id:
                errors["local_act_revision"] = "Локальный акт относится к другой организации."
            if self.local_act_revision_code != revision_evidence_code(self.local_act_revision):
                errors["local_act_revision_code"] = "Снимок локального акта не совпадает с редакцией."
        elif self.local_act_revision_code:
            errors["local_act_revision_code"] = "Код локального акта нельзя хранить без редакции."

        if (
            self.normative_evidence_status == NormativeEvidenceStatus.CONFIRMED.value
            and not self.normative_basis_revision_id
        ):
            errors["normative_basis_revision"] = (
                "Статус CONFIRMED требует опубликованной нормативной редакции."
            )
        if self.local_act_status == LocalActStatus.CONFIRMED.value and not self.local_act_revision_id:
            errors["local_act_revision"] = (
                "Статус CONFIRMED требует опубликованной редакции локального акта."
            )
        if self.local_act_status == LocalActStatus.NOT_REQUIRED.value and self.local_act_revision_id:
            errors["local_act_revision"] = "При NOT_REQUIRED локальный акт не связывается с решением."
        if self.proven_legal_mode != ProvenLegalMode.VERIFY.value and not self.normative_basis_revision_id:
            errors["normative_basis_revision"] = (
                "Non-VERIFY решение требует опубликованной нормативной редакции."
            )

        if self.supersedes_id:
            if self.supersedes_id == self.pk:
                errors["supersedes"] = "Решение не может заменять само себя."
            elif (
                self.supersedes.code != self.code
                or self.supersedes.organization_id != self.organization_id
            ):
                errors["supersedes"] = "Заменяемое решение должно иметь тот же код и область организации."

        if self.hash_algorithm != "SHA-256":
            errors["hash_algorithm"] = "Поддерживается только SHA-256."
        if not _valid_sha256(self.digest):
            errors["digest"] = "Контрольная сумма должна быть SHA-256 в нижнем hex-регистре."
        if self.canonical_json:
            try:
                stored = _parsed_object(self.canonical_json, field_name="canonical_json")
                expected = self.canonical_payload()
                if stored != json.loads(canonical_json(expected)):
                    errors["canonical_json"] = "Сохранённый снимок не соответствует полям решения."
                if hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest() != self.digest:
                    errors["digest"] = "SHA-256 не соответствует каноническому снимку решения."
            except ValidationError as error:
                errors["canonical_json"] = "; ".join(error.messages)
        else:
            errors["canonical_json"] = "Канонический снимок обязателен."

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Решение о правовом режиме неизменяемо; создайте новое решение.")
        self.code = self.code.strip().upper()
        self.module_id = self.module_id.strip().upper()
        self.digest = self.digest.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление решения о правовом режиме запрещено.")


class EvidenceEvent(models.Model):
    public_id = models.UUIDField(
        "Публичный идентификатор",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        related_name="evidence_events",
        verbose_name="Организация",
    )
    event_type = models.CharField(
        "Тип evidence-события",
        max_length=32,
        choices=_choices(EvidenceEventType),
        db_index=True,
    )
    subject_type = models.CharField("Тип предмета", max_length=128, db_index=True)
    subject_id = models.CharField("Идентификатор предмета", max_length=192, db_index=True)
    actor = models.ForeignKey(
        Employee,
        on_delete=models.PROTECT,
        related_name="evidence_events",
        verbose_name="Участник",
    )
    actor_snapshot = models.JSONField("Снимок участника", default=dict)
    occurred_at = models.DateTimeField(
        "Серверное время события",
        default=timezone.now,
        editable=False,
        db_index=True,
    )
    confirmation_method = models.CharField(
        "Способ подтверждения",
        max_length=32,
        choices=_choices(EvidenceConfirmationMethod),
    )
    requires_reauthentication = models.BooleanField(
        "Требовалась повторная аутентификация",
        default=False,
    )
    normative_basis_revision = models.ForeignKey(
        NormativeRevision,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="evidence_events",
        verbose_name="Нормативная редакция-основание",
    )
    normative_basis_code = models.CharField(
        "Снимок кода нормативного основания",
        max_length=256,
        blank=True,
        editable=False,
    )
    source_ids = models.JSONField("Traceable source IDs", default=list)
    correlation_id = models.CharField("Корреляционный идентификатор", max_length=192, blank=True)
    payload = models.JSONField("Evidence payload", default=dict)
    document_signature_id = models.PositiveBigIntegerField(
        "Связанное системное подтверждение документа",
        null=True,
        blank=True,
        editable=False,
    )
    corrects_event = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="corrections",
        verbose_name="Исправляет событие",
    )
    schema_version = models.CharField(
        "Версия схемы",
        max_length=64,
        default="eod.evidence.event-record.v1",
        editable=False,
    )
    canonical_json = models.TextField("Канонический снимок события", editable=False)
    hash_algorithm = models.CharField(
        "Алгоритм контроля целостности",
        max_length=16,
        default="SHA-256",
        editable=False,
    )
    digest = models.CharField("SHA-256 события", max_length=64, editable=False, db_index=True)
    created_at = models.DateTimeField("Создано", auto_now_add=True, editable=False)

    objects = AppendOnlyManager()

    class Meta:
        ordering = ("-occurred_at", "-pk")
        indexes = [
            models.Index(
                fields=("organization", "subject_type", "subject_id", "-occurred_at"),
                name="norm_evid_subject_idx",
            ),
            models.Index(
                fields=("organization", "event_type", "-occurred_at"),
                name="norm_evid_type_idx",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=("organization", "correlation_id"),
                condition=~Q(correlation_id=""),
                name="uniq_evidence_correlation_per_org",
            ),
            models.UniqueConstraint(
                fields=("document_signature_id",),
                condition=Q(event_type=EvidenceEventType.SIGNATURE.value),
                name="uniq_evidence_event_per_doc_signature",
            ),
        ]
        verbose_name = "evidence-событие"
        verbose_name_plural = "evidence-события"

    def __str__(self) -> str:
        return f"{self.event_type} · {self.subject_type}:{self.subject_id}"

    def _contract(self) -> EvidenceEventContract:
        return EvidenceEventContract(
            event_type=EvidenceEventType(self.event_type),
            subject_type=self.subject_type,
            subject_id=self.subject_id,
            actor_employee_id=self.actor_id,
            actor_snapshot=self.actor_snapshot,
            occurred_at=self.occurred_at,
            confirmation_method=EvidenceConfirmationMethod(self.confirmation_method),
            requires_reauthentication=self.requires_reauthentication,
            payload=self.payload,
            source_ids=tuple(self.source_ids or ()),
            basis_revision_code=self.normative_basis_code,
            correlation_id=self.correlation_id,
        )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema_version,
            "public_id": str(self.public_id),
            "organization_id": self.organization_id,
            "event": self._contract().canonical_payload(),
            "normative_basis": {
                "revision_id": self.normative_basis_revision_id,
                "revision_code": self.normative_basis_code,
            },
            "document_signature_id": self.document_signature_id,
            "corrects_event_public_id": (
                str(self.corrects_event.public_id) if self.corrects_event_id else ""
            ),
        }

    def _validate_document_signature(self, errors: dict[str, str]) -> None:
        if self.event_type != EvidenceEventType.SIGNATURE.value:
            if self.document_signature_id is not None:
                errors["document_signature_id"] = (
                    "Системное подтверждение документа связывается только с SIGNATURE."
                )
            return
        if self.document_signature_id is None:
            errors["document_signature_id"] = (
                "SIGNATURE должен ссылаться на существующее системное подтверждение документа."
            )
            return

        from apps.documents.models import DocumentSignature

        try:
            signature = DocumentSignature.objects.select_related(
                "snapshot__document", "employee"
            ).get(pk=self.document_signature_id)
        except DocumentSignature.DoesNotExist:
            errors["document_signature_id"] = "Системное подтверждение документа не найдено."
            return

        if signature.employee_id and signature.employee_id != self.actor_id:
            errors["actor"] = "Системное подтверждение создано другим сотрудником."
        if signature.snapshot.document.organization_id != self.organization_id:
            errors["organization"] = "Системное подтверждение относится к другой организации."
        if self.confirmation_method != signature.confirmation_method:
            errors["confirmation_method"] = (
                "Способ evidence-подтверждения не совпадает с DocumentSignature."
            )
        if self.payload.get("snapshot_digest") != signature.snapshot.digest:
            errors["payload"] = "Evidence payload содержит другой digest подписываемого снимка."
        if self.payload.get("purpose") != signature.purpose:
            errors["payload"] = "Evidence payload содержит другое назначение подписи."
        if self.payload.get("signature_checksum") != signature.checksum:
            errors["payload"] = "Evidence payload содержит другую checksum системного подтверждения."

    def clean(self) -> None:
        super().clean()
        errors: dict[str, str] = {}
        try:
            self._contract()
        except ValidationError as error:
            if hasattr(error, "message_dict"):
                errors.update(error.message_dict)
            else:
                errors["payload"] = "; ".join(error.messages)

        if not isinstance(self.actor_snapshot, dict):
            errors["actor_snapshot"] = "Снимок участника должен быть JSON-объектом."
        if not isinstance(self.payload, dict):
            errors["payload"] = "Evidence payload должен быть JSON-объектом."
        if not isinstance(self.source_ids, list):
            errors["source_ids"] = "Source IDs должны храниться JSON-массивом."
        if self.actor_id and self.actor.organization_id != self.organization_id:
            errors["actor"] = "Участник относится к другой организации."

        if self.normative_basis_revision_id:
            revision = self.normative_basis_revision
            if revision.status != PublicationStatus.PUBLISHED or not _valid_sha256(revision.digest):
                errors["normative_basis_revision"] = (
                    "Основанием может быть только опубликованная редакция с SHA-256."
                )
            if self.normative_basis_code != revision_evidence_code(revision):
                errors["normative_basis_code"] = "Снимок основания не совпадает с редакцией."
            document = revision.document
            if document.organization_id not in (None, self.organization_id):
                errors["normative_basis_revision"] = "Нормативная редакция недоступна организации события."
        elif self.normative_basis_code:
            errors["normative_basis_code"] = "Код основания нельзя хранить без связанной редакции."

        if self.corrects_event_id:
            if self.corrects_event_id == self.pk:
                errors["corrects_event"] = "Событие не может исправлять само себя."
            elif (
                self.corrects_event.organization_id != self.organization_id
                or self.corrects_event.event_type != self.event_type
                or self.corrects_event.subject_type != self.subject_type
                or self.corrects_event.subject_id != self.subject_id
            ):
                errors["corrects_event"] = (
                    "Исправление должно относиться к тому же типу события и тому же предмету."
                )

        self._validate_document_signature(errors)

        if self.hash_algorithm != "SHA-256":
            errors["hash_algorithm"] = "Поддерживается только SHA-256."
        if not _valid_sha256(self.digest):
            errors["digest"] = "Контрольная сумма должна быть SHA-256 в нижнем hex-регистре."
        if self.canonical_json:
            try:
                stored = _parsed_object(self.canonical_json, field_name="canonical_json")
                expected = self.canonical_payload()
                if stored != json.loads(canonical_json(expected)):
                    errors["canonical_json"] = "Сохранённый снимок не соответствует полям события."
                if hashlib.sha256(self.canonical_json.encode("utf-8")).hexdigest() != self.digest:
                    errors["digest"] = "SHA-256 не соответствует каноническому снимку события."
            except ValidationError as error:
                errors["canonical_json"] = "; ".join(error.messages)
        else:
            errors["canonical_json"] = "Канонический снимок обязателен."

        if errors:
            raise ValidationError(errors)

    def save(self, *args: Any, **kwargs: Any) -> None:
        if self.pk:
            raise ValidationError("Evidence-событие неизменяемо; создайте связанное исправление.")
        self.subject_type = self.subject_type.strip().lower()
        self.subject_id = self.subject_id.strip()
        self.correlation_id = self.correlation_id.strip()
        self.digest = self.digest.strip().lower()
        self.full_clean()
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Физическое удаление evidence-события запрещено.")
