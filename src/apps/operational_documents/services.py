from __future__ import annotations

import unicodedata
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Organization, Workplace

from . import _services_core as _core
from .models import (
    OperationalDocumentNumberSequence,
    OperationalDocumentRecord,
    OperationalDocumentTypeRevision,
    RecordRevisionAction,
    SchemaPublicationStatus,
)


def __getattr__(name: str) -> Any:
    return getattr(_core, name)


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(dir(_core)))


def can_administer_operational_document_types(user: Any) -> bool:
    return bool(getattr(user, "is_superuser", False))


def publish_type_revision(
    *,
    revision: OperationalDocumentTypeRevision,
    actor: Employee,
) -> OperationalDocumentTypeRevision:
    return _core.publish_type_revision(revision=revision, actor=actor)


def normalize_search_text(value: object) -> str:
    """Normalize text for database-independent Unicode substring search."""

    if value is None:
        return ""
    return unicodedata.normalize("NFKC", str(value)).casefold()


def _allocate_number(
    revision: OperationalDocumentTypeRevision,
    year: int,
) -> tuple[int, str]:
    organization_id = revision.document_type.organization_id
    Organization.objects.select_for_update().only("pk").get(pk=organization_id)
    sequence, _created = (
        OperationalDocumentNumberSequence.objects.select_for_update().get_or_create(
            document_type=revision.document_type,
            year=year,
            defaults={"last_value": 0},
        )
    )

    candidate = sequence.last_value
    while True:
        candidate += 1
        registration_number = _core._registration_number(revision, year, candidate)
        if not OperationalDocumentRecord.objects.filter(
            organization_id=organization_id,
            registration_number=registration_number,
        ).exists():
            sequence.last_value = candidate
            sequence.save(update_fields=("last_value", "updated_at"))
            return candidate, registration_number


@transaction.atomic
def create_record(
    *,
    revision: OperationalDocumentTypeRevision,
    actor: Employee,
    title: str,
    summary: str,
    event_at: datetime,
    workplace: Workplace | None,
    field_values: Mapping[str, Any],
    participant_map: Mapping[str, Iterable[Employee]],
    equipment_assets: Iterable[EquipmentAsset] = (),
    documents: Iterable[Document] = (),
    related_records: Iterable[OperationalDocumentRecord] = (),
) -> OperationalDocumentRecord:
    revision = (
        OperationalDocumentTypeRevision.objects.select_for_update()
        .select_related("document_type", "document_type__organization")
        .get(pk=revision.pk)
    )
    if revision.status != SchemaPublicationStatus.PUBLISHED:
        raise ValidationError("Запись можно создать только по опубликованной редакции типа.")
    if actor.organization_id != revision.document_type.organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")
    if workplace and workplace.organization_id != actor.organization_id:
        raise ValidationError("Рабочее место относится к другой организации.")
    if revision.requires_workplace and workplace is None:
        raise ValidationError({"workplace": "Для этого типа документа требуется рабочее место."})
    normalized_values = _core.normalize_field_values(revision, field_values)
    participants = _core._validate_participants(
        revision,
        actor.organization_id,
        participant_map,
    )
    equipment, linked_documents, linked_records = _core._validate_related_collections(
        organization_id=actor.organization_id,
        equipment_assets=equipment_assets,
        documents=documents,
        related_records=related_records,
    )
    initial_status = _core._initial_status(revision)
    moment = _core._aware(event_at)
    year = timezone.localtime(moment).year
    sequence_value, registration_number = _allocate_number(revision, year)
    creator_snapshot = _core._employee_snapshot(actor)
    record = OperationalDocumentRecord.objects.create(
        organization=actor.organization,
        document_type=revision.document_type,
        schema_revision=revision,
        sequence_year=year,
        sequence_value=sequence_value,
        registration_number=registration_number,
        title=title,
        summary=summary,
        workplace=workplace,
        workplace_name_snapshot=workplace.name if workplace else "",
        event_at=moment,
        status_code=str(initial_status["code"]),
        status_name_snapshot=str(initial_status["name"]),
        status_is_terminal=bool(initial_status.get("is_terminal")),
        field_values=normalized_values,
        created_by=actor,
        created_by_full_name_snapshot=creator_snapshot["full_name"],
        created_by_position_snapshot=creator_snapshot["position"],
        created_by_division_snapshot=creator_snapshot["division"],
        updated_by=actor,
        closed_at=timezone.now() if initial_status.get("is_terminal") else None,
    )
    _core._sync_participants(record, participants)
    _core._sync_equipment(record, equipment)
    _core._sync_documents(record, linked_documents)
    _core._sync_relations(record, linked_records, actor)
    record.search_text = _core._search_text(record)
    record.save(update_fields=("search_text", "updated_at"))
    revision_row = _core._append_record_revision(
        record=record,
        actor=actor,
        action=RecordRevisionAction.CREATED,
    )
    _core._audit(
        organization_id=actor.organization_id,
        actor=actor,
        event_type="RECORD_CREATED",
        entity_type="operational_document_record",
        entity_id=str(record.public_id),
        document_type=record.document_type,
        record=record,
        payload={
            "registration_number": record.registration_number,
            "revision_sha256": revision_row.sha256,
        },
    )
    return record


def update_record(*args: Any, **kwargs: Any) -> OperationalDocumentRecord:
    return _core.update_record(*args, **kwargs)


def transition_record(*args: Any, **kwargs: Any) -> OperationalDocumentRecord:
    return _core.transition_record(*args, **kwargs)


__all__ = sorted(
    {name for name in dir(_core) if not name.startswith("_")}
    | {
        "can_administer_operational_document_types",
        "create_record",
        "normalize_search_text",
        "publish_type_revision",
        "transition_record",
        "update_record",
    }
)
