from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime
from typing import Any

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.equipment.models import EquipmentAsset
from apps.equipment.services import dispatcher_name_on
from apps.operational_documents.models import (
    OperationalDocumentRecord,
    OperationalDocumentRecordRevision,
    OperationalDocumentType,
    OperationalDocumentTypeRevision,
    SchemaPublicationStatus,
)
from apps.operational_documents.services import (
    canonical_json,
    create_record,
    current_published_revision,
    normalize_field_definitions,
    normalize_participant_role_definitions,
    normalize_status_definitions,
    normalize_transition_definitions,
    publish_type_revision,
    sha256_text,
    transition_record,
    update_record,
)
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee, Workplace

from .constants import (
    DEADLINE_EXTENSION_TEXT,
    DOCUMENT_TYPE_CODE,
    DOCUMENT_TYPE_NAME,
    DOCUMENT_TYPE_SHORT_NAME,
    FIELD_DEFINITIONS,
    FIELD_DEFECT_DESCRIPTION,
    FIELD_DETECTED_AT,
    FIELD_ELIMINATION_DEADLINE,
    FIELD_RESOLUTION_WORK_SUMMARY,
    FIELD_RESOLVED_AT,
    NUMBER_PREFIX,
    NUMBER_WIDTH,
    PARTICIPANT_ROLE_DEFINITIONS,
    ROLE_DISCOVERED_BY,
    ROLE_OPERATIONAL_ACKNOWLEDGER,
    ROLE_OPERATIONS_RESPONSIBLE,
    ROLE_RESOLUTION_RESPONSIBLE,
    SOURCE_APPENDIX,
    SOURCE_DOCUMENT,
    SOURCE_SECTION,
    STATUS_CLOSED,
    STATUS_IN_PROGRESS,
    STATUS_REGISTERED,
    STATUS_RESOLVED,
    STATUS_DEFINITIONS,
    TRANSITION_ASSIGN_DEADLINE,
    TRANSITION_CLOSE,
    TRANSITION_CONFIRM_RESOLUTION,
    TRANSITION_DEFINITIONS,
)
from .models import (
    DefectActionCode,
    EquipmentDefectActionEvidence,
    EquipmentDefectContext,
    EquipmentDefectOperationalLogLink,
    EquipmentDefectVolume,
)


SOURCE_DESCRIPTION = (
    "Source-bound форма по "
    f"{SOURCE_DOCUMENT}, раздел {SOURCE_SECTION}, приложение № {SOURCE_APPENDIX}. "
    "Электронный справочно-контрольный и демонстрационный контур с печатным "
    "представлением утверждённой бумажной формы."
)


def _expected_contract() -> dict[str, Any]:
    statuses = normalize_status_definitions(STATUS_DEFINITIONS)
    return {
        "fields": normalize_field_definitions(FIELD_DEFINITIONS),
        "statuses": statuses,
        "transitions": normalize_transition_definitions(TRANSITION_DEFINITIONS, statuses),
        "roles": normalize_participant_role_definitions(PARTICIPANT_ROLE_DEFINITIONS),
    }


def _validate_installed_revision(revision: OperationalDocumentTypeRevision) -> None:
    expected = _expected_contract()
    mismatches: list[str] = []
    if revision.number_prefix != NUMBER_PREFIX:
        mismatches.append("префикс номера")
    if revision.number_width != NUMBER_WIDTH:
        mismatches.append("разрядность номера")
    if not revision.requires_workplace:
        mismatches.append("обязательность рабочего места")
    if revision.field_definitions != expected["fields"]:
        mismatches.append("поля")
    if revision.status_definitions != expected["statuses"]:
        mismatches.append("состояния")
    if revision.transition_definitions != expected["transitions"]:
        mismatches.append("переходы")
    if revision.participant_role_definitions != expected["roles"]:
        mismatches.append("роли участников")
    if mismatches:
        raise ValidationError(
            "Опубликованная форма журнала дефектов не соответствует приложению № 8: "
            + ", ".join(mismatches)
            + ". Опубликованная редакция не изменена автоматически."
        )


@transaction.atomic
def ensure_defect_document_type(actor: Employee) -> OperationalDocumentTypeRevision:
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может установить форму журнала.")

    try:
        document_type = OperationalDocumentType.objects.select_for_update().get(
            organization=actor.organization,
            code=DOCUMENT_TYPE_CODE,
        )
    except OperationalDocumentType.DoesNotExist:
        document_type = OperationalDocumentType.objects.create(
            organization=actor.organization,
            code=DOCUMENT_TYPE_CODE,
            name=DOCUMENT_TYPE_NAME,
            short_name=DOCUMENT_TYPE_SHORT_NAME,
            description=SOURCE_DESCRIPTION,
            created_by=actor,
        )
    else:
        if document_type.name != DOCUMENT_TYPE_NAME:
            raise ValidationError(
                "Системный код журнала дефектов уже занят типом с другим наименованием."
            )

    published = current_published_revision(document_type)
    if published is not None:
        _validate_installed_revision(published)
        return published

    revision_number = (
        document_type.revisions.aggregate(maximum=Max("revision_number"))["maximum"] or 0
    ) + 1
    revision = OperationalDocumentTypeRevision.objects.create(
        document_type=document_type,
        revision_number=revision_number,
        number_prefix=NUMBER_PREFIX,
        number_width=NUMBER_WIDTH,
        requires_workplace=True,
        field_definitions=FIELD_DEFINITIONS,
        status_definitions=STATUS_DEFINITIONS,
        transition_definitions=TRANSITION_DEFINITIONS,
        participant_role_definitions=PARTICIPANT_ROLE_DEFINITIONS,
        created_by=actor,
    )
    published = publish_type_revision(revision=revision, actor=actor)
    _validate_installed_revision(published)
    return published


def _aware(value: datetime) -> datetime:
    if timezone.is_naive(value):
        return timezone.make_aware(value, timezone.get_current_timezone())
    return value


def _stored_datetime(record: OperationalDocumentRecord, code: str) -> datetime | None:
    value = record.field_values.get(code, {}).get("value")
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return _aware(value)
    parsed = parse_datetime(str(value))
    if parsed is None:
        raise ValidationError(f"Сохранённое поле {code} не является датой и временем.")
    return _aware(parsed)


def _stored_text(record: OperationalDocumentRecord, code: str) -> str:
    value = record.field_values.get(code, {}).get("value")
    return "" if value is None else str(value)


def raw_field_values(record: OperationalDocumentRecord) -> dict[str, Any]:
    return {
        FIELD_DETECTED_AT: _stored_datetime(record, FIELD_DETECTED_AT),
        FIELD_DEFECT_DESCRIPTION: _stored_text(record, FIELD_DEFECT_DESCRIPTION),
        FIELD_ELIMINATION_DEADLINE: _stored_datetime(record, FIELD_ELIMINATION_DEADLINE),
        FIELD_RESOLVED_AT: _stored_datetime(record, FIELD_RESOLVED_AT),
        FIELD_RESOLUTION_WORK_SUMMARY: _stored_text(
            record,
            FIELD_RESOLUTION_WORK_SUMMARY,
        ),
    }


def participant_map(record: OperationalDocumentRecord) -> dict[str, list[Employee]]:
    result = {
        ROLE_DISCOVERED_BY: [],
        ROLE_OPERATIONS_RESPONSIBLE: [],
        ROLE_RESOLUTION_RESPONSIBLE: [],
        ROLE_OPERATIONAL_ACKNOWLEDGER: [],
    }
    for participant in record.participants.select_related("employee"):
        if participant.role_code in result:
            result[participant.role_code].append(participant.employee)
    return result


def participant_for_role(record: OperationalDocumentRecord, role_code: str):
    return record.participants.filter(role_code=role_code).order_by("pk").first()


def _preserved_equipment(record: OperationalDocumentRecord) -> list[EquipmentAsset]:
    return [link.equipment for link in record.equipment_links.select_related("equipment")]


def _preserved_documents(record: OperationalDocumentRecord) -> list[Any]:
    return [link.document for link in record.document_links.select_related("document")]


def _preserved_relations(record: OperationalDocumentRecord) -> list[OperationalDocumentRecord]:
    return [
        relation.target_record
        for relation in record.outgoing_relations.select_related("target_record")
    ]


def _locked_defect_record(record: OperationalDocumentRecord) -> OperationalDocumentRecord:
    locked = (
        OperationalDocumentRecord.objects.select_for_update()
        .select_related(
            "organization",
            "document_type",
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


def _update_core_record(
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
        equipment_assets=_preserved_equipment(record),
        documents=_preserved_documents(record),
        related_records=_preserved_relations(record),
        comment=comment,
    )


def _latest_revision(record: OperationalDocumentRecord) -> OperationalDocumentRecordRevision:
    revision = record.revisions.filter(revision_number=record.version).first()
    if revision is None:
        raise ValidationError("Для текущей версии записи отсутствует неизменяемая редакция.")
    return revision


def _append_action_evidence(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    action_code: str,
    comment: str = "",
    previous_deadline: datetime | None = None,
    new_deadline: datetime | None = None,
) -> EquipmentDefectActionEvidence:
    record.refresh_from_db()
    revision = _latest_revision(record)
    snapshot = {
        "schema": "eod.equipment-defect-action.v1",
        "source": {
            "document": SOURCE_DOCUMENT,
            "section": SOURCE_SECTION,
            "appendix": SOURCE_APPENDIX,
        },
        "record": {
            "public_id": str(record.public_id),
            "registration_number": record.registration_number,
            "version": record.version,
            "revision_sha256": revision.sha256,
            "status_code": record.status_code,
        },
        "action": {
            "code": action_code,
            "result": "CONFIRMED",
            "comment": comment.strip(),
            "previous_deadline": previous_deadline,
            "new_deadline": new_deadline,
        },
        "actor": {
            "public_id": str(actor.public_id),
            "full_name": actor.full_name,
            "position": actor.position.name,
            "division": actor.division.name,
        },
    }
    normalized_snapshot = __import__("json").loads(canonical_json(snapshot))
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


@transaction.atomic
def current_defect_volume(*, workplace: Workplace, actor: Employee) -> EquipmentDefectVolume:
    if workplace.organization_id != actor.organization_id:
        raise ValidationError("Рабочее место относится к другой организации.")
    volume = (
        EquipmentDefectVolume.objects.select_for_update()
        .filter(
            organization=actor.organization,
            workplace=workplace,
            accepts_new_records=True,
        )
        .first()
    )
    if volume is not None:
        return volume
    sequence_number = (
        EquipmentDefectVolume.objects.filter(
            organization=actor.organization,
            workplace=workplace,
        ).aggregate(maximum=Max("sequence_number"))["maximum"]
        or 0
    ) + 1
    return EquipmentDefectVolume.objects.create(
        organization=actor.organization,
        workplace=workplace,
        sequence_number=sequence_number,
        organization_name_snapshot=actor.organization.name,
        workplace_name_snapshot=workplace.name,
        division_name_snapshot=workplace.division.name if workplace.division_id else "",
        started_on=timezone.localdate(),
        accepts_new_records=True,
        created_by=actor,
    )


@transaction.atomic
def open_new_defect_volume(*, workplace: Workplace, actor: Employee) -> EquipmentDefectVolume:
    current = current_defect_volume(workplace=workplace, actor=actor)
    if not current.defect_contexts.exists():
        raise ValidationError("Новый том не открывается, пока текущий том не содержит записей.")
    current.accepts_new_records = False
    current.save(update_fields=("accepts_new_records",))
    return current_defect_volume(workplace=workplace, actor=actor)


def _close_completed_old_volumes(workplace: Workplace) -> None:
    volumes = EquipmentDefectVolume.objects.select_for_update().filter(
        workplace=workplace,
        accepts_new_records=False,
        closed_on__isnull=True,
    )
    for volume in volumes:
        contexts = volume.defect_contexts.select_related("record")
        if not contexts.exists() or contexts.filter(record__status_is_terminal=False).exists():
            continue
        resolved_dates = [
            _stored_datetime(context.record, FIELD_RESOLVED_AT)
            for context in contexts
        ]
        resolved_dates = [value for value in resolved_dates if value is not None]
        if not resolved_dates:
            continue
        volume.closed_on = max(resolved_dates).date()
        volume.save(update_fields=("closed_on",))


@transaction.atomic
def register_defect(
    *,
    actor: Employee,
    workplace: Workplace,
    equipment: EquipmentAsset,
    discovered_by: Employee,
    detected_at: datetime,
    defect_description: str,
    operational_log_entry: OperationalLogEntry | None = None,
    presentation_key: str | None = None,
) -> OperationalDocumentRecord:
    detected_at = _aware(detected_at)
    description = defect_description.strip()
    if not description:
        raise ValidationError("Содержание дефекта обязательно.")
    if detected_at > timezone.now():
        raise ValidationError("Дата обнаружения дефекта не может быть в будущем.")
    if workplace.organization_id != actor.organization_id:
        raise ValidationError("Рабочее место относится к другой организации.")
    if equipment.organization_id != actor.organization_id:
        raise ValidationError("Оборудование относится к другой организации.")
    if discovered_by.organization_id != actor.organization_id:
        raise ValidationError("Лицо, обнаружившее дефект, относится к другой организации.")
    if operational_log_entry is not None:
        if operational_log_entry.journal.organization_id != actor.organization_id:
            raise ValidationError("Запись оперативного журнала относится к другой организации.")
        if operational_log_entry.journal.workplace_id != workplace.id:
            raise ValidationError("Запись оперативного журнала относится к другому рабочему месту.")

    revision = ensure_defect_document_type(actor)
    volume = current_defect_volume(workplace=workplace, actor=actor)
    dispatcher_name = dispatcher_name_on(equipment, detected_at.date())
    record = create_record(
        revision=revision,
        actor=actor,
        title=f"{dispatcher_name} — {description[:220]}",
        summary=description,
        event_at=detected_at,
        workplace=workplace,
        field_values={
            FIELD_DETECTED_AT: detected_at,
            FIELD_DEFECT_DESCRIPTION: description,
            FIELD_ELIMINATION_DEADLINE: None,
            FIELD_RESOLVED_AT: None,
            FIELD_RESOLUTION_WORK_SUMMARY: "",
        },
        participant_map={ROLE_DISCOVERED_BY: [discovered_by]},
        equipment_assets=[equipment],
    )
    EquipmentDefectContext.objects.create(
        record=record,
        volume=volume,
        presentation_key=presentation_key,
    )
    if operational_log_entry is not None:
        EquipmentDefectOperationalLogLink.objects.create(
            record=record,
            operational_log_entry=operational_log_entry,
            entry_sequence_snapshot=operational_log_entry.sequence_number,
            entry_event_at_snapshot=operational_log_entry.event_at,
            entry_content_snapshot=operational_log_entry.content[:1200],
            entry_digest_snapshot=operational_log_entry.digest,
            created_by=actor,
        )
    _append_action_evidence(
        record=record,
        actor=actor,
        action_code=DefectActionCode.REGISTERED,
        comment="Дефект зарегистрирован оперативным персоналом.",
    )
    return record


@transaction.atomic
def confirm_deadline(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    responsible: Employee,
    deadline: datetime,
) -> OperationalDocumentRecord:
    locked = _locked_defect_record(record)
    if locked.status_code != STATUS_REGISTERED:
        raise ValidationError("Срок устанавливается только для зарегистрированного дефекта.")
    deadline = _aware(deadline)
    detected_at = _stored_datetime(locked, FIELD_DETECTED_AT)
    if detected_at is None or deadline < detected_at:
        raise ValidationError("Срок устранения не может быть раньше даты обнаружения.")
    if responsible.organization_id != locked.organization_id:
        raise ValidationError("Ответственный относится к другой организации.")

    values = raw_field_values(locked)
    values[FIELD_ELIMINATION_DEADLINE] = deadline
    participants = participant_map(locked)
    participants[ROLE_OPERATIONS_RESPONSIBLE] = [responsible]
    updated = _update_core_record(
        record=locked,
        actor=actor,
        values=values,
        participants=participants,
        comment="Установлен и подтверждён срок устранения дефекта.",
    )
    transitioned = transition_record(
        record=updated,
        actor=actor,
        transition_code=TRANSITION_ASSIGN_DEADLINE,
    )
    _append_action_evidence(
        record=transitioned,
        actor=actor,
        action_code=DefectActionCode.DEADLINE_CONFIRMED,
        new_deadline=deadline,
    )
    return transitioned


@transaction.atomic
def extend_deadline(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    new_deadline: datetime,
    reason: str,
) -> OperationalDocumentRecord:
    locked = _locked_defect_record(record)
    if locked.status_code != STATUS_IN_PROGRESS:
        raise ValidationError("Продлить срок можно только для дефекта в работе.")
    previous_deadline = _stored_datetime(locked, FIELD_ELIMINATION_DEADLINE)
    if previous_deadline is None:
        raise ValidationError("Нельзя продлить срок, который ещё не установлен.")
    new_deadline = _aware(new_deadline)
    if new_deadline <= previous_deadline:
        raise ValidationError("Новый срок должен быть позже прежнего.")
    normalized_reason = reason.strip()
    if not normalized_reason:
        raise ValidationError("Укажите причину или комментарий к продлению.")

    values = raw_field_values(locked)
    values[FIELD_ELIMINATION_DEADLINE] = new_deadline
    comment = (
        f"{DEADLINE_EXTENSION_TEXT}. Новый срок: "
        f"{timezone.localtime(new_deadline):%d.%m.%Y %H:%M}. "
        f"Причина: {normalized_reason}"
    )
    updated = _update_core_record(
        record=locked,
        actor=actor,
        values=values,
        participants=participant_map(locked),
        comment=comment,
    )
    _append_action_evidence(
        record=updated,
        actor=actor,
        action_code=DefectActionCode.DEADLINE_EXTENDED,
        comment=normalized_reason,
        previous_deadline=previous_deadline,
        new_deadline=new_deadline,
    )
    return updated


@transaction.atomic
def confirm_resolution(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
    responsible: Employee,
    resolved_at: datetime,
    work_summary: str,
) -> OperationalDocumentRecord:
    locked = _locked_defect_record(record)
    if locked.status_code != STATUS_IN_PROGRESS:
        raise ValidationError("Устранение фиксируется только для дефекта в работе.")
    resolved_at = _aware(resolved_at)
    detected_at = _stored_datetime(locked, FIELD_DETECTED_AT)
    if detected_at is None or resolved_at < detected_at:
        raise ValidationError("Дата устранения не может быть раньше даты обнаружения.")
    if resolved_at > timezone.now():
        raise ValidationError("Дата устранения не может быть в будущем.")
    normalized_summary = work_summary.strip()
    if not normalized_summary:
        raise ValidationError("Содержание выполненных работ обязательно.")
    if responsible.organization_id != locked.organization_id:
        raise ValidationError("Ответственный относится к другой организации.")

    values = raw_field_values(locked)
    values[FIELD_RESOLVED_AT] = resolved_at
    values[FIELD_RESOLUTION_WORK_SUMMARY] = normalized_summary
    participants = participant_map(locked)
    participants[ROLE_RESOLUTION_RESPONSIBLE] = [responsible]
    updated = _update_core_record(
        record=locked,
        actor=actor,
        values=values,
        participants=participants,
        comment="Зафиксированы дата и содержание выполненных работ по устранению дефекта.",
    )
    transitioned = transition_record(
        record=updated,
        actor=actor,
        transition_code=TRANSITION_CONFIRM_RESOLUTION,
    )
    _append_action_evidence(
        record=transitioned,
        actor=actor,
        action_code=DefectActionCode.RESOLUTION_CONFIRMED,
        comment=normalized_summary,
    )
    return transitioned


@transaction.atomic
def acknowledge_resolution(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
) -> OperationalDocumentRecord:
    locked = _locked_defect_record(record)
    if locked.status_code != STATUS_RESOLVED:
        raise ValidationError("Ознакомление доступно после подтверждения устранения.")
    if not actor.position.is_operational:
        raise ValidationError("Ознакомление выполняется оперативным персоналом.")
    participants = participant_map(locked)
    existing_ids = {
        employee.pk for employee in participants[ROLE_OPERATIONAL_ACKNOWLEDGER]
    }
    if actor.pk in existing_ids:
        raise ValidationError("Этот сотрудник уже ознакомился с записью.")
    participants[ROLE_OPERATIONAL_ACKNOWLEDGER].append(actor)
    updated = _update_core_record(
        record=locked,
        actor=actor,
        values=raw_field_values(locked),
        participants=participants,
        comment="Оперативный персонал ознакомился с записью об устранении дефекта.",
    )
    _append_action_evidence(
        record=updated,
        actor=actor,
        action_code=DefectActionCode.ACKNOWLEDGED,
    )
    return updated


@transaction.atomic
def close_defect(
    *,
    record: OperationalDocumentRecord,
    actor: Employee,
) -> OperationalDocumentRecord:
    locked = _locked_defect_record(record)
    if locked.status_code != STATUS_RESOLVED:
        raise ValidationError("Закрыть можно только устранённый дефект.")
    if not locked.equipment_defect_actions.filter(
        action_code=DefectActionCode.ACKNOWLEDGED
    ).exists():
        raise ValidationError("Перед закрытием требуется ознакомление оперативного персонала.")
    if not locked.participants.filter(
        role_code=ROLE_OPERATIONAL_ACKNOWLEDGER
    ).exists():
        raise ValidationError("В записи отсутствует ознакомившийся оперативный персонал.")

    transitioned = transition_record(
        record=locked,
        actor=actor,
        transition_code=TRANSITION_CLOSE,
    )
    _append_action_evidence(
        record=transitioned,
        actor=actor,
        action_code=DefectActionCode.CLOSED,
    )
    if transitioned.workplace_id:
        _close_completed_old_volumes(transitioned.workplace)
    return transitioned


def defect_field_display(record: OperationalDocumentRecord, code: str) -> str:
    return str(record.field_values.get(code, {}).get("display") or "")


def defect_field_value(record: OperationalDocumentRecord, code: str) -> Any:
    return record.field_values.get(code, {}).get("value")


def assert_terminal_lock(record: OperationalDocumentRecord) -> None:
    if record.status_code != STATUS_CLOSED or not record.status_is_terminal:
        raise ValidationError("Запись не находится в конечном состоянии.")


def installed_defect_revision_for(actor: Employee) -> OperationalDocumentTypeRevision:
    revision = ensure_defect_document_type(actor)
    if revision.status != SchemaPublicationStatus.PUBLISHED:
        raise ValidationError("Форма журнала дефектов не опубликована.")
    return revision
