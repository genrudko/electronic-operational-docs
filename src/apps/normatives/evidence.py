from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from django.core.exceptions import ValidationError


class ProductTargetMode(StrEnum):
    ELECTRONIC_ORIGINAL_TARGET = "ELECTRONIC_ORIGINAL_TARGET"
    HYBRID = "HYBRID"
    PAPER_MIRROR = "PAPER_MIRROR"
    EVIDENCE_EVENT = "EVIDENCE_EVENT"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    POST_DEMO = "POST_DEMO"


class ProvenLegalMode(StrEnum):
    ELECTRONIC_ORIGINAL = "ELECTRONIC_ORIGINAL"
    HYBRID = "HYBRID"
    PAPER_MIRROR = "PAPER_MIRROR"
    REFERENCE_ONLY = "REFERENCE_ONLY"
    VERIFY = "VERIFY"


class NormativeEvidenceStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    PARTIAL = "PARTIAL"
    VERIFY = "VERIFY"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class LocalActStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    VERIFY = "VERIFY"
    NOT_REQUIRED = "NOT_REQUIRED"


class EvidenceEventType(StrEnum):
    SIGNATURE = "SIGNATURE"
    ACKNOWLEDGEMENT = "ACKNOWLEDGEMENT"
    INSTRUCTION = "INSTRUCTION"
    KNOWLEDGE_CHECK = "KNOWLEDGE_CHECK"
    ACTION_CONFIRMATION = "ACTION_CONFIRMATION"


class EvidenceConfirmationMethod(StrEnum):
    PASSWORD_REAUTH = "PASSWORD_REAUTH"
    SESSION_AUTH = "SESSION_AUTH"
    LEGACY_MIGRATION = "LEGACY_MIGRATION"
    DEMO_SEED = "DEMO_SEED"


_TARGET_PROVEN_COMPATIBILITY: dict[ProductTargetMode, frozenset[ProvenLegalMode]] = {
    ProductTargetMode.ELECTRONIC_ORIGINAL_TARGET: frozenset(
        {ProvenLegalMode.ELECTRONIC_ORIGINAL, ProvenLegalMode.VERIFY}
    ),
    ProductTargetMode.HYBRID: frozenset({ProvenLegalMode.HYBRID, ProvenLegalMode.VERIFY}),
    ProductTargetMode.PAPER_MIRROR: frozenset(
        {ProvenLegalMode.PAPER_MIRROR, ProvenLegalMode.VERIFY}
    ),
    ProductTargetMode.REFERENCE_ONLY: frozenset(
        {ProvenLegalMode.REFERENCE_ONLY, ProvenLegalMode.VERIFY}
    ),
    ProductTargetMode.EVIDENCE_EVENT: frozenset({ProvenLegalMode.VERIFY}),
    ProductTargetMode.POST_DEMO: frozenset({ProvenLegalMode.VERIFY}),
}

_EVENT_REQUIRED_PAYLOAD_FIELDS: dict[EvidenceEventType, frozenset[str]] = {
    EvidenceEventType.SIGNATURE: frozenset({"snapshot_digest", "purpose"}),
    EvidenceEventType.ACKNOWLEDGEMENT: frozenset(
        {"content_digest", "acknowledgement_scope"}
    ),
    EvidenceEventType.INSTRUCTION: frozenset(
        {"content_digest", "instruction_kind", "instructor_employee_id"}
    ),
    EvidenceEventType.KNOWLEDGE_CHECK: frozenset(
        {"result", "assessment_reference"}
    ),
    EvidenceEventType.ACTION_CONFIRMATION: frozenset(
        {"action_code", "subject_state_digest"}
    ),
}

_ACTOR_SNAPSHOT_FIELDS = frozenset(
    {"employee_id", "username", "full_name", "position", "division", "workplace"}
)

_FORBIDDEN_KEY_TOKENS = frozenset(
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


def _normalized_key(value: object) -> str:
    return "".join(character for character in str(value).casefold() if character.isalnum())


_FORBIDDEN_NORMALIZED_KEY_TOKENS = frozenset(
    _normalized_key(token) for token in _FORBIDDEN_KEY_TOKENS
)


def _required_text(value: object, *, field_name: str) -> str:
    normalized = " ".join(str(value or "").split())
    if not normalized:
        raise ValidationError({field_name: "Поле обязательно."})
    return normalized


def _normalized_source_ids(values: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(
        sorted(
            {
                token
                for value in values
                if (token := " ".join(str(value or "").split()).upper())
            }
        )
    )
    if not normalized:
        raise ValidationError({"source_ids": "Требуется хотя бы один traceable source ID."})
    return normalized


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime):
        moment = value
        if moment.tzinfo is None or moment.utcoffset() is None:
            raise ValidationError({"occurred_at": "Время должно содержать часовой пояс."})
        return moment.astimezone(UTC).isoformat(timespec="microseconds").replace(
            "+00:00", "Z"
        )
    if isinstance(value, date):
        return value.isoformat()
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise ValidationError(
        {"payload": f"Неподдерживаемый тип canonical JSON: {type(value).__name__}."}
    )


def _freeze_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({str(key): _freeze_json(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_json(item) for item in value)
    if isinstance(value, (datetime, date)) or value is None or isinstance(
        value, (str, int, float, bool)
    ):
        return value
    raise ValidationError(
        {"payload": f"Неподдерживаемый тип canonical JSON: {type(value).__name__}."}
    )


def canonical_json(value: Mapping[str, Any]) -> str:
    return json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def _assert_secret_free(value: Any, *, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            normalized_key = _normalized_key(key)
            if any(token in normalized_key for token in _FORBIDDEN_NORMALIZED_KEY_TOKENS):
                raise ValidationError(
                    {"payload": f"Секретное поле запрещено в evidence payload: {path}.{key}."}
                )
            _assert_secret_free(item, path=f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _assert_secret_free(item, path=f"{path}[{index}]")


def _normalized_actor_snapshot(
    value: Mapping[str, Any],
    *,
    actor_employee_id: int,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValidationError({"actor_snapshot": "Actor snapshot должен быть JSON-объектом."})
    missing = sorted(field_name for field_name in _ACTOR_SNAPSHOT_FIELDS if field_name not in value)
    if missing:
        raise ValidationError(
            {
                "actor_snapshot": (
                    "В actor snapshot отсутствуют обязательные поля: "
                    + ", ".join(missing)
                    + "."
                )
            }
        )
    if value.get("employee_id") != actor_employee_id:
        raise ValidationError(
            {"actor_snapshot": "Actor snapshot относится к другому сотруднику."}
        )
    _required_text(value.get("full_name"), field_name="actor_snapshot.full_name")
    _assert_secret_free(value, path="actor_snapshot")
    return _freeze_json(value)


@dataclass(frozen=True, slots=True)
class LegalModeDecisionContract:
    code: str
    module_id: str
    subject_label: str
    product_target_mode: ProductTargetMode
    source_ids: tuple[str, ...]
    proven_legal_mode: ProvenLegalMode = ProvenLegalMode.VERIFY
    normative_evidence_status: NormativeEvidenceStatus = NormativeEvidenceStatus.VERIFY
    local_act_status: LocalActStatus = LocalActStatus.VERIFY
    basis_revision_code: str = ""
    decision_basis: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _required_text(self.code, field_name="code").upper())
        object.__setattr__(
            self,
            "module_id",
            _required_text(self.module_id, field_name="module_id").upper(),
        )
        object.__setattr__(
            self,
            "subject_label",
            _required_text(self.subject_label, field_name="subject_label"),
        )
        object.__setattr__(
            self,
            "product_target_mode",
            ProductTargetMode(self.product_target_mode),
        )
        object.__setattr__(
            self,
            "proven_legal_mode",
            ProvenLegalMode(self.proven_legal_mode),
        )
        object.__setattr__(
            self,
            "normative_evidence_status",
            NormativeEvidenceStatus(self.normative_evidence_status),
        )
        object.__setattr__(
            self,
            "local_act_status",
            LocalActStatus(self.local_act_status),
        )
        object.__setattr__(self, "source_ids", _normalized_source_ids(self.source_ids))
        object.__setattr__(
            self,
            "basis_revision_code",
            " ".join(self.basis_revision_code.split()).upper(),
        )
        object.__setattr__(
            self,
            "decision_basis",
            " ".join(self.decision_basis.split()),
        )

        allowed = _TARGET_PROVEN_COMPATIBILITY[self.product_target_mode]
        if self.proven_legal_mode not in allowed:
            raise ValidationError(
                {
                    "proven_legal_mode": (
                        "Доказанный режим несовместим с product target; "
                        "target и proven mode нельзя подменять друг другом."
                    )
                }
            )

        if self.proven_legal_mode != ProvenLegalMode.VERIFY:
            errors: dict[str, str] = {}
            if self.normative_evidence_status != NormativeEvidenceStatus.CONFIRMED:
                errors["normative_evidence_status"] = (
                    "Non-VERIFY режим требует подтверждённого нормативного evidence."
                )
            if self.local_act_status == LocalActStatus.VERIFY:
                errors["local_act_status"] = (
                    "Non-VERIFY режим требует закрытого статуса применимого локального акта."
                )
            if not self.basis_revision_code:
                errors["basis_revision_code"] = (
                    "Non-VERIFY режим требует traceable published basis revision."
                )
            if not self.decision_basis:
                errors["decision_basis"] = (
                    "Non-VERIFY режим требует явного основания решения."
                )
            if errors:
                raise ValidationError(errors)

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": "eod.normative.legal-mode-decision.v1",
            "code": self.code,
            "module_id": self.module_id,
            "subject_label": self.subject_label,
            "product_target_mode": self.product_target_mode.value,
            "proven_legal_mode": self.proven_legal_mode.value,
            "normative_evidence_status": self.normative_evidence_status.value,
            "local_act_status": self.local_act_status.value,
            "basis_revision_code": self.basis_revision_code,
            "source_ids": list(self.source_ids),
            "decision_basis": self.decision_basis,
        }

    @property
    def digest(self) -> str:
        return sha256_digest(self.canonical_payload())


@dataclass(frozen=True, slots=True)
class EvidenceEventContract:
    event_type: EvidenceEventType
    subject_type: str
    subject_id: str
    actor_employee_id: int
    actor_snapshot: Mapping[str, Any]
    occurred_at: datetime
    confirmation_method: EvidenceConfirmationMethod
    payload: Mapping[str, Any]
    source_ids: tuple[str, ...]
    basis_revision_code: str = ""
    requires_reauthentication: bool = False
    correlation_id: str = ""
    schema_version: str = field(default="eod.evidence.event.v1", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "event_type", EvidenceEventType(self.event_type))
        object.__setattr__(
            self,
            "confirmation_method",
            EvidenceConfirmationMethod(self.confirmation_method),
        )
        object.__setattr__(
            self,
            "subject_type",
            _required_text(self.subject_type, field_name="subject_type").lower(),
        )
        object.__setattr__(
            self,
            "subject_id",
            _required_text(self.subject_id, field_name="subject_id"),
        )
        if not isinstance(self.actor_employee_id, int) or self.actor_employee_id <= 0:
            raise ValidationError(
                {"actor_employee_id": "Требуется положительный идентификатор сотрудника."}
            )
        object.__setattr__(
            self,
            "actor_snapshot",
            _normalized_actor_snapshot(
                self.actor_snapshot,
                actor_employee_id=self.actor_employee_id,
            ),
        )
        if self.occurred_at.tzinfo is None or self.occurred_at.utcoffset() is None:
            raise ValidationError({"occurred_at": "Время должно содержать часовой пояс."})
        if not isinstance(self.payload, Mapping):
            raise ValidationError({"payload": "Evidence payload должен быть JSON-объектом."})

        normalized_payload = dict(self.payload)
        _assert_secret_free(normalized_payload)
        object.__setattr__(self, "payload", _freeze_json(normalized_payload))
        object.__setattr__(self, "source_ids", _normalized_source_ids(self.source_ids))
        object.__setattr__(
            self,
            "basis_revision_code",
            " ".join(self.basis_revision_code.split()).upper(),
        )
        object.__setattr__(
            self,
            "correlation_id",
            " ".join(self.correlation_id.split()),
        )

        missing = sorted(
            field_name
            for field_name in _EVENT_REQUIRED_PAYLOAD_FIELDS[self.event_type]
            if normalized_payload.get(field_name) in (None, "", [], {})
        )
        if missing:
            raise ValidationError(
                {
                    "payload": (
                        f"Для события {self.event_type.value} отсутствуют обязательные поля: "
                        + ", ".join(missing)
                        + "."
                    )
                }
            )

        if (
            self.event_type == EvidenceEventType.SIGNATURE
            and self.confirmation_method == EvidenceConfirmationMethod.SESSION_AUTH
        ):
            raise ValidationError(
                {
                    "confirmation_method": (
                        "SIGNATURE нельзя фиксировать только текущей сессией; "
                        "нужен PASSWORD_REAUTH либо честный LEGACY_MIGRATION/DEMO_SEED."
                    )
                }
            )
        if self.requires_reauthentication:
            if self.confirmation_method != EvidenceConfirmationMethod.PASSWORD_REAUTH:
                raise ValidationError(
                    {
                        "confirmation_method": (
                            "Re-auth-required событие требует PASSWORD_REAUTH."
                        )
                    }
                )
        elif self.confirmation_method == EvidenceConfirmationMethod.PASSWORD_REAUTH:
            raise ValidationError(
                {
                    "requires_reauthentication": (
                        "PASSWORD_REAUTH должен быть отражён явным re-auth requirement."
                    )
                }
            )

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema_version,
            "event_type": self.event_type.value,
            "subject": {
                "type": self.subject_type,
                "id": self.subject_id,
            },
            "actor_employee_id": self.actor_employee_id,
            "actor_snapshot": dict(self.actor_snapshot),
            "occurred_at": self.occurred_at,
            "confirmation_method": self.confirmation_method.value,
            "requires_reauthentication": self.requires_reauthentication,
            "basis_revision_code": self.basis_revision_code,
            "source_ids": list(self.source_ids),
            "correlation_id": self.correlation_id,
            "payload": dict(self.payload),
        }

    @property
    def digest(self) -> str:
        return sha256_digest(self.canonical_payload())
