from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Any

from django.core.exceptions import ValidationError

from apps.normatives.evidence import sha256_digest


class AuthorityDecision(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    VERIFY = "VERIFY"


class AuthorityBasisStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    VERIFY = "VERIFY"
    REJECTED = "REJECTED"


class AuthorityScopeKind(StrEnum):
    ORGANIZATION = "ORGANIZATION"
    DIVISION = "DIVISION"
    WORKPLACE = "WORKPLACE"
    OPERATIONAL_AREA = "OPERATIONAL_AREA"
    ENERGY_SITE = "ENERGY_SITE"
    EQUIPMENT = "EQUIPMENT"


class PersonnelRelationKind(StrEnum):
    EMPLOYEE = "EMPLOYEE"
    SECONDED = "SECONDED"
    CONTRACTOR = "CONTRACTOR"
    SYSTEM_OPERATOR = "SYSTEM_OPERATOR"


class AuthorityReason(StrEnum):
    EXPLICIT_GRANT = "EXPLICIT_GRANT"
    EMPLOYEE_INACTIVE = "EMPLOYEE_INACTIVE"
    EMPLOYMENT_NOT_EFFECTIVE = "EMPLOYMENT_NOT_EFFECTIVE"
    TENANT_MISMATCH = "TENANT_MISMATCH"
    NO_MATCHING_GRANT = "NO_MATCHING_GRANT"
    GRANT_INACTIVE = "GRANT_INACTIVE"
    GRANT_NOT_EFFECTIVE = "GRANT_NOT_EFFECTIVE"
    SCOPE_MISMATCH = "SCOPE_MISMATCH"
    BASIS_VERIFY = "BASIS_VERIFY"
    BASIS_REJECTED = "BASIS_REJECTED"
    QUALIFICATION_MISSING = "QUALIFICATION_MISSING"
    EXTERNAL_ENGAGEMENT_REQUIRED = "EXTERNAL_ENGAGEMENT_REQUIRED"
    EXTERNAL_ENGAGEMENT_NOT_EFFECTIVE = "EXTERNAL_ENGAGEMENT_NOT_EFFECTIVE"
    EXTERNAL_SCOPE_MISMATCH = "EXTERNAL_SCOPE_MISMATCH"
    SUBSTITUTION_NOT_ALLOWED = "SUBSTITUTION_NOT_ALLOWED"
    SUBSTITUTION_NOT_EFFECTIVE = "SUBSTITUTION_NOT_EFFECTIVE"
    SUBSTITUTION_SCOPE_MISMATCH = "SUBSTITUTION_SCOPE_MISMATCH"


_CODE_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9_.:-]*$")
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


def _normalized_code(value: object, *, field_name: str) -> str:
    normalized = _required_text(value, field_name=field_name).upper().replace(" ", "_")
    if not _CODE_PATTERN.fullmatch(normalized):
        raise ValidationError(
            {field_name: "Код может содержать только A-Z, 0-9, точку, двоеточие, дефис и _."}
        )
    return normalized


def _positive_int(value: object, *, field_name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ValidationError({field_name: "Требуется положительный целочисленный идентификатор."})
    return value


def _normalized_codes(values: Sequence[str], *, field_name: str) -> tuple[str, ...]:
    return tuple(
        sorted({_normalized_code(value, field_name=field_name) for value in values})
    )


def _normalized_source_ids(values: Sequence[str]) -> tuple[str, ...]:
    normalized = tuple(
        sorted(
            {
                _normalized_code(value, field_name="source_ids")
                for value in values
                if str(value or "").strip()
            }
        )
    )
    if not normalized:
        raise ValidationError({"source_ids": "Требуется хотя бы один traceable source ID."})
    return normalized


def _ensure_aware(value: datetime, *, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValidationError({field_name: "Время должно содержать часовой пояс."})
    return value


def _validate_window(
    valid_from: datetime,
    valid_until: datetime | None,
    *,
    field_name: str = "valid_until",
) -> None:
    _ensure_aware(valid_from, field_name="valid_from")
    if valid_until is not None:
        _ensure_aware(valid_until, field_name=field_name)
        if valid_until < valid_from:
            raise ValidationError({field_name: "Окончание периода раньше его начала."})


def _is_effective(
    *,
    active: bool,
    valid_from: datetime,
    valid_until: datetime | None,
    moment: datetime,
) -> bool:
    return active and valid_from <= moment and (
        valid_until is None or valid_until >= moment
    )


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
        {"snapshot": f"Неподдерживаемый тип snapshot: {type(value).__name__}."}
    )


@dataclass(frozen=True, slots=True)
class AuthorityScope:
    kind: AuthorityScopeKind
    reference: str
    label: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "kind", AuthorityScopeKind(self.kind))
        object.__setattr__(
            self,
            "reference",
            _required_text(self.reference, field_name="scope.reference"),
        )
        object.__setattr__(self, "label", " ".join(self.label.split()))

    def canonical_payload(self) -> dict[str, str]:
        return {
            "kind": self.kind.value,
            "reference": self.reference,
            "label": self.label,
        }


@dataclass(frozen=True, slots=True)
class AuthorityActorFact:
    employee_id: int
    organization_id: int
    relation_kind: PersonnelRelationKind
    full_name: str
    position: str
    division: str
    workplace: str
    employment_from: datetime
    employment_until: datetime | None = None
    is_active: bool = True
    application_roles: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "employee_id",
            _positive_int(self.employee_id, field_name="employee_id"),
        )
        object.__setattr__(
            self,
            "organization_id",
            _positive_int(self.organization_id, field_name="organization_id"),
        )
        object.__setattr__(self, "relation_kind", PersonnelRelationKind(self.relation_kind))
        object.__setattr__(
            self,
            "full_name",
            _required_text(self.full_name, field_name="full_name"),
        )
        object.__setattr__(self, "position", " ".join(self.position.split()))
        object.__setattr__(self, "division", " ".join(self.division.split()))
        object.__setattr__(self, "workplace", " ".join(self.workplace.split()))
        object.__setattr__(
            self,
            "application_roles",
            _normalized_codes(self.application_roles, field_name="application_roles"),
        )
        _validate_window(self.employment_from, self.employment_until)

    def is_effective_at(self, moment: datetime) -> bool:
        return _is_effective(
            active=self.is_active,
            valid_from=self.employment_from,
            valid_until=self.employment_until,
            moment=moment,
        )


@dataclass(frozen=True, slots=True)
class AuthorityRequest:
    organization_id: int
    actor_employee_id: int
    action_code: str
    occurred_at: datetime
    scope: AuthorityScope
    subject_type: str
    subject_id: str
    required_qualification_codes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "organization_id",
            _positive_int(self.organization_id, field_name="organization_id"),
        )
        object.__setattr__(
            self,
            "actor_employee_id",
            _positive_int(self.actor_employee_id, field_name="actor_employee_id"),
        )
        object.__setattr__(
            self,
            "action_code",
            _normalized_code(self.action_code, field_name="action_code"),
        )
        object.__setattr__(
            self,
            "occurred_at",
            _ensure_aware(self.occurred_at, field_name="occurred_at"),
        )
        if not isinstance(self.scope, AuthorityScope):
            raise ValidationError({"scope": "Требуется структурированная область действия."})
        object.__setattr__(
            self,
            "subject_type",
            _normalized_code(self.subject_type, field_name="subject_type"),
        )
        object.__setattr__(
            self,
            "subject_id",
            _required_text(self.subject_id, field_name="subject_id"),
        )
        object.__setattr__(
            self,
            "required_qualification_codes",
            _normalized_codes(
                self.required_qualification_codes,
                field_name="required_qualification_codes",
            ),
        )


@dataclass(frozen=True, slots=True)
class AuthorityGrantFact:
    grant_id: str
    employee_id: int
    organization_id: int
    action_code: str
    scope: AuthorityScope
    valid_from: datetime
    valid_until: datetime | None
    basis_status: AuthorityBasisStatus
    basis_reference: str
    source_ids: tuple[str, ...]
    is_active: bool = True
    allow_substitution: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "grant_id",
            _required_text(self.grant_id, field_name="grant_id"),
        )
        object.__setattr__(
            self,
            "employee_id",
            _positive_int(self.employee_id, field_name="employee_id"),
        )
        object.__setattr__(
            self,
            "organization_id",
            _positive_int(self.organization_id, field_name="organization_id"),
        )
        object.__setattr__(
            self,
            "action_code",
            _normalized_code(self.action_code, field_name="action_code"),
        )
        if not isinstance(self.scope, AuthorityScope):
            raise ValidationError({"scope": "Требуется структурированная область grant."})
        object.__setattr__(self, "basis_status", AuthorityBasisStatus(self.basis_status))
        object.__setattr__(
            self,
            "basis_reference",
            _required_text(self.basis_reference, field_name="basis_reference"),
        )
        object.__setattr__(self, "source_ids", _normalized_source_ids(self.source_ids))
        _validate_window(self.valid_from, self.valid_until)

    def is_effective_at(self, moment: datetime) -> bool:
        return _is_effective(
            active=self.is_active,
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            moment=moment,
        )


@dataclass(frozen=True, slots=True)
class AuthorityQualificationFact:
    employee_id: int
    code: str
    valid_from: datetime
    valid_until: datetime | None = None
    is_active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "employee_id",
            _positive_int(self.employee_id, field_name="employee_id"),
        )
        object.__setattr__(self, "code", _normalized_code(self.code, field_name="code"))
        _validate_window(self.valid_from, self.valid_until)

    def is_effective_at(self, moment: datetime) -> bool:
        return _is_effective(
            active=self.is_active,
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            moment=moment,
        )


@dataclass(frozen=True, slots=True)
class AuthoritySubstitutionFact:
    substitution_id: str
    replaced_employee_id: int
    substitute_employee_id: int
    organization_id: int
    action_codes: tuple[str, ...]
    scope: AuthorityScope
    valid_from: datetime
    valid_until: datetime | None
    basis_status: AuthorityBasisStatus
    basis_reference: str
    is_active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "substitution_id",
            _required_text(self.substitution_id, field_name="substitution_id"),
        )
        object.__setattr__(
            self,
            "replaced_employee_id",
            _positive_int(self.replaced_employee_id, field_name="replaced_employee_id"),
        )
        object.__setattr__(
            self,
            "substitute_employee_id",
            _positive_int(self.substitute_employee_id, field_name="substitute_employee_id"),
        )
        if self.replaced_employee_id == self.substitute_employee_id:
            raise ValidationError(
                {"substitute_employee_id": "Сотрудник не может замещать сам себя."}
            )
        object.__setattr__(
            self,
            "organization_id",
            _positive_int(self.organization_id, field_name="organization_id"),
        )
        object.__setattr__(
            self,
            "action_codes",
            _normalized_codes(self.action_codes, field_name="action_codes"),
        )
        if not self.action_codes:
            raise ValidationError({"action_codes": "Нужно явно указать разрешённые действия."})
        if not isinstance(self.scope, AuthorityScope):
            raise ValidationError({"scope": "Требуется структурированная область замещения."})
        object.__setattr__(self, "basis_status", AuthorityBasisStatus(self.basis_status))
        object.__setattr__(
            self,
            "basis_reference",
            _required_text(self.basis_reference, field_name="basis_reference"),
        )
        _validate_window(self.valid_from, self.valid_until)

    def is_effective_at(self, moment: datetime) -> bool:
        return _is_effective(
            active=self.is_active,
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            moment=moment,
        )


@dataclass(frozen=True, slots=True)
class ExternalPersonnelEngagementFact:
    engagement_id: str
    employee_id: int
    home_organization_id: int
    host_organization_id: int
    relation_kind: PersonnelRelationKind
    scope: AuthorityScope
    valid_from: datetime
    valid_until: datetime | None
    basis_status: AuthorityBasisStatus
    basis_reference: str
    is_active: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "engagement_id",
            _required_text(self.engagement_id, field_name="engagement_id"),
        )
        object.__setattr__(
            self,
            "employee_id",
            _positive_int(self.employee_id, field_name="employee_id"),
        )
        object.__setattr__(
            self,
            "home_organization_id",
            _positive_int(self.home_organization_id, field_name="home_organization_id"),
        )
        object.__setattr__(
            self,
            "host_organization_id",
            _positive_int(self.host_organization_id, field_name="host_organization_id"),
        )
        object.__setattr__(self, "relation_kind", PersonnelRelationKind(self.relation_kind))
        if self.relation_kind == PersonnelRelationKind.EMPLOYEE:
            raise ValidationError(
                {"relation_kind": "Внешняя связь не применяется к штатному сотруднику."}
            )
        if not isinstance(self.scope, AuthorityScope):
            raise ValidationError({"scope": "Требуется структурированная область внешнего допуска."})
        object.__setattr__(self, "basis_status", AuthorityBasisStatus(self.basis_status))
        object.__setattr__(
            self,
            "basis_reference",
            _required_text(self.basis_reference, field_name="basis_reference"),
        )
        _validate_window(self.valid_from, self.valid_until)

    def is_effective_at(self, moment: datetime) -> bool:
        return _is_effective(
            active=self.is_active,
            valid_from=self.valid_from,
            valid_until=self.valid_until,
            moment=moment,
        )


@dataclass(frozen=True, slots=True)
class AuthorityEvaluationResult:
    decision: AuthorityDecision
    reasons: tuple[AuthorityReason, ...]
    snapshot: Mapping[str, Any]
    matched_grant_id: str = ""
    schema_version: str = field(default="eod.personnel-authority.evaluation.v1", init=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "decision", AuthorityDecision(self.decision))
        object.__setattr__(
            self,
            "reasons",
            tuple(sorted({AuthorityReason(reason) for reason in self.reasons}, key=str)),
        )
        if not self.reasons:
            raise ValidationError({"reasons": "Результат должен содержать хотя бы одну причину."})
        if not isinstance(self.snapshot, Mapping):
            raise ValidationError({"snapshot": "Snapshot должен быть JSON-объектом."})
        _assert_secret_free(self.snapshot)
        object.__setattr__(self, "snapshot", _freeze_json(dict(self.snapshot)))
        object.__setattr__(self, "matched_grant_id", self.matched_grant_id.strip())
        if self.decision == AuthorityDecision.ALLOW and not self.matched_grant_id:
            raise ValidationError(
                {"matched_grant_id": "ALLOW требует явного структурированного grant."}
            )

    @property
    def digest(self) -> str:
        return sha256_digest(self.canonical_payload())

    def canonical_payload(self) -> dict[str, Any]:
        return {
            "schema": self.schema_version,
            "decision": self.decision.value,
            "reasons": [reason.value for reason in self.reasons],
            "matched_grant_id": self.matched_grant_id,
            "snapshot": self.snapshot,
        }


def _scope_matches(
    granted_scope: AuthorityScope,
    requested_scope: AuthorityScope,
    organization_id: int,
) -> bool:
    if granted_scope.kind == AuthorityScopeKind.ORGANIZATION:
        return granted_scope.reference == str(organization_id)
    return (
        granted_scope.kind == requested_scope.kind
        and granted_scope.reference == requested_scope.reference
    )


def _basis_decision(status: AuthorityBasisStatus) -> tuple[AuthorityDecision, AuthorityReason] | None:
    if status == AuthorityBasisStatus.CONFIRMED:
        return None
    if status == AuthorityBasisStatus.VERIFY:
        return AuthorityDecision.VERIFY, AuthorityReason.BASIS_VERIFY
    return AuthorityDecision.DENY, AuthorityReason.BASIS_REJECTED


def _build_snapshot(
    *,
    actor: AuthorityActorFact,
    request: AuthorityRequest,
    grant: AuthorityGrantFact | None,
    substitution: AuthoritySubstitutionFact | None,
    external_engagement: ExternalPersonnelEngagementFact | None,
    qualifications: Sequence[AuthorityQualificationFact],
    decision: AuthorityDecision,
    reasons: Sequence[AuthorityReason],
) -> dict[str, Any]:
    return {
        "actor": {
            "employee_id": actor.employee_id,
            "organization_id": actor.organization_id,
            "relation_kind": actor.relation_kind.value,
            "full_name": actor.full_name,
            "position": actor.position,
            "division": actor.division,
            "workplace": actor.workplace,
            "application_roles": list(actor.application_roles),
        },
        "request": {
            "organization_id": request.organization_id,
            "actor_employee_id": request.actor_employee_id,
            "action_code": request.action_code,
            "occurred_at": request.occurred_at.astimezone(UTC),
            "scope": request.scope.canonical_payload(),
            "subject_type": request.subject_type,
            "subject_id": request.subject_id,
            "required_qualification_codes": list(request.required_qualification_codes),
        },
        "grant": (
            {
                "grant_id": grant.grant_id,
                "employee_id": grant.employee_id,
                "organization_id": grant.organization_id,
                "action_code": grant.action_code,
                "scope": grant.scope.canonical_payload(),
                "valid_from": grant.valid_from.astimezone(UTC),
                "valid_until": (
                    grant.valid_until.astimezone(UTC) if grant.valid_until else None
                ),
                "basis_status": grant.basis_status.value,
                "basis_reference": grant.basis_reference,
                "source_ids": list(grant.source_ids),
                "allow_substitution": grant.allow_substitution,
            }
            if grant
            else None
        ),
        "substitution": (
            {
                "substitution_id": substitution.substitution_id,
                "replaced_employee_id": substitution.replaced_employee_id,
                "substitute_employee_id": substitution.substitute_employee_id,
                "action_codes": list(substitution.action_codes),
                "scope": substitution.scope.canonical_payload(),
                "basis_status": substitution.basis_status.value,
                "basis_reference": substitution.basis_reference,
            }
            if substitution
            else None
        ),
        "external_engagement": (
            {
                "engagement_id": external_engagement.engagement_id,
                "home_organization_id": external_engagement.home_organization_id,
                "host_organization_id": external_engagement.host_organization_id,
                "relation_kind": external_engagement.relation_kind.value,
                "scope": external_engagement.scope.canonical_payload(),
                "basis_status": external_engagement.basis_status.value,
                "basis_reference": external_engagement.basis_reference,
            }
            if external_engagement
            else None
        ),
        "qualifications": [
            {
                "employee_id": item.employee_id,
                "code": item.code,
                "valid_from": item.valid_from.astimezone(UTC),
                "valid_until": item.valid_until.astimezone(UTC) if item.valid_until else None,
            }
            for item in sorted(qualifications, key=lambda item: item.code)
        ],
        "decision": decision.value,
        "reasons": [reason.value for reason in reasons],
    }


def evaluate_authority(
    *,
    actor: AuthorityActorFact,
    request: AuthorityRequest,
    grants: Sequence[AuthorityGrantFact],
    qualifications: Sequence[AuthorityQualificationFact] = (),
    substitutions: Sequence[AuthoritySubstitutionFact] = (),
    external_engagements: Sequence[ExternalPersonnelEngagementFact] = (),
) -> AuthorityEvaluationResult:
    if actor.employee_id != request.actor_employee_id:
        raise ValidationError({"actor_employee_id": "Запрос относится к другому сотруднику."})

    terminal_reasons: list[AuthorityReason] = []
    if not actor.is_active:
        terminal_reasons.append(AuthorityReason.EMPLOYEE_INACTIVE)
    if not actor.is_effective_at(request.occurred_at):
        terminal_reasons.append(AuthorityReason.EMPLOYMENT_NOT_EFFECTIVE)

    external_engagement: ExternalPersonnelEngagementFact | None = None
    precondition_decision = AuthorityDecision.DENY
    if actor.relation_kind == PersonnelRelationKind.EMPLOYEE:
        if actor.organization_id != request.organization_id:
            terminal_reasons.append(AuthorityReason.TENANT_MISMATCH)
    else:
        candidates = [
            item
            for item in external_engagements
            if item.employee_id == actor.employee_id
            and item.host_organization_id == request.organization_id
            and item.relation_kind == actor.relation_kind
        ]
        if not candidates:
            terminal_reasons.append(AuthorityReason.EXTERNAL_ENGAGEMENT_REQUIRED)
        else:
            external_engagement = sorted(candidates, key=lambda item: item.engagement_id)[0]
            if not external_engagement.is_effective_at(request.occurred_at):
                terminal_reasons.append(AuthorityReason.EXTERNAL_ENGAGEMENT_NOT_EFFECTIVE)
            if not _scope_matches(
                external_engagement.scope,
                request.scope,
                request.organization_id,
            ):
                terminal_reasons.append(AuthorityReason.EXTERNAL_SCOPE_MISMATCH)
            basis = _basis_decision(external_engagement.basis_status)
            if basis:
                precondition_decision, reason = basis
                terminal_reasons.append(reason)

    if terminal_reasons:
        decision = (
            AuthorityDecision.VERIFY
            if precondition_decision == AuthorityDecision.VERIFY
            and set(terminal_reasons) == {AuthorityReason.BASIS_VERIFY}
            else AuthorityDecision.DENY
        )
        snapshot = _build_snapshot(
            actor=actor,
            request=request,
            grant=None,
            substitution=None,
            external_engagement=external_engagement,
            qualifications=(),
            decision=decision,
            reasons=terminal_reasons,
        )
        return AuthorityEvaluationResult(
            decision=decision,
            reasons=tuple(terminal_reasons),
            snapshot=snapshot,
        )

    active_qualification_codes = {
        item.code
        for item in qualifications
        if item.employee_id == actor.employee_id and item.is_effective_at(request.occurred_at)
    }
    missing_qualifications = set(request.required_qualification_codes) - active_qualification_codes
    if missing_qualifications:
        reasons = (AuthorityReason.QUALIFICATION_MISSING,)
        snapshot = _build_snapshot(
            actor=actor,
            request=request,
            grant=None,
            substitution=None,
            external_engagement=external_engagement,
            qualifications=qualifications,
            decision=AuthorityDecision.DENY,
            reasons=reasons,
        )
        return AuthorityEvaluationResult(
            decision=AuthorityDecision.DENY,
            reasons=reasons,
            snapshot=snapshot,
        )

    action_grants = sorted(
        (grant for grant in grants if grant.action_code == request.action_code),
        key=lambda item: item.grant_id,
    )
    if not action_grants:
        reasons = (AuthorityReason.NO_MATCHING_GRANT,)
        snapshot = _build_snapshot(
            actor=actor,
            request=request,
            grant=None,
            substitution=None,
            external_engagement=external_engagement,
            qualifications=qualifications,
            decision=AuthorityDecision.DENY,
            reasons=reasons,
        )
        return AuthorityEvaluationResult(
            decision=AuthorityDecision.DENY,
            reasons=reasons,
            snapshot=snapshot,
        )

    verify_candidate: tuple[
        AuthorityGrantFact,
        AuthoritySubstitutionFact | None,
        tuple[AuthorityReason, ...],
    ] | None = None
    deny_candidate: tuple[
        AuthorityGrantFact,
        AuthoritySubstitutionFact | None,
        tuple[AuthorityReason, ...],
    ] | None = None

    for grant in action_grants:
        reasons: list[AuthorityReason] = []
        substitution: AuthoritySubstitutionFact | None = None

        if grant.organization_id != request.organization_id:
            reasons.append(AuthorityReason.TENANT_MISMATCH)
        if not grant.is_active:
            reasons.append(AuthorityReason.GRANT_INACTIVE)
        elif not grant.is_effective_at(request.occurred_at):
            reasons.append(AuthorityReason.GRANT_NOT_EFFECTIVE)
        if not _scope_matches(grant.scope, request.scope, request.organization_id):
            reasons.append(AuthorityReason.SCOPE_MISMATCH)

        if grant.employee_id != actor.employee_id:
            substitution_candidates = [
                item
                for item in substitutions
                if item.replaced_employee_id == grant.employee_id
                and item.substitute_employee_id == actor.employee_id
                and item.organization_id == request.organization_id
            ]
            if not grant.allow_substitution or not substitution_candidates:
                reasons.append(AuthorityReason.SUBSTITUTION_NOT_ALLOWED)
            else:
                substitution = sorted(
                    substitution_candidates,
                    key=lambda item: item.substitution_id,
                )[0]
                if not substitution.is_effective_at(request.occurred_at):
                    reasons.append(AuthorityReason.SUBSTITUTION_NOT_EFFECTIVE)
                if request.action_code not in substitution.action_codes:
                    reasons.append(AuthorityReason.SUBSTITUTION_NOT_ALLOWED)
                if not _scope_matches(
                    substitution.scope,
                    request.scope,
                    request.organization_id,
                ):
                    reasons.append(AuthorityReason.SUBSTITUTION_SCOPE_MISMATCH)
                substitution_basis = _basis_decision(substitution.basis_status)
                if substitution_basis:
                    _, reason = substitution_basis
                    reasons.append(reason)

        grant_basis = _basis_decision(grant.basis_status)
        if grant_basis:
            _, reason = grant_basis
            reasons.append(reason)

        if not reasons:
            reasons_tuple = (AuthorityReason.EXPLICIT_GRANT,)
            snapshot = _build_snapshot(
                actor=actor,
                request=request,
                grant=grant,
                substitution=substitution,
                external_engagement=external_engagement,
                qualifications=qualifications,
                decision=AuthorityDecision.ALLOW,
                reasons=reasons_tuple,
            )
            return AuthorityEvaluationResult(
                decision=AuthorityDecision.ALLOW,
                reasons=reasons_tuple,
                snapshot=snapshot,
                matched_grant_id=grant.grant_id,
            )

        reasons_tuple = tuple(reasons)
        if AuthorityReason.BASIS_VERIFY in reasons_tuple and not any(
            reason
            in {
                AuthorityReason.TENANT_MISMATCH,
                AuthorityReason.GRANT_INACTIVE,
                AuthorityReason.GRANT_NOT_EFFECTIVE,
                AuthorityReason.SCOPE_MISMATCH,
                AuthorityReason.SUBSTITUTION_NOT_ALLOWED,
                AuthorityReason.SUBSTITUTION_NOT_EFFECTIVE,
                AuthorityReason.SUBSTITUTION_SCOPE_MISMATCH,
                AuthorityReason.BASIS_REJECTED,
            }
            for reason in reasons_tuple
        ):
            verify_candidate = (grant, substitution, reasons_tuple)
        elif deny_candidate is None:
            deny_candidate = (grant, substitution, reasons_tuple)

    if verify_candidate is not None:
        grant, substitution, reasons = verify_candidate
        decision = AuthorityDecision.VERIFY
    else:
        grant, substitution, reasons = deny_candidate or (
            action_grants[0],
            None,
            (AuthorityReason.NO_MATCHING_GRANT,),
        )
        decision = AuthorityDecision.DENY

    snapshot = _build_snapshot(
        actor=actor,
        request=request,
        grant=grant,
        substitution=substitution,
        external_engagement=external_engagement,
        qualifications=qualifications,
        decision=decision,
        reasons=reasons,
    )
    return AuthorityEvaluationResult(
        decision=decision,
        reasons=reasons,
        snapshot=snapshot,
        matched_grant_id=grant.grant_id if decision == AuthorityDecision.VERIFY else "",
    )
