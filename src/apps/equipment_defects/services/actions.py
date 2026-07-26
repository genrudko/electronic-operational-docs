from __future__ import annotations

from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from apps.equipment.models import EquipmentAsset
from apps.equipment.services import dispatcher_name_on
from apps.operational_documents.models import OperationalDocumentRecord
from apps.operational_documents.services import create_record, transition_record
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee, Workplace

from ..constants import (
    DEADLINE_EXTENSION_TEXT,
    FIELD_DEFECT_DESCRIPTION,
    FIELD_DETECTED_AT,
    FIELD_ELIMINATION_DEADLINE,
    FIELD_RESOLUTION_WORK_SUMMARY,
    FIELD_RESOLVED_AT,
    ROLE_DISCOVERED_BY,
    ROLE_OPERATIONAL_ACKNOWLEDGER,
    ROLE_OPERATIONS_RESPONSIBLE,
    ROLE_RESOLUTION_RESPONSIBLE,
    STATUS_IN_PROGRESS,
    STATUS_REGISTERED,
    STATUS_RESOLVED,
    TRANSITION_ASSIGN_DEADLINE,
    TRANSITION_CLOSE,
    TRANSITION_CONFIRM_RESOLUTION,
)
from ..models import (
    DefectActionCode,
    EquipmentDefectContext,
    EquipmentDefectOperationalLogLink,
)
from .helpers import (
    append_action_evidence,
    aware_datetime,
    locked_defect_record,
    participant_map,
    raw_field_values,
    stored_datetime,
    update_core_record,
)
from .schema import ensure_defect_document_type
from .volumes import close_completed_old_volumes, current_defect_volume


def _validate_actor(record: OperationalDocumentRecord, actor: Employee) -> None:
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может выполнить действие.")
    if actor.organization_id != record.organization_id:
        raise ValidationError("Сотрудник относится к другой организации.")


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
    detected_at = aware_datetime(detected_at)
    description = defect_description.strip()
    if not actor.is_active:
        raise ValidationError("Недействующий сотрудник не может зарегистрировать дефект.")
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
    if not discovered_by.is_active:
        raise ValidationError("Лицо, обнаружившее дефект, должно быть действующим сотрудником.")
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
    append_action_evidence(
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
    locked = locked_defect_record(record)
    _validate_actor(locked, actor)
    if locked.status_code != STATUS_REGISTERED:
        raise ValidationError("Срок устанавливается только для зарегистрированного дефекта.")
    deadline = aware_datetime(deadline)
    detected_at = stored_datetime(locked, FIELD_DETECTED_AT)
    if detected_at is None or deadline < detected_at:
        raise ValidationError("Срок устранения не может быть раньше даты обнаружения.")
    if responsible.organization_id != locked.organization_id:
        raise ValidationError("Ответственный относится к другой организации.")
    if not responsible.is_active:
        raise ValidationError("Ответственный должен быть действующим сотрудником.")

    values = raw_field_values(locked)
    values[FIELD_ELIMINATION_DEADLINE] = deadline
    participants = participant_map(locked)
    participants[ROLE_OPERATIONS_RESPONSIBLE] = [responsible]
    updated = update_core_record(
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
    append_action_evidence(
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
    locked = locked_defect_record(record)
    _validate_actor(locked, actor)
    if locked.status_code != STATUS_IN_PROGRESS:
        raise ValidationError("Продлить срок можно только для дефекта в работе.")
    previous_deadline = stored_datetime(locked, FIELD_ELIMINATION_DEADLINE)
    if previous_deadline is None:
        raise ValidationError("Нельзя продлить срок, который ещё не установлен.")
    new_deadline = aware_datetime(new_deadline)
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
    updated = update_core_record(
        record=locked,
        actor=actor,
        values=values,
        participants=participant_map(locked),
        comment=comment,
    )
    append_action_evidence(
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
    locked = locked_defect_record(record)
    _validate_actor(locked, actor)
    if locked.status_code != STATUS_IN_PROGRESS:
        raise ValidationError("Устранение фиксируется только для дефекта в работе.")
    resolved_at = aware_datetime(resolved_at)
    detected_at = stored_datetime(locked, FIELD_DETECTED_AT)
    if detected_at is None or resolved_at < detected_at:
        raise ValidationError("Дата устранения не может быть раньше даты обнаружения.")
    if resolved_at > timezone.now() + timedelta(seconds=1):
        raise ValidationError("Дата устранения не может быть в будущем.")
    normalized_summary = work_summary.strip()
    if not normalized_summary:
        raise ValidationError("Содержание выполненных работ обязательно.")
    if responsible.organization_id != locked.organization_id:
        raise ValidationError("Ответственный относится к другой организации.")
    if not responsible.is_active:
        raise ValidationError("Ответственный должен быть действующим сотрудником.")

    values = raw_field_values(locked)
    values[FIELD_RESOLVED_AT] = resolved_at
    values[FIELD_RESOLUTION_WORK_SUMMARY] = normalized_summary
    participants = participant_map(locked)
    participants[ROLE_RESOLUTION_RESPONSIBLE] = [responsible]
    updated = update_core_record(
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
    append_action_evidence(
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
    locked = locked_defect_record(record)
    _validate_actor(locked, actor)
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
    updated = update_core_record(
        record=locked,
        actor=actor,
        values=raw_field_values(locked),
        participants=participants,
        comment="Оперативный персонал ознакомился с записью об устранении дефекта.",
    )
    append_action_evidence(
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
    locked = locked_defect_record(record)
    _validate_actor(locked, actor)
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
    append_action_evidence(
        record=transitioned,
        actor=actor,
        action_code=DefectActionCode.CLOSED,
    )
    if transitioned.workplace_id:
        close_completed_old_volumes(transitioned.workplace)
    return transitioned
