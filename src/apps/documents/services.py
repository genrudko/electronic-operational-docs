from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.organizations.models import Employee
from apps.organizations.services import user_has_role

from .models import (
    AuditEvent,
    Document,
    DocumentLink,
    DocumentNumberSequence,
    DocumentType,
    DocumentVersion,
)


@dataclass(frozen=True, slots=True)
class RegistrationResult:
    document: Document
    version: DocumentVersion
    registration_number: str


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


@transaction.atomic
def register_document(*, document: Document, actor: Employee) -> RegistrationResult:
    locked = (
        Document.objects.select_for_update()
        .select_related("document_type", "organization", "current_version")
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
        },
    )
    return RegistrationResult(
        document=locked,
        version=version,
        registration_number=number,
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
