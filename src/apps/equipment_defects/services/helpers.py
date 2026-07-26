from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.equipment.models import EquipmentAsset
from apps.operational_documents.models import (
    OperationalDocumentRecord,
    OperationalDocumentRecordRevision,
)
from apps.operational_documents.services import (
    canonical_json,
    sha256_text,
    update_record,
)
from apps.organizations.models import Employee

from ..constants import (
    DOCUMENT_TYPE_CODE,
    FIELD_DEFECT_DESCRIPTION,
    FIELD_DETECTED_AT,
    FIELD_ELIMINATION_DEADLINE,
    FIELD_RESOLUTION_WORK_SUMMARY,
    FIELD_RESOLVED_AT,
    ROLE_DISCOVERED_BY,
    ROLE_OPERATIONAL_ACKNOWLEDGER,
    ROLE_OPERATIONS_RESPONSIBLE,
    ROLE_RESOLUTION_RESPONSIBLE,
    SOURCE_APPENDIX,
    SOURCE_DOCUMENT,
    SOURCE_SECTION,
)
from ..models import EquipmentDefectActionEvidence, EquipmentDefectContext


def aware_datetime(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def stored_datetime(record: OperationalDocumentRecord, code: str) -> datetime | None:
    value = record.field_values.get(code, {}).get("value")
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return aware_datetime(value)
    parsed = parse_datetime(str(value))
    if parsed is None:
        raise ValidationError(f"Сохранённое поле {code} не является датой и временем.")
    return aware_datetime(parsed)


def stored_text(record: OperationalDocumentRecord, code: str) -> str:
    value = record.field_values.get(code, {}).get("value")
    return "" if value is None else str(value)


def raw_field_values(record: OperationalDocumentRecord) -> dict[str, Any]:
    return {
        FIELD_DETECTED_AT: stored_datetime(record, FIELD_DETECTED_AT),
        FIELD_DEFECT_DESCRIPTION: stored_text(record, FIELD_DEFECT_DESCRIPTION),
        FIELD_ELIMINATION_DEADLINE: stored_datetime(record, FIELD_ELIMINATION_DEADLINE),
        FIELD_RESOLVED_AT: stored_datetime(record, FIELD_RESOLVED_AT),
        FIELD_RESOLUTION_WORK_SUMMARY: stored_text(
            record,
            FIELD_RESOLUTION_WORK_SUMMARY,
        ),
    }


def participant_map(record: OperationalDocumentRecord) -> dict[str, list[Employee]]:
    result = {
        ROLE_DISCOVERED_BY: [],
        ROLE_OPERATIONAL_ACKNOWLEDGER: [],
        ROLE_OPERATIONS_RESPONSIBLE: [],
        ROLE_RESOLUTION_RESPONSIBLE: [],
    }
    for participant in record.participants.select_related("employee"):
        if participant.role_code in result:
            result[participant.role_code].append(participant.employee)
    return result


def participant_for_role(record: OperationalDocumentRecord, role_code: str):
    return record.participants.filter(role_code=role_code).order_by("pk").first()


def preserved_equipment(record: OperationalDocumentRecord) -> list[EquipmentAsset]:
    return [link.equipment for link in record.equipment_links.select_related("equipment")]


def preserved_documents(record: OperationalDocumentRecord) -> list[Any]:
    return [link.document for link in record.document_links.select_related("document")]


def preserved_relations(record: OperationalDocumentRecord) -> list[OperationalDocumentRecord]:
    return [
        relation.target_record
        for relation in record.outgoing_relations.select_related("target_record")
    ]


def locked_defect_record(record: OperationalDocumentRecord) -> OperationalDocumentRecord:
    locked = (
        OperationalDocumentRecord.objects.select_for_update()
        .select_related(
            "document_type",
            "organization",
            "schema_revision",
            "workplace",
        )
        .get(pk=record.pk)
    )
    if locked.document_type.code != DOCUMENT_TYPE_CODE:
        raise ValidationError("Запись не относится к журналу дефектов оборудования.")
    if not EquipmentDefectContext.objects.filter(record=locked).exists():
        raise ValidationError("Для записи отсутствует source-bound контекст журнала дефектов.")
    return locked


def update_core_record(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    values: Mapping[str, Any],
    participants: Mapping[str, Iterable[Employee]],
    comment: str,
) -> OperationalDocumentRecord:
    return update_record(
        record=record,
        actor=actor,
        title=record.title,
        summary=str(values.get(FIELD_DEFECT_DESCRIPTION) or record.summary),
        event_at=record.event_at,
        workplace=record.workplace,
        field_values=values,
        participant_map=participants,
        equipment_assets=preserved_equipment(record),
        documents=preserved_documents(record),
        related_records=preserved_relations(record),
        comment=comment,
    )


def latest_revision(record: OperationalDocumentRecord) -> OperationalDocumentRecordRevision:
    revision = record.revisions.filter(revision_number=record.version).first()
    if revision is None:
        raise ValidationError("Для текущей версии записи отсутствует неизменяемая редакция.")
    return revision


@transaction.atomic
def append_action_evidence(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    action_code: str,
    comment: str = "",
    previous_deadline: datetime | None = None,
    new_deadline: datetime | None = None,
) -> EquipmentDefectActionEvidence:
    record.refresh_from_db()
    revision = latest_revision(record)
    snapshot = {
        "schema": "eod.equipment-defect-action.v1",
        "source": {
            "appendix": SOURCE_APPENDIX,
            "document": SOURCE_DOCUMENT,
            "section": SOURCE_SECTION,
        },
        "record": {
            "public_id": str(record.public_id),
            "registration_number": record.registration_number,
            "revision_sha256": revision.sha256,
            "status_code": record.status_code,
            "version": record.version,
        },
        "action": {
            "code": action_code,
            "comment": comment.strip(),
            "new_deadline": new_deadline,
            "previous_deadline": previous_deadline,
            "result": "CONFIRMED",
        },
        "actor": {
            "division": actor.division.name,
            "full_name": actor.full_name,
            "position": actor.position.name,
            "public_id": str(actor.public_id),
        },
    }
    normalized_snapshot = json.loads(canonical_json(snapshot))
    digest = sha256_text(canonical_json(normalized_snapshot))
    return EquipmentDefectActionEvidence.objects.create(
        record=record,
        action_code=action_code,
        actor=actor,
        actor_full_name_snapshot=actor.full_name,
        actor_position_snapshot=actor.position.name,
        actor_division_snapshot=actor.division.name,
        record_version=record.version,
        record_revision=revision,
        previous_deadline=previous_deadline,
        new_deadline=new_deadline,
        result="CONFIRMED",
        comment=comment,
        canonical_snapshot=normalized_snapshot,
        sha256=digest,
    )


def defect_field_display(record: OperationalDocumentRecord, code: str) -> str:
    return str(record.field_values.get(code, {}).get("display") or "")


def defect_field_value(record: OperationalDocumentRecord, code: str) -> Any:
    return record.field_values.get(code, {}).get("value")


def assert_terminal_lock(record: OperationalDocumentRecord) -> None:
    if not record.status_is_terminal:
        raise ValidationError("Запись не находится в конечном состоянии.")
