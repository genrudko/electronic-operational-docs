from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Q, QuerySet
from django.utils import timezone

from apps.documents.models import DocumentSignature
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
from .evidence_models import (
    EvidenceEvent,
    LegalModeDecision,
    employee_evidence_snapshot,
    revision_evidence_code,
)
from .models import NormativeDocument, NormativeRevision, PublicationStatus


class EvidenceIntegrityStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"

    @property
    def label(self) -> str:
        return {
            self.VALID: "Целостность подтверждена",
            self.INVALID: "Целостность нарушена",
        }[self]


@dataclass(frozen=True, slots=True)
class EvidenceIntegrityResult:
    status: EvidenceIntegrityStatus
    message: str


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    if isinstance(value, list):
        return [_thaw_json(item) for item in value]
    return value


def _locked_actor(actor: Employee) -> Employee:
    locked = (
        Employee.objects.select_for_update()
        .select_related("user", "organization", "division", "position", "workplace")
        .get(pk=actor.pk)
    )
    if not locked.is_active:
        raise ValidationError("Недействующий сотрудник не может создавать evidence-записи.")
    return locked


def _validate_actor_organization(actor: Employee, organization: Organization) -> None:
    if actor.organization_id != organization.pk:
        raise ValidationError("Сотрудник относится к другой организации.")


def _published_revision(
    revision: NormativeRevision | None,
    *,
    organization: Organization | None,
    local_only: bool = False,
) -> NormativeRevision | None:
    if revision is None:
        return None
    locked = (
        NormativeRevision.objects.select_for_update()
        .select_related("document")
        .get(pk=revision.pk)
    )
    if locked.status != PublicationStatus.PUBLISHED or len(locked.digest) != 64:
        raise ValidationError(
            "Evidence-основанием может быть только опубликованная редакция с SHA-256."
        )
    document = locked.document
    if local_only:
        if document.scope != NormativeDocument.Scope.LOCAL:
            raise ValidationError(
                "Локальным основанием может быть только локальный документ организации."
            )
        if organization is None or document.organization_id != organization.pk:
            raise ValidationError("Локальный акт относится к другой организации.")
    else:
        if document.scope == NormativeDocument.Scope.LOCAL:
            raise ValidationError(
                "Локальный акт должен храниться отдельно от нормативной редакции-основания."
            )
        if document.organization_id not in (None, getattr(organization, "pk", None)):
            raise ValidationError("Нормативная редакция недоступна выбранной организации.")
    return locked


def _validate_personal_session(*, actor: Employee, user: Any) -> None:
    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied(
            "Для evidence-события требуется действующая персональная сессия."
        )
    if not getattr(user, "is_active", False):
        raise PermissionDenied(
            "Недействующая учётная запись не может подтверждать действие."
        )
    if actor.user_id != getattr(user, "pk", None):
        raise PermissionDenied(
            "Учётная запись не соответствует сотруднику, выполняющему действие."
        )


def _validate_confirmation(
    *,
    actor: Employee,
    user: Any,
    password: str,
    confirmation_method: EvidenceConfirmationMethod,
    requires_reauthentication: bool,
) -> None:
    if confirmation_method == EvidenceConfirmationMethod.SESSION_AUTH:
        _validate_personal_session(actor=actor, user=user)
        if requires_reauthentication:
            raise ValidationError(
                {
                    "confirmation_method": (
                        "Для re-auth-required события недостаточно текущей сессии."
                    )
                }
            )
        return
    if confirmation_method == EvidenceConfirmationMethod.PASSWORD_REAUTH:
        _validate_personal_session(actor=actor, user=user)
        if not requires_reauthentication:
            raise ValidationError(
                {
                    "requires_reauthentication": (
                        "PASSWORD_REAUTH требует явного re-auth requirement."
                    )
                }
            )
        if not password or not user.check_password(password):
            raise ValidationError({"password": "Неверный текущий пароль."})
        return
    if confirmation_method == EvidenceConfirmationMethod.DEMO_SEED:
        if not settings.DEBUG:
            raise PermissionDenied("DEMO_SEED доступен только в DEBUG-профиле.")
        return
    raise PermissionDenied(
        "LEGACY_MIGRATION создаётся только контролируемым migration/backfill-контуром."
    )


def _decision_canonical(record: LegalModeDecision) -> tuple[str, str]:
    canonical = canonical_json(record.canonical_payload())
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _event_canonical(record: EvidenceEvent) -> tuple[str, str]:
    canonical = canonical_json(record.canonical_payload())
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@transaction.atomic
def record_legal_mode_decision(
    *,
    actor: Employee,
    code: str,
    module_id: str,
    subject_label: str,
    product_target_mode: ProductTargetMode,
    source_ids: tuple[str, ...],
    organization: Organization | None = None,
    proven_legal_mode: ProvenLegalMode = ProvenLegalMode.VERIFY,
    normative_evidence_status: NormativeEvidenceStatus = NormativeEvidenceStatus.VERIFY,
    local_act_status: LocalActStatus = LocalActStatus.VERIFY,
    normative_basis_revision: NormativeRevision | None = None,
    local_act_revision: NormativeRevision | None = None,
    decision_basis: str = "",
    supersedes: LegalModeDecision | None = None,
) -> LegalModeDecision:
    locked_actor = _locked_actor(actor)
    if organization is not None:
        _validate_actor_organization(locked_actor, organization)

    normative_basis = _published_revision(
        normative_basis_revision,
        organization=organization,
    )
    local_basis = _published_revision(
        local_act_revision,
        organization=organization,
        local_only=True,
    )
    normative_code = revision_evidence_code(normative_basis)
    local_code = revision_evidence_code(local_basis)

    if (
        normative_evidence_status == NormativeEvidenceStatus.CONFIRMED
        and normative_basis is None
    ):
        raise ValidationError(
            {
                "normative_basis_revision": (
                    "Статус CONFIRMED требует опубликованной нормативной редакции."
                )
            }
        )
    if local_act_status == LocalActStatus.CONFIRMED and local_basis is None:
        raise ValidationError(
            {
                "local_act_revision": (
                    "Статус CONFIRMED требует опубликованной редакции локального акта."
                )
            }
        )
    if local_act_status == LocalActStatus.NOT_REQUIRED and local_basis is not None:
        raise ValidationError(
            {
                "local_act_revision": (
                    "При NOT_REQUIRED локальный акт не связывается с решением."
                )
            }
        )

    contract = LegalModeDecisionContract(
        code=code,
        module_id=module_id,
        subject_label=subject_label,
        product_target_mode=product_target_mode,
        source_ids=source_ids,
        proven_legal_mode=proven_legal_mode,
        normative_evidence_status=normative_evidence_status,
        local_act_status=local_act_status,
        basis_revision_code=normative_code,
        decision_basis=decision_basis,
    )

    locked_supersedes = None
    if supersedes is not None:
        locked_supersedes = LegalModeDecision.objects.select_for_update().get(
            pk=supersedes.pk
        )
        if locked_supersedes.code != contract.code:
            raise ValidationError(
                {"supersedes": "Можно заменить только решение с тем же кодом."}
            )
        if locked_supersedes.organization_id != getattr(organization, "pk", None):
            raise ValidationError(
                {"supersedes": "Заменяемое решение относится к другой области."}
            )
        if locked_supersedes.superseded_by.exists():
            raise ValidationError(
                {"supersedes": "Решение уже заменено более новой записью."}
            )

    record = LegalModeDecision(
        organization=organization,
        code=contract.code,
        module_id=contract.module_id,
        subject_label=contract.subject_label,
        product_target_mode=contract.product_target_mode.value,
        proven_legal_mode=contract.proven_legal_mode.value,
        normative_evidence_status=contract.normative_evidence_status.value,
        local_act_status=contract.local_act_status.value,
        normative_basis_revision=normative_basis,
        normative_basis_code=normative_code,
        local_act_revision=local_basis,
        local_act_revision_code=local_code,
        source_ids=list(contract.source_ids),
        decision_basis=contract.decision_basis,
        decision_maker=locked_actor,
        decision_maker_snapshot=employee_evidence_snapshot(locked_actor),
        decided_at=timezone.now(),
        supersedes=locked_supersedes,
    )
    record.canonical_json, record.digest = _decision_canonical(record)
    record.save()
    return record


def _same_idempotent_request(
    existing: EvidenceEvent,
    *,
    event_type: EvidenceEventType,
    subject_type: str,
    subject_id: str,
    actor: Employee,
    confirmation_method: EvidenceConfirmationMethod,
    requires_reauthentication: bool,
    payload: dict[str, Any],
    source_ids: tuple[str, ...],
    normative_basis: NormativeRevision | None,
    corrects_event: EvidenceEvent | None,
) -> bool:
    return (
        existing.event_type == event_type.value
        and existing.subject_type == subject_type.strip().lower()
        and existing.subject_id == subject_id.strip()
        and existing.actor_id == actor.pk
        and existing.confirmation_method == confirmation_method.value
        and existing.requires_reauthentication == requires_reauthentication
        and existing.payload == payload
        and existing.source_ids == sorted(set(source_ids))
        and existing.normative_basis_revision_id == getattr(normative_basis, "pk", None)
        and existing.corrects_event_id == getattr(corrects_event, "pk", None)
    )


def _existing_for_correlation(
    *,
    organization: Organization,
    correlation_id: str,
) -> EvidenceEvent | None:
    if not correlation_id:
        return None
    return EvidenceEvent.objects.filter(
        organization=organization,
        correlation_id=correlation_id,
    ).first()


def _persist_event(
    *,
    contract: EvidenceEventContract,
    actor: Employee,
    organization: Organization,
    normative_basis: NormativeRevision | None,
    document_signature_id: int | None = None,
    corrects_event: EvidenceEvent | None = None,
) -> EvidenceEvent:
    record = EvidenceEvent(
        organization=organization,
        event_type=contract.event_type.value,
        subject_type=contract.subject_type,
        subject_id=contract.subject_id,
        actor=actor,
        actor_snapshot=_thaw_json(contract.actor_snapshot),
        occurred_at=contract.occurred_at,
        confirmation_method=contract.confirmation_method.value,
        requires_reauthentication=contract.requires_reauthentication,
        normative_basis_revision=normative_basis,
        normative_basis_code=contract.basis_revision_code,
        source_ids=list(contract.source_ids),
        correlation_id=contract.correlation_id,
        payload=_thaw_json(contract.payload),
        document_signature_id=document_signature_id,
        corrects_event=corrects_event,
    )
    record.canonical_json, record.digest = _event_canonical(record)
    try:
        record.save()
    except IntegrityError as error:
        if contract.correlation_id:
            existing = _existing_for_correlation(
                organization=organization,
                correlation_id=contract.correlation_id,
            )
            if existing is not None:
                return existing
        raise ValidationError(
            "Evidence-событие с такими уникальными реквизитами уже существует."
        ) from error
    return record


@transaction.atomic
def record_evidence_event(
    *,
    actor: Employee,
    user: Any,
    event_type: EvidenceEventType,
    subject_type: str,
    subject_id: str,
    payload: dict[str, Any],
    source_ids: tuple[str, ...],
    confirmation_method: EvidenceConfirmationMethod = EvidenceConfirmationMethod.SESSION_AUTH,
    requires_reauthentication: bool = False,
    password: str = "",
    normative_basis_revision: NormativeRevision | None = None,
    correlation_id: str = "",
    corrects_event: EvidenceEvent | None = None,
) -> EvidenceEvent:
    event_type = EvidenceEventType(event_type)
    if event_type == EvidenceEventType.SIGNATURE:
        raise ValidationError(
            "SIGNATURE создаётся только из существующего immutable DocumentSignature."
        )

    locked_actor = _locked_actor(actor)
    organization = locked_actor.organization
    confirmation_method = EvidenceConfirmationMethod(confirmation_method)
    _validate_confirmation(
        actor=locked_actor,
        user=user,
        password=password,
        confirmation_method=confirmation_method,
        requires_reauthentication=requires_reauthentication,
    )
    normative_basis = _published_revision(
        normative_basis_revision,
        organization=organization,
    )
    normalized_correlation = correlation_id.strip()
    locked_correction = None
    if corrects_event is not None:
        locked_correction = EvidenceEvent.objects.select_for_update().get(
            pk=corrects_event.pk
        )

    contract = EvidenceEventContract(
        event_type=event_type,
        subject_type=subject_type,
        subject_id=subject_id,
        actor_employee_id=locked_actor.pk,
        actor_snapshot=employee_evidence_snapshot(locked_actor),
        occurred_at=timezone.now(),
        confirmation_method=confirmation_method,
        requires_reauthentication=requires_reauthentication,
        payload=payload,
        source_ids=source_ids,
        basis_revision_code=revision_evidence_code(normative_basis),
        correlation_id=normalized_correlation,
    )
    existing = _existing_for_correlation(
        organization=organization,
        correlation_id=normalized_correlation,
    )
    if existing is not None:
        if _same_idempotent_request(
            existing,
            event_type=contract.event_type,
            subject_type=contract.subject_type,
            subject_id=contract.subject_id,
            actor=locked_actor,
            confirmation_method=contract.confirmation_method,
            requires_reauthentication=contract.requires_reauthentication,
            payload=_thaw_json(contract.payload),
            source_ids=contract.source_ids,
            normative_basis=normative_basis,
            corrects_event=locked_correction,
        ):
            return existing
        raise ValidationError(
            {
                "correlation_id": (
                    "Корреляционный идентификатор уже использован другим событием."
                )
            }
        )

    return _persist_event(
        contract=contract,
        actor=locked_actor,
        organization=organization,
        normative_basis=normative_basis,
        corrects_event=locked_correction,
    )


@transaction.atomic
def record_document_signature_evidence(
    *,
    signature: DocumentSignature,
    source_ids: tuple[str, ...] = ("SRC-SYSTEM-DOCUMENT-SIGNATURE",),
    normative_basis_revision: NormativeRevision | None = None,
) -> EvidenceEvent | None:
    locked_signature = (
        DocumentSignature.objects.select_related(
            "snapshot__document__organization",
            "employee__user",
            "employee__organization",
            "employee__division",
            "employee__position",
            "employee__workplace",
        )
        .get(pk=signature.pk)
    )
    if locked_signature.employee_id is None:
        return None
    existing = EvidenceEvent.objects.filter(
        event_type=EvidenceEventType.SIGNATURE.value,
        document_signature_id=locked_signature.pk,
    ).first()
    if existing is not None:
        return existing

    actor = locked_signature.employee
    organization = locked_signature.snapshot.document.organization
    _validate_actor_organization(actor, organization)
    normative_basis = _published_revision(
        normative_basis_revision,
        organization=organization,
    )
    method = EvidenceConfirmationMethod(locked_signature.confirmation_method)
    contract = EvidenceEventContract(
        event_type=EvidenceEventType.SIGNATURE,
        subject_type="document_signature",
        subject_id=str(locked_signature.pk),
        actor_employee_id=actor.pk,
        actor_snapshot=employee_evidence_snapshot(actor),
        occurred_at=locked_signature.signed_at,
        confirmation_method=method,
        requires_reauthentication=(
            method == EvidenceConfirmationMethod.PASSWORD_REAUTH
        ),
        payload={
            "snapshot_digest": locked_signature.snapshot.digest,
            "purpose": locked_signature.purpose,
            "signature_checksum": locked_signature.checksum,
        },
        source_ids=source_ids,
        basis_revision_code=revision_evidence_code(normative_basis),
        correlation_id=f"document-signature:{locked_signature.pk}",
    )
    return _persist_event(
        contract=contract,
        actor=actor,
        organization=organization,
        normative_basis=normative_basis,
        document_signature_id=locked_signature.pk,
    )


def verify_legal_mode_decision_integrity(
    decision: LegalModeDecision,
) -> EvidenceIntegrityResult:
    try:
        expected = canonical_json(decision.canonical_payload())
        stored = json.loads(decision.canonical_json)
    except (TypeError, ValueError, ValidationError):
        return EvidenceIntegrityResult(
            EvidenceIntegrityStatus.INVALID,
            "Канонический снимок решения повреждён или не соответствует контракту.",
        )
    digest = hashlib.sha256(decision.canonical_json.encode("utf-8")).hexdigest()
    if decision.hash_algorithm != "SHA-256" or digest != decision.digest:
        return EvidenceIntegrityResult(
            EvidenceIntegrityStatus.INVALID,
            "Контрольная сумма решения не совпадает.",
        )
    if stored != json.loads(expected):
        return EvidenceIntegrityResult(
            EvidenceIntegrityStatus.INVALID,
            "Текущие поля решения отличаются от канонического снимка.",
        )
    return EvidenceIntegrityResult(
        EvidenceIntegrityStatus.VALID,
        "Канонический снимок и SHA-256 решения согласованы.",
    )


def verify_evidence_event_integrity(event: EvidenceEvent) -> EvidenceIntegrityResult:
    try:
        expected = canonical_json(event.canonical_payload())
        stored = json.loads(event.canonical_json)
    except (TypeError, ValueError, ValidationError):
        return EvidenceIntegrityResult(
            EvidenceIntegrityStatus.INVALID,
            "Канонический снимок события повреждён или не соответствует контракту.",
        )
    digest = hashlib.sha256(event.canonical_json.encode("utf-8")).hexdigest()
    if event.hash_algorithm != "SHA-256" or digest != event.digest:
        return EvidenceIntegrityResult(
            EvidenceIntegrityStatus.INVALID,
            "Контрольная сумма evidence-события не совпадает.",
        )
    if stored != json.loads(expected):
        return EvidenceIntegrityResult(
            EvidenceIntegrityStatus.INVALID,
            "Текущие поля события отличаются от канонического снимка.",
        )
    if event.event_type == EvidenceEventType.SIGNATURE.value:
        try:
            signature = DocumentSignature.objects.select_related("snapshot").get(
                pk=event.document_signature_id
            )
        except DocumentSignature.DoesNotExist:
            return EvidenceIntegrityResult(
                EvidenceIntegrityStatus.INVALID,
                "Связанное системное подтверждение документа отсутствует.",
            )
        if (
            event.payload.get("snapshot_digest") != signature.snapshot.digest
            or event.payload.get("signature_checksum") != signature.checksum
        ):
            return EvidenceIntegrityResult(
                EvidenceIntegrityStatus.INVALID,
                "Evidence-событие не совпадает со связанным DocumentSignature.",
            )
    return EvidenceIntegrityResult(
        EvidenceIntegrityStatus.VALID,
        "Канонический снимок и SHA-256 evidence-события согласованы.",
    )


def visible_legal_mode_decisions(
    employee: Employee,
) -> QuerySet[LegalModeDecision]:
    return LegalModeDecision.objects.filter(
        Q(organization__isnull=True) | Q(organization=employee.organization)
    ).select_related(
        "organization",
        "decision_maker",
        "normative_basis_revision__document",
        "local_act_revision__document",
        "supersedes",
    )


def visible_evidence_events(employee: Employee) -> QuerySet[EvidenceEvent]:
    return EvidenceEvent.objects.filter(
        organization=employee.organization
    ).select_related(
        "actor",
        "normative_basis_revision__document",
        "corrects_event",
    )
