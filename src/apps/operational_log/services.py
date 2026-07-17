from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from datetime import UTC, date, datetime
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Max, Prefetch, QuerySet
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.equipment.services import dispatcher_name_on
from apps.organizations.models import Employee

from .models import (
    DraftRevisionAction,
    EntryForm,
    OperationalDraftEntry,
    OperationalDraftRevision,
    OperationalJournal,
    OperationalJournalSequence,
    OperationalLogAuditEvent,
    OperationalLogDocumentLink,
    OperationalLogEntry,
    OperationalLogEquipmentLink,
    OperationalShift,
    OperationalShiftMember,
    ShiftStatus,
)


def canonical_json(value: Any) -> str:
    def normalize(item: Any) -> Any:
        if isinstance(item, dict):
            return {str(key): normalize(child) for key, child in item.items()}
        if isinstance(item, (list, tuple)):
            return [normalize(child) for child in item]
        if isinstance(item, datetime):
            moment = item
            if timezone.is_naive(moment):
                moment = timezone.make_aware(moment, timezone.get_current_timezone())
            return (
                moment.astimezone(UTC)
                .isoformat(timespec="microseconds")
                .replace("+00:00", "Z")
            )
        if isinstance(item, date):
            return item.isoformat()
        if item is None or isinstance(item, (str, int, float, bool)):
            return item
        return str(item)

    return json.dumps(
        normalize(value),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_iso(value: datetime) -> str:
    moment = value
    if timezone.is_naive(moment):
        moment = timezone.make_aware(moment, timezone.get_current_timezone())
    return (
        moment.astimezone(UTC).isoformat(timespec="microseconds").replace("+00:00", "Z")
    )


def employee_for_user(user: Any) -> Employee | None:
    if user is None or not getattr(user, "is_authenticated", False):
        return None
    try:
        employee = user.employee_profile
    except (AttributeError, Employee.DoesNotExist):
        return None
    return employee if employee.is_active else None


def require_operational_employee(user: Any) -> Employee:
    employee = employee_for_user(user)
    if employee is None:
        raise PermissionDenied(
            "Для просмотра оперативного журнала нужен действующий профиль сотрудника."
        )
    return employee


def _aware_event_time(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def _unique_persisted(items: Iterable[Any], label: str) -> list[Any]:
    result: list[Any] = []
    seen: set[int] = set()
    for item in items:
        if item.pk is None:
            raise ValidationError(
                f"{label}: несохранённый объект нельзя связать с записью."
            )
        if item.pk in seen:
            raise ValidationError(f"{label}: один объект указан более одного раза.")
        seen.add(item.pk)
        result.append(item)
    return result


def _equipment_snapshot(equipment: EquipmentAsset, day: date) -> dict[str, Any]:
    return {
        "equipment_id": equipment.pk,
        "public_id": str(equipment.public_id),
        "code": equipment.code,
        "dispatcher_name": dispatcher_name_on(equipment, day),
        "site": equipment.site.short_name or equipment.site.name,
    }


def _document_snapshot(document: Document) -> dict[str, Any]:
    return {
        "document_id": document.pk,
        "public_id": str(document.public_id),
        "registration_number": document.registration_number,
        "title": document.title,
    }


def _entry_snapshot_payload(
    *,
    journal: OperationalJournal,
    sequence_number: int,
    event_at: datetime,
    registered_at: datetime,
    entry_form: str,
    type_code: str,
    type_title: str,
    content: str,
    typed_payload: dict[str, Any],
    author: Employee,
    equipment: list[dict[str, Any]],
    documents: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": "operational-log-entry.v1",
        "journal": {
            "id": journal.pk,
            "code": journal.code,
            "title": journal.title,
            "organization_id": journal.organization_id,
            "workplace_id": journal.workplace_id,
            "workplace": journal.workplace.name,
        },
        "entry": {
            "sequence_number": sequence_number,
            "event_at": utc_iso(event_at),
            "registered_at": utc_iso(registered_at),
            "entry_form": entry_form,
            "type_code": type_code,
            "type_title": type_title,
            "content": content,
            "typed_payload": typed_payload,
        },
        "author": {
            "employee_id": author.pk,
            "full_name": author.full_name,
            "position": author.position.name,
            "workplace": author.workplace.name if author.workplace_id else "",
        },
        "equipment": equipment,
        "documents": documents,
    }


@transaction.atomic
def register_entry(
    *,
    journal: OperationalJournal,
    actor: Employee,
    event_at: datetime,
    content: str,
    entry_form: str = EntryForm.FREE_TEXT,
    type_code: str = "",
    type_title: str = "",
    typed_payload: dict[str, Any] | None = None,
    equipment: Iterable[EquipmentAsset] = (),
    documents: Iterable[Document] = (),
) -> OperationalLogEntry:
    locked_journal = (
        OperationalJournal.objects.select_for_update()
        .select_related("organization", "workplace")
        .get(pk=journal.pk)
    )
    if not locked_journal.is_active:
        raise ValidationError("Нельзя зарегистрировать запись в недействующем журнале.")
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может регистрировать записи.")
    if actor.organization_id != locked_journal.organization_id:
        raise PermissionDenied(
            "Нельзя регистрировать запись в журнале другой организации."
        )

    normalized_event_at = _aware_event_time(event_at)
    registered_at = timezone.now()
    if normalized_event_at > registered_at:
        raise ValidationError({"event_at": "Время события не может быть в будущем."})

    normalized_content = content.strip()
    normalized_code = type_code.strip().lower()
    normalized_title = type_title.strip()
    normalized_payload = dict(typed_payload or {})
    if not normalized_content:
        raise ValidationError({"content": "Содержание записи обязательно."})
    if entry_form == EntryForm.FREE_TEXT:
        if normalized_code or normalized_title or normalized_payload:
            raise ValidationError(
                "Свободная запись не должна содержать типизированные реквизиты."
            )
    elif entry_form == EntryForm.TYPED:
        if not normalized_code or not normalized_title:
            raise ValidationError(
                "Для типизированной записи требуются код и наименование типа."
            )
    else:
        raise ValidationError({"entry_form": "Неизвестная форма записи."})

    equipment_items = sorted(
        _unique_persisted(equipment, "Оборудование"),
        key=lambda item: item.pk,
    )
    document_items = sorted(
        _unique_persisted(documents, "Документы"),
        key=lambda item: item.pk,
    )
    for item in equipment_items:
        if item.organization_id != locked_journal.organization_id:
            raise ValidationError(
                "Связанное оборудование относится к другой организации."
            )
    for item in document_items:
        if item.organization_id != locked_journal.organization_id:
            raise ValidationError("Связанный документ относится к другой организации.")
        if item.status != Document.Status.REGISTERED:
            raise ValidationError(
                "В журнале можно ссылаться только на зарегистрированные документы."
            )

    OperationalJournalSequence.objects.get_or_create(journal=locked_journal)
    sequence = OperationalJournalSequence.objects.select_for_update().get(
        journal=locked_journal
    )
    sequence.last_value += 1
    sequence.save(update_fields=("last_value", "updated_at"))

    equipment_snapshots = [
        _equipment_snapshot(item, normalized_event_at.date())
        for item in equipment_items
    ]
    document_snapshots = [_document_snapshot(item) for item in document_items]
    snapshot = _entry_snapshot_payload(
        journal=locked_journal,
        sequence_number=sequence.last_value,
        event_at=normalized_event_at,
        registered_at=registered_at,
        entry_form=entry_form,
        type_code=normalized_code,
        type_title=normalized_title,
        content=normalized_content,
        typed_payload=normalized_payload,
        author=actor,
        equipment=equipment_snapshots,
        documents=document_snapshots,
    )
    digest = sha256_text(canonical_json(snapshot))
    entry = OperationalLogEntry.objects.create(
        journal=locked_journal,
        sequence_number=sequence.last_value,
        event_at=normalized_event_at,
        registered_at=registered_at,
        entry_form=entry_form,
        type_code=normalized_code,
        type_title=normalized_title,
        content=normalized_content,
        typed_payload=normalized_payload,
        author=actor,
        author_full_name_snapshot=actor.full_name,
        author_position_snapshot=actor.position.name,
        author_workplace_snapshot=actor.workplace.name if actor.workplace_id else "",
        digest=digest,
    )
    for item, item_snapshot in zip(equipment_items, equipment_snapshots, strict=True):
        OperationalLogEquipmentLink.objects.create(
            entry=entry,
            equipment=item,
            equipment_code_snapshot=item_snapshot["code"],
            dispatcher_name_snapshot=item_snapshot["dispatcher_name"],
            site_name_snapshot=item_snapshot["site"],
        )
    for item, item_snapshot in zip(document_items, document_snapshots, strict=True):
        OperationalLogDocumentLink.objects.create(
            entry=entry,
            document=item,
            registration_number_snapshot=item_snapshot["registration_number"],
            title_snapshot=item_snapshot["title"],
        )
    OperationalLogAuditEvent.objects.create(
        entry=entry,
        event_type=OperationalLogAuditEvent.EventType.ENTRY_REGISTERED,
        actor=actor,
        event_at=registered_at,
        snapshot=snapshot,
        digest=digest,
    )
    return entry


def entry_snapshot(entry: OperationalLogEntry) -> dict[str, Any]:
    equipment = [
        {
            "equipment_id": link.equipment_id,
            "public_id": str(link.equipment.public_id),
            "code": link.equipment_code_snapshot,
            "dispatcher_name": link.dispatcher_name_snapshot,
            "site": link.site_name_snapshot,
        }
        for link in entry.equipment_links.select_related("equipment").order_by(
            "equipment_id"
        )
    ]
    documents = [
        {
            "document_id": link.document_id,
            "public_id": str(link.document.public_id),
            "registration_number": link.registration_number_snapshot,
            "title": link.title_snapshot,
        }
        for link in entry.document_links.select_related("document").order_by(
            "document_id"
        )
    ]
    return {
        "schema_version": "operational-log-entry.v1",
        "journal": {
            "id": entry.journal_id,
            "code": entry.journal.code,
            "title": entry.journal.title,
            "organization_id": entry.journal.organization_id,
            "workplace_id": entry.journal.workplace_id,
            "workplace": entry.journal.workplace.name,
        },
        "entry": {
            "sequence_number": entry.sequence_number,
            "event_at": utc_iso(entry.event_at),
            "registered_at": utc_iso(entry.registered_at),
            "entry_form": entry.entry_form,
            "type_code": entry.type_code,
            "type_title": entry.type_title,
            "content": entry.content,
            "typed_payload": entry.typed_payload,
        },
        "author": {
            "employee_id": entry.author_id,
            "full_name": entry.author_full_name_snapshot,
            "position": entry.author_position_snapshot,
            "workplace": entry.author_workplace_snapshot,
        },
        "equipment": equipment,
        "documents": documents,
    }


def verify_entry_integrity(entry: OperationalLogEntry) -> bool:
    expected = sha256_text(canonical_json(entry_snapshot(entry)))
    if expected != entry.digest:
        raise ValidationError(
            "Контрольная сумма записи оперативного журнала не совпадает."
        )
    event = entry.audit_events.filter(
        event_type=OperationalLogAuditEvent.EventType.ENTRY_REGISTERED
    ).first()
    if (
        event is None
        or event.digest != entry.digest
        or event.snapshot != entry_snapshot(entry)
    ):
        raise ValidationError("Событие регистрации не соответствует снимку записи.")
    return True


def timeline_queryset(journal: OperationalJournal) -> QuerySet[OperationalLogEntry]:
    return (
        journal.entries.select_related("author", "journal", "journal__workplace")
        .prefetch_related(
            Prefetch(
                "equipment_links",
                queryset=OperationalLogEquipmentLink.objects.select_related(
                    "equipment"
                ),
            ),
            Prefetch(
                "document_links",
                queryset=OperationalLogDocumentLink.objects.select_related("document"),
            ),
        )
        .order_by("-sequence_number")
    )



class DraftConflictError(ValidationError):
    def __init__(self, current_entry: OperationalDraftEntry) -> None:
        self.current_entry = current_entry
        super().__init__(
            "Черновая запись была изменена в другой вкладке или на другом устройстве."
        )


ACTIVE_SHIFT_STATUSES = (
    ShiftStatus.OPEN,
    ShiftStatus.HANDOVER_PREPARATION,
)


def active_shift_for_journal(
    journal: OperationalJournal,
) -> OperationalShift | None:
    return (
        OperationalShift.objects.filter(
            journal=journal,
            status__in=ACTIVE_SHIFT_STATUSES,
        )
        .select_related(
            "journal",
            "journal__workplace",
            "opened_by",
            "opened_by__position",
        )
        .order_by("-planned_start_at", "-pk")
        .first()
    )


def _require_shift_actor(
    shift: OperationalShift,
    actor: Employee,
) -> None:
    if not actor.is_active:
        raise ValidationError(
            "Недействующий сотрудник не может работать с черновиком."
        )
    if actor.organization_id != shift.journal.organization_id:
        raise PermissionDenied(
            "Нельзя работать с черновиком смены другой организации."
        )
    if shift.status != ShiftStatus.OPEN:
        raise ValidationError(
            "Черновик можно менять только в открытой смене."
        )


def _draft_snapshot(
    entry: OperationalDraftEntry,
    actor: Employee,
) -> dict[str, Any]:
    return {
        "schema_version": "operational-draft-entry.v1",
        "shift": {
            "id": entry.shift_id,
            "public_id": str(entry.shift.public_id),
            "journal_id": entry.shift.journal_id,
            "journal_code": entry.shift.journal.code,
            "status": entry.shift.status,
        },
        "draft": {
            "id": entry.pk,
            "public_id": str(entry.public_id),
            "position": entry.position,
            "event_at": utc_iso(entry.event_at),
            "content": entry.content,
            "version": entry.version,
            "is_removed": entry.is_removed,
        },
        "actor": {
            "employee_id": actor.pk,
            "full_name": actor.full_name,
            "position": actor.position.name,
        },
    }


def _append_draft_revision(
    *,
    entry: OperationalDraftEntry,
    actor: Employee,
    action: str,
) -> OperationalDraftRevision:
    last_number = (
        entry.revisions.aggregate(value=Max("revision_number"))["value"]
        or 0
    )
    snapshot = _draft_snapshot(entry, actor)
    return OperationalDraftRevision.objects.create(
        entry=entry,
        revision_number=last_number + 1,
        action=action,
        snapshot=snapshot,
        digest=sha256_text(canonical_json(snapshot)),
        changed_by=actor,
    )


@transaction.atomic
def open_shift(
    *,
    journal: OperationalJournal,
    actor: Employee,
    planned_start_at: datetime,
    planned_end_at: datetime,
) -> OperationalShift:
    locked_journal = (
        OperationalJournal.objects.select_for_update()
        .select_related("organization", "workplace")
        .get(pk=journal.pk)
    )
    if not locked_journal.is_active:
        raise ValidationError(
            "Нельзя открыть смену для недействующего журнала."
        )
    if not actor.is_active:
        raise ValidationError(
            "Недействующий сотрудник не может открыть смену."
        )
    if actor.organization_id != locked_journal.organization_id:
        raise PermissionDenied(
            "Нельзя открыть смену в журнале другой организации."
        )
    if active_shift_for_journal(locked_journal) is not None:
        raise ValidationError(
            "Для этого журнала уже существует открытая смена."
        )

    start_at = _aware_event_time(planned_start_at)
    end_at = _aware_event_time(planned_end_at)
    if end_at <= start_at:
        raise ValidationError(
            {"planned_end_at": "Окончание должно быть позже начала."}
        )

    shift = OperationalShift.objects.create(
        journal=locked_journal,
        status=ShiftStatus.OPEN,
        planned_start_at=start_at,
        planned_end_at=end_at,
        opened_by=actor,
        opened_by_full_name_snapshot=actor.full_name,
        opened_by_position_snapshot=actor.position.name,
    )
    OperationalShiftMember.objects.create(
        shift=shift,
        employee=actor,
        employee_full_name_snapshot=actor.full_name,
        employee_position_snapshot=actor.position.name,
        is_shift_lead=True,
    )
    return shift


def draft_entries_queryset(
    shift: OperationalShift,
    *,
    include_removed: bool = False,
) -> QuerySet[OperationalDraftEntry]:
    queryset = (
        shift.draft_entries.select_related(
            "shift",
            "shift__journal",
            "created_by",
            "created_by__position",
            "updated_by",
            "updated_by__position",
        )
        .prefetch_related("revisions")
        .order_by("position", "pk")
    )
    if not include_removed:
        queryset = queryset.filter(is_removed=False)
    return queryset


@transaction.atomic
def create_draft_entry(
    *,
    shift: OperationalShift,
    actor: Employee,
    event_at: datetime | None = None,
    content: str = "",
) -> OperationalDraftEntry:
    locked_shift = (
        OperationalShift.objects.select_for_update()
        .select_related("journal")
        .get(pk=shift.pk)
    )
    _require_shift_actor(locked_shift, actor)
    last_position = (
        OperationalDraftEntry.objects.filter(
            shift=locked_shift,
            is_removed=False,
        ).aggregate(value=Max("position"))["value"]
        or 0
    )
    entry = OperationalDraftEntry.objects.create(
        shift=locked_shift,
        position=last_position + 10,
        event_at=_aware_event_time(event_at or timezone.now()),
        content=content,
        version=1,
        created_by=actor,
        updated_by=actor,
    )
    _append_draft_revision(
        entry=entry,
        actor=actor,
        action=DraftRevisionAction.CREATED,
    )
    return entry


@transaction.atomic
def update_draft_entry(
    *,
    entry: OperationalDraftEntry,
    actor: Employee,
    expected_version: int,
    event_at: datetime,
    content: str,
) -> OperationalDraftEntry:
    locked_entry = (
        OperationalDraftEntry.objects.select_for_update()
        .select_related(
            "shift",
            "shift__journal",
            "created_by",
            "updated_by",
        )
        .get(pk=entry.pk)
    )
    _require_shift_actor(locked_entry.shift, actor)
    if expected_version != locked_entry.version:
        raise DraftConflictError(locked_entry)

    normalized_event_at = _aware_event_time(event_at)
    normalized_content = content.replace("\r\n", "\n").replace(
        "\r",
        "\n",
    )
    if (
        normalized_event_at == locked_entry.event_at
        and normalized_content == locked_entry.content
    ):
        return locked_entry

    locked_entry.event_at = normalized_event_at
    locked_entry.content = normalized_content
    locked_entry.version += 1
    locked_entry.updated_by = actor
    locked_entry.save(
        update_fields=(
            "event_at",
            "content",
            "version",
            "updated_by",
            "updated_at",
        )
    )
    _append_draft_revision(
        entry=locked_entry,
        actor=actor,
        action=DraftRevisionAction.UPDATED,
    )
    return locked_entry


@transaction.atomic
def move_draft_entry(
    *,
    entry: OperationalDraftEntry,
    actor: Employee,
    direction: str,
) -> OperationalDraftEntry:
    locked_shift = (
        OperationalShift.objects.select_for_update()
        .select_related("journal")
        .get(pk=entry.shift_id)
    )
    _require_shift_actor(locked_shift, actor)
    items = list(
        OperationalDraftEntry.objects.select_for_update()
        .filter(shift=locked_shift, is_removed=False)
        .select_related("shift", "shift__journal")
        .order_by("position", "pk")
    )
    current = next(
        (item for item in items if item.pk == entry.pk),
        None,
    )
    if current is None:
        raise ValidationError(
            "Убранную запись нельзя перемещать."
        )
    if direction not in {"up", "down"}:
        raise ValidationError("Неизвестное направление перемещения.")

    index = items.index(current)
    target_index = index - 1 if direction == "up" else index + 1
    if target_index < 0 or target_index >= len(items):
        return current

    target = items[target_index]
    current.position, target.position = target.position, current.position
    for item in (current, target):
        item.version += 1
        item.updated_by = actor
        item.save(
            update_fields=(
                "position",
                "version",
                "updated_by",
                "updated_at",
            )
        )
        _append_draft_revision(
            entry=item,
            actor=actor,
            action=DraftRevisionAction.REORDERED,
        )
    return current


@transaction.atomic
def remove_draft_entry(
    *,
    entry: OperationalDraftEntry,
    actor: Employee,
) -> OperationalDraftEntry:
    locked_entry = (
        OperationalDraftEntry.objects.select_for_update()
        .select_related("shift", "shift__journal")
        .get(pk=entry.pk)
    )
    _require_shift_actor(locked_entry.shift, actor)
    if locked_entry.is_removed:
        return locked_entry
    locked_entry.is_removed = True
    locked_entry.version += 1
    locked_entry.updated_by = actor
    locked_entry.save(
        update_fields=(
            "is_removed",
            "version",
            "updated_by",
            "updated_at",
        )
    )
    _append_draft_revision(
        entry=locked_entry,
        actor=actor,
        action=DraftRevisionAction.REMOVED,
    )
    return locked_entry


@transaction.atomic
def restore_draft_entry(
    *,
    entry: OperationalDraftEntry,
    actor: Employee,
) -> OperationalDraftEntry:
    locked_entry = (
        OperationalDraftEntry.objects.select_for_update()
        .select_related("shift", "shift__journal")
        .get(pk=entry.pk)
    )
    _require_shift_actor(locked_entry.shift, actor)
    if not locked_entry.is_removed:
        return locked_entry
    last_position = (
        OperationalDraftEntry.objects.filter(
            shift=locked_entry.shift,
            is_removed=False,
        ).aggregate(value=Max("position"))["value"]
        or 0
    )
    locked_entry.is_removed = False
    locked_entry.position = last_position + 10
    locked_entry.version += 1
    locked_entry.updated_by = actor
    locked_entry.save(
        update_fields=(
            "is_removed",
            "position",
            "version",
            "updated_by",
            "updated_at",
        )
    )
    _append_draft_revision(
        entry=locked_entry,
        actor=actor,
        action=DraftRevisionAction.RESTORED,
    )
    return locked_entry
