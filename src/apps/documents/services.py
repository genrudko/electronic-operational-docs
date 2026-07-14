from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import Employee
from apps.organizations.services import get_effective_roles, user_has_role

from .models import (
    AuditEvent,
    Document,
    DocumentLink,
    DocumentNumberSequence,
    DocumentSignature,
    DocumentType,
    DocumentVersion,
    SignedSnapshot,
)


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    document: Document
    version: DocumentVersion
    registration_number: str
    snapshot: SignedSnapshot
    signature: DocumentSignature


def employee_for_user(user: Any) -> Employee | None:
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    try:
        employee = user.employee_profile
    except (AttributeError, Employee.DoesNotExist):
        return None
    return employee if employee.is_active else None


def user_can_use_documents(user: Any) -> bool:
    return user_has_role(user, "operator") or user_has_role(user, "shift_supervisor")


def require_document_employee(user: Any) -> Employee:
    employee = employee_for_user(user)
    if employee is None or not user_can_use_documents(user):
        raise PermissionDenied("У пользователя нет полномочий для работы с документами.")
    return employee


def _validate_actor(actor: Employee, organization_id: int) -> None:
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может выполнять документарные действия.")
    if actor.organization_id != organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")


def _audit(
    *,
    event_type: str,
    actor: Employee,
    document: Document,
    version: DocumentVersion | None = None,
    entity_type: str = "document",
    entity_id: str | None = None,
    payload: dict[str, Any] | None = None,
) -> AuditEvent:
    return AuditEvent.objects.create(
        organization=document.organization,
        event_type=event_type,
        actor_user=actor.user,
        actor_employee=actor,
        document=document,
        document_version=version,
        entity_type=entity_type,
        entity_id=entity_id or str(document.public_id),
        payload=payload or {},
    )


@transaction.atomic
def create_document_draft(
    *,
    document_type: DocumentType,
    actor: Employee,
    title: str,
    content: dict[str, Any],
    public_id: UUID | None = None,
) -> Document:
    _validate_actor(actor, document_type.organization_id)
    if not document_type.is_active:
        raise ValidationError("Нельзя создать документ недействующего типа.")
    normalized_title = title.strip()
    if not normalized_title:
        raise ValidationError({"title": "Заголовок обязателен."})
    if not isinstance(content, dict):
        raise ValidationError({"content": "Содержимое должно быть JSON-объектом."})

    document_kwargs: dict[str, Any] = {
        "organization": document_type.organization,
        "document_type": document_type,
        "title": normalized_title,
        "created_by": actor,
    }
    if public_id is not None:
        document_kwargs["public_id"] = public_id
    document = Document.objects.create(**document_kwargs)
    version = DocumentVersion.objects.create(
        document=document,
        version_number=1,
        title=normalized_title,
        content=content,
        created_by=actor,
    )
    document.current_version = version
    document.save(update_fields=("current_version", "updated_at"))
    _audit(
        event_type=AuditEvent.EventType.DOCUMENT_CREATED,
        actor=actor,
        document=document,
        version=version,
        payload={"version_number": version.version_number},
    )
    return document


@transaction.atomic
def update_document_draft(
    *,
    document: Document,
    actor: Employee,
    title: str,
    content: dict[str, Any],
) -> Document:
    locked = (
        Document.objects.select_for_update()
        .select_related("current_version", "organization")
        .get(pk=document.pk)
    )
    _validate_actor(actor, locked.organization_id)
    if locked.status != Document.Status.DRAFT:
        raise ValidationError("Редактировать можно только черновик.")
    if locked.current_version_id is None:
        raise ValidationError("У документа отсутствует текущая версия.")

    normalized_title = title.strip()
    if not normalized_title:
        raise ValidationError({"title": "Заголовок обязателен."})
    if not isinstance(content, dict):
        raise ValidationError({"content": "Содержимое должно быть JSON-объектом."})

    version = DocumentVersion.objects.select_for_update().get(pk=locked.current_version_id)
    locked.title = normalized_title
    locked.save(update_fields=("title", "updated_at"))
    version.title = normalized_title
    version.content = content
    version.save(update_fields=("title", "content", "updated_at"))
    _audit(
        event_type=AuditEvent.EventType.DRAFT_UPDATED,
        actor=actor,
        document=locked,
        version=version,
        payload={"version_number": version.version_number},
    )
    return locked


def _allocate_number(*, document_type: DocumentType, year: int) -> int:
    sequence, _ = DocumentNumberSequence.objects.select_for_update().get_or_create(
        organization=document_type.organization,
        document_type=document_type,
        year=year,
        defaults={"last_value": 0},
    )
    sequence.last_value += 1
    sequence.save(update_fields=("last_value", "updated_at"))
    return sequence.last_value


def _registration_number(document_type: DocumentType, year: int, sequence: int) -> str:
    return f"{document_type.number_prefix}-{year}-{sequence:0{document_type.number_width}d}"



class IntegrityStatus(StrEnum):
    VALID = "VALID"
    INVALID = "INVALID"
    LEGACY = "LEGACY"
    MISSING = "MISSING"


@dataclass(frozen=True, slots=True)
class IntegrityResult:
    status: IntegrityStatus
    message: str
    snapshot: SignedSnapshot | None = None
    signature: DocumentSignature | None = None


SNAPSHOT_SCHEMA = "eod.document.registration.v1"
SIGNATURE_SCHEMA = "eod.document.signature.v1"


def _json_safe(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, datetime):
        moment = value
        if timezone.is_naive(moment):
            moment = timezone.make_aware(moment, timezone.get_current_timezone())
        return moment.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def canonical_json(value: dict[str, Any]) -> str:
    return json.dumps(
        _json_safe(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _employee_snapshot(employee: Employee | None) -> dict[str, Any]:
    if employee is None:
        return {
            "employee_id": None,
            "personnel_number": "",
            "full_name": "",
            "position": "",
            "division": "",
            "workplace": "",
        }
    return {
        "employee_id": employee.pk,
        "personnel_number": employee.personnel_number,
        "full_name": employee.full_name,
        "position": employee.position.name if employee.position_id else "",
        "division": employee.division.name if employee.division_id else "",
        "workplace": employee.workplace.name if employee.workplace_id else "",
    }


def _effective_roles_snapshot(actor: Employee, day: date) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for effective in get_effective_roles(actor, day):
        assignment = effective.assignment
        source = effective.source_employee
        items.append(
            {
                "role_code": assignment.role.code,
                "role_name": assignment.role.name,
                "scope_code": assignment.scope.code if assignment.scope_id else "",
                "scope_name": assignment.scope.name if assignment.scope_id else "",
                "source_employee_id": source.pk,
                "source_employee_name": source.full_name,
                "is_substituted": effective.is_substituted,
                "substitution_id": effective.substitution.pk if effective.substitution else None,
            }
        )
    return sorted(
        items,
        key=lambda item: (
            item["role_code"],
            item["scope_code"],
            item["source_employee_id"] or 0,
            item["substitution_id"] or 0,
        ),
    )


def registration_confirmation_preview(actor: Employee) -> dict[str, Any]:
    return {
        "identity": _employee_snapshot(actor),
        "effective_roles": _effective_roles_snapshot(actor, timezone.localdate()),
    }


def _protected_document_payload(document: Document, version: DocumentVersion) -> dict[str, Any]:
    return {
        "document": {
            "id": document.pk,
            "public_id": str(document.public_id),
            "organization_id": document.organization_id,
            "document_type_id": document.document_type_id,
            "title": document.title,
            "status": document.status,
            "current_version_id": document.current_version_id,
            "registration_year": document.registration_year,
            "sequence_number": document.sequence_number,
            "registration_number": document.registration_number,
            "registered_at": document.registered_at,
            "registered_by_id": document.registered_by_id,
        },
        "version": {
            "id": version.pk,
            "document_id": version.document_id,
            "version_number": version.version_number,
            "status": version.status,
            "title": version.title,
            "content": version.content,
            "registered_at": version.registered_at,
            "registered_by_id": version.registered_by_id,
        },
    }


def _historical_context(document: Document, actor: Employee, roles: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "organization": {
            "id": document.organization_id,
            "code": document.organization.code,
            "name": document.organization.name,
            "short_name": document.organization.short_name,
        },
        "document_type": {
            "id": document.document_type_id,
            "code": document.document_type.code,
            "name": document.document_type.name,
            "number_prefix": document.document_type.number_prefix,
        },
        "created_by": _employee_snapshot(document.created_by),
        "registered_by": _employee_snapshot(actor),
        "effective_roles": roles,
    }


def _registration_snapshot_payload(
    document: Document,
    version: DocumentVersion,
    *,
    historical_context: dict[str, Any],
) -> dict[str, Any]:
    protected = _protected_document_payload(document, version)
    return {
        "schema": SNAPSHOT_SCHEMA,
        "purpose": SignedSnapshot.Purpose.REGISTRATION,
        **protected,
        "historical_context": historical_context,
    }


def _signature_checksum_payload(
    *,
    snapshot_digest: str,
    purpose: str,
    confirmation_method: str,
    user_id: int | None,
    employee_id: int | None,
    username_snapshot: str,
    full_name_snapshot: str,
    position_snapshot: str,
    division_snapshot: str,
    workplace_snapshot: str,
    roles_snapshot: list[dict[str, Any]],
    signed_at: datetime,
) -> dict[str, Any]:
    return {
        "schema": SIGNATURE_SCHEMA,
        "snapshot_digest": snapshot_digest,
        "purpose": purpose,
        "confirmation_method": confirmation_method,
        "user_id": user_id,
        "employee_id": employee_id,
        "username_snapshot": username_snapshot,
        "full_name_snapshot": full_name_snapshot,
        "position_snapshot": position_snapshot,
        "division_snapshot": division_snapshot,
        "workplace_snapshot": workplace_snapshot,
        "roles_snapshot": roles_snapshot,
        "signed_at": signed_at,
    }


def _create_registration_signature(
    *,
    document: Document,
    version: DocumentVersion,
    actor: Employee,
    confirmation_method: str,
    user: Any | None,
    signed_at: datetime,
) -> tuple[SignedSnapshot, DocumentSignature]:
    role_day = timezone.localtime(signed_at).date()
    roles = _effective_roles_snapshot(actor, role_day)
    identity = _employee_snapshot(actor)
    context = _historical_context(document, actor, roles)
    payload = _registration_snapshot_payload(
        document,
        version,
        historical_context=context,
    )
    canonical = canonical_json(payload)
    digest = sha256_text(canonical)
    snapshot = SignedSnapshot.objects.create(
        document=document,
        document_version=version,
        purpose=SignedSnapshot.Purpose.REGISTRATION,
        schema_version=SNAPSHOT_SCHEMA,
        canonical_json=canonical,
        hash_algorithm="SHA-256",
        digest=digest,
        created_at=signed_at,
    )

    username = getattr(user, "get_username", lambda: "")() if user is not None else ""
    checksum_payload = _signature_checksum_payload(
        snapshot_digest=digest,
        purpose=SignedSnapshot.Purpose.REGISTRATION,
        confirmation_method=confirmation_method,
        user_id=getattr(user, "pk", None),
        employee_id=actor.pk,
        username_snapshot=username,
        full_name_snapshot=identity["full_name"],
        position_snapshot=identity["position"],
        division_snapshot=identity["division"],
        workplace_snapshot=identity["workplace"],
        roles_snapshot=roles,
        signed_at=signed_at,
    )
    checksum = sha256_text(canonical_json(checksum_payload))
    signature = DocumentSignature.objects.create(
        snapshot=snapshot,
        purpose=SignedSnapshot.Purpose.REGISTRATION,
        confirmation_method=confirmation_method,
        user=user,
        employee=actor,
        username_snapshot=username,
        full_name_snapshot=identity["full_name"],
        position_snapshot=identity["position"],
        division_snapshot=identity["division"],
        workplace_snapshot=identity["workplace"],
        roles_snapshot=roles,
        signed_at=signed_at,
        checksum_algorithm="SHA-256",
        checksum=checksum,
    )
    _audit(
        event_type=AuditEvent.EventType.DOCUMENT_SIGNATURE_CREATED,
        actor=actor,
        document=document,
        version=version,
        entity_type="document_signature",
        entity_id=str(signature.pk),
        payload={
            "purpose": signature.purpose,
            "confirmation_method": signature.confirmation_method,
            "snapshot_digest": snapshot.digest,
            "signature_checksum": signature.checksum,
        },
    )
    return snapshot, signature


@transaction.atomic
def _register_document_core(
    *,
    document: Document,
    actor: Employee,
    confirmation_method: str,
    user: Any | None,
) -> RegistrationResult:
    locked = (
        Document.objects.select_for_update()
        .select_related(
            "document_type",
            "organization",
            "current_version",
            "created_by__position",
            "created_by__division",
            "created_by__workplace",
        )
        .get(pk=document.pk)
    )
    _validate_actor(actor, locked.organization_id)
    if locked.status != Document.Status.DRAFT:
        raise ValidationError("Документ уже зарегистрирован.")
    if locked.current_version_id is None:
        raise ValidationError("Нельзя зарегистрировать документ без версии.")

    version = DocumentVersion.objects.select_for_update().get(pk=locked.current_version_id)
    if version.status != DocumentVersion.Status.DRAFT:
        raise ValidationError("Текущая версия уже зафиксирована.")
    body = str(version.content.get("body", "")).strip()
    if not body:
        raise ValidationError("Нельзя зарегистрировать документ без содержимого.")

    registered_at = timezone.now()
    year = timezone.localtime(registered_at).year
    sequence = _allocate_number(document_type=locked.document_type, year=year)
    number = _registration_number(locked.document_type, year, sequence)

    version.status = DocumentVersion.Status.REGISTERED
    version.registered_at = registered_at
    version.registered_by = actor
    version.save(
        update_fields=(
            "status",
            "registered_at",
            "registered_by",
            "updated_at",
        )
    )

    locked.status = Document.Status.REGISTERED
    locked.registration_year = year
    locked.sequence_number = sequence
    locked.registration_number = number
    locked.registered_at = registered_at
    locked.registered_by = actor
    locked.save(
        update_fields=(
            "status",
            "registration_year",
            "sequence_number",
            "registration_number",
            "registered_at",
            "registered_by",
            "updated_at",
        )
    )

    snapshot, signature = _create_registration_signature(
        document=locked,
        version=version,
        actor=actor,
        confirmation_method=confirmation_method,
        user=user,
        signed_at=registered_at,
    )
    _audit(
        event_type=AuditEvent.EventType.DOCUMENT_REGISTERED,
        actor=actor,
        document=locked,
        version=version,
        payload={
            "registration_number": number,
            "registration_year": year,
            "sequence_number": sequence,
            "version_number": version.version_number,
            "confirmation_method": signature.confirmation_method,
            "snapshot_digest": snapshot.digest,
            "signature_checksum": signature.checksum,
        },
    )
    return RegistrationResult(
        document=locked,
        version=version,
        registration_number=number,
        snapshot=snapshot,
        signature=signature,
    )


def register_document_with_password(
    *,
    document: Document,
    actor: Employee,
    user: Any,
    password: str,
) -> RegistrationResult:
    if user is None or not getattr(user, "is_authenticated", False):
        raise PermissionDenied("Для регистрации требуется действующая персональная сессия.")
    if actor.user_id != getattr(user, "pk", None):
        raise PermissionDenied("Учётная запись не соответствует сотруднику, выполняющему действие.")
    if not getattr(user, "is_active", False):
        raise PermissionDenied("Недействующая учётная запись не может подтверждать документ.")
    if not password or not user.check_password(password):
        raise ValidationError({"password": "Неверный текущий пароль."})
    return _register_document_core(
        document=document,
        actor=actor,
        confirmation_method=DocumentSignature.ConfirmationMethod.PASSWORD_REAUTH,
        user=user,
    )


def register_demo_document(*, document: Document, actor: Employee) -> RegistrationResult:
    if not settings.DEBUG:
        raise PermissionDenied("Демонстрационная регистрация доступна только в DEBUG-профиле.")
    return _register_document_core(
        document=document,
        actor=actor,
        confirmation_method=DocumentSignature.ConfirmationMethod.DEMO_SEED,
        user=actor.user,
    )


def verify_document_integrity(document: Document) -> IntegrityResult:
    if document.status != Document.Status.REGISTERED or document.current_version_id is None:
        return IntegrityResult(
            status=IntegrityStatus.MISSING,
            message="Контроль целостности применяется к зарегистрированным версиям.",
        )
    try:
        snapshot = document.signed_snapshots.select_related("document_version").get(
            document_version_id=document.current_version_id,
            purpose=SignedSnapshot.Purpose.REGISTRATION,
        )
    except SignedSnapshot.DoesNotExist:
        return IntegrityResult(
            status=IntegrityStatus.MISSING,
            message="Для зарегистрированной версии отсутствует подписываемый снимок.",
        )
    try:
        signature = snapshot.signature
    except DocumentSignature.DoesNotExist:
        return IntegrityResult(
            status=IntegrityStatus.MISSING,
            message="Для подписываемого снимка отсутствует запись системного подтверждения.",
            snapshot=snapshot,
        )

    if snapshot.hash_algorithm != "SHA-256" or signature.checksum_algorithm != "SHA-256":
        return IntegrityResult(
            status=IntegrityStatus.INVALID,
            message="Обнаружен неподдерживаемый алгоритм контроля целостности.",
            snapshot=snapshot,
            signature=signature,
        )
    if sha256_text(snapshot.canonical_json) != snapshot.digest:
        return IntegrityResult(
            status=IntegrityStatus.INVALID,
            message="Контрольная сумма сохранённого снимка не совпадает.",
            snapshot=snapshot,
            signature=signature,
        )
    try:
        stored_payload = json.loads(snapshot.canonical_json)
    except (TypeError, ValueError):
        return IntegrityResult(
            status=IntegrityStatus.INVALID,
            message="Канонический снимок повреждён и не разбирается как JSON.",
            snapshot=snapshot,
            signature=signature,
        )
    if stored_payload.get("schema") != SNAPSHOT_SCHEMA:
        return IntegrityResult(
            status=IntegrityStatus.INVALID,
            message="Версия схемы снимка не поддерживается.",
            snapshot=snapshot,
            signature=signature,
        )

    version = DocumentVersion.objects.get(pk=document.current_version_id)
    current_protected = _json_safe(_protected_document_payload(document, version))
    stored_protected = {
        "document": stored_payload.get("document"),
        "version": stored_payload.get("version"),
    }
    if current_protected != stored_protected:
        return IntegrityResult(
            status=IntegrityStatus.INVALID,
            message="Текущее зарегистрированное содержимое отличается от подписанного снимка.",
            snapshot=snapshot,
            signature=signature,
        )

    checksum_payload = _signature_checksum_payload(
        snapshot_digest=snapshot.digest,
        purpose=signature.purpose,
        confirmation_method=signature.confirmation_method,
        user_id=signature.user_id,
        employee_id=signature.employee_id,
        username_snapshot=signature.username_snapshot,
        full_name_snapshot=signature.full_name_snapshot,
        position_snapshot=signature.position_snapshot,
        division_snapshot=signature.division_snapshot,
        workplace_snapshot=signature.workplace_snapshot,
        roles_snapshot=signature.roles_snapshot,
        signed_at=signature.signed_at,
    )
    if sha256_text(canonical_json(checksum_payload)) != signature.checksum:
        return IntegrityResult(
            status=IntegrityStatus.INVALID,
            message="Контрольная сумма записи системного подтверждения не совпадает.",
            snapshot=snapshot,
            signature=signature,
        )

    if signature.confirmation_method == DocumentSignature.ConfirmationMethod.LEGACY_MIGRATION:
        return IntegrityResult(
            status=IntegrityStatus.LEGACY,
            message=(
                "Документ существовал до Patch 004. Снимок создан при миграции без "
                "повторной аутентификации и не является имитацией подписи пользователя."
            ),
            snapshot=snapshot,
            signature=signature,
        )
    return IntegrityResult(
        status=IntegrityStatus.VALID,
        message="Снимок, системное подтверждение и зарегистрированное содержимое согласованы.",
        snapshot=snapshot,
        signature=signature,
    )


@transaction.atomic
def create_document_link(
    *,
    source_document: Document,
    target_document: Document,
    link_type: str,
    actor: Employee,
) -> DocumentLink:
    source = Document.objects.select_for_update().get(pk=source_document.pk)
    target = Document.objects.select_for_update().get(pk=target_document.pk)
    _validate_actor(actor, source.organization_id)
    if source.organization_id != target.organization_id:
        raise ValidationError("Связанные документы относятся к разным организациям.")
    if source.status != Document.Status.REGISTERED or target.status != Document.Status.REGISTERED:
        raise ValidationError("Связи можно создавать только между зарегистрированными документами.")

    link = DocumentLink.objects.create(
        source_document=source,
        target_document=target,
        link_type=link_type,
        created_by=actor,
    )
    _audit(
        event_type=AuditEvent.EventType.DOCUMENT_LINK_CREATED,
        actor=actor,
        document=source,
        entity_type="document_link",
        entity_id=str(link.pk),
        payload={
            "link_type": link.link_type,
            "target_document": str(target.public_id),
            "target_registration_number": target.registration_number,
        },
    )
    return link


def registration_year_for(day: date | None = None) -> int:
    return (day or timezone.localdate()).year
