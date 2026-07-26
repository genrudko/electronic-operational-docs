from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from apps.organizations.models import Employee, Workplace

from ..constants import FIELD_RESOLVED_AT
from ..models import EquipmentDefectVolume
from .helpers import stored_datetime


def try_close_volume(volume: EquipmentDefectVolume) -> bool:
    locked = EquipmentDefectVolume.objects.select_for_update().get(pk=volume.pk)
    if locked.closed_on is not None:
        return True
    contexts = list(locked.defect_contexts.select_related("record"))
    if not contexts:
        return False
    if any(not context.record.status_is_terminal for context in contexts):
        return False
    resolved_dates = [
        stored_datetime(context.record, FIELD_RESOLVED_AT)
        for context in contexts
    ]
    if any(value is None for value in resolved_dates):
        return False
    locked.closed_on = max(value for value in resolved_dates if value is not None).date()
    locked.accepts_new_records = False
    locked.save(update_fields=("accepts_new_records", "closed_on"))
    return True


@transaction.atomic
def current_defect_volume(
    *,
    workplace: Workplace,
    actor: Employee,
) -> EquipmentDefectVolume:
    if workplace.organization_id != actor.organization_id:
        raise ValidationError("Рабочее место относится к другой организации.")
    volume = (
        EquipmentDefectVolume.objects.select_for_update()
        .filter(
            accepts_new_records=True,
            organization=actor.organization,
            workplace=workplace,
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
def open_new_defect_volume(
    *,
    workplace: Workplace,
    actor: Employee,
) -> EquipmentDefectVolume:
    current = current_defect_volume(workplace=workplace, actor=actor)
    if not current.defect_contexts.exists():
        raise ValidationError("Новый том не открывается, пока текущий том не содержит записей.")
    current.accepts_new_records = False
    current.save(update_fields=("accepts_new_records",))
    try_close_volume(current)
    return current_defect_volume(workplace=workplace, actor=actor)


@transaction.atomic
def close_completed_old_volumes(workplace: Workplace) -> None:
    volumes = EquipmentDefectVolume.objects.select_for_update().filter(
        accepts_new_records=False,
        closed_on__isnull=True,
        workplace=workplace,
    )
    for volume in volumes:
        try_close_volume(volume)
