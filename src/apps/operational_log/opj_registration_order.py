from __future__ import annotations

import uuid
from collections.abc import Iterable

from django.core.exceptions import ValidationError

from .models import OperationalDraftEntry, OperationalShift

REGISTERED_DRAFT_TYPES = ("opj-entry", "opj-communication")


def _registered_draft_sequences(shift: OperationalShift) -> dict[str, tuple[int, object]]:
    result: dict[str, tuple[int, object]] = {}
    entries = shift.journal.entries.filter(
        type_code__in=REGISTERED_DRAFT_TYPES,
    ).only("sequence_number", "event_at", "typed_payload")
    for entry in entries:
        payload = entry.typed_payload if isinstance(entry.typed_payload, dict) else {}
        draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
        public_id = str(draft.get("public_id") or "")
        if public_id:
            result[public_id] = (entry.sequence_number, entry.event_at)
    return result


def ordered_registration_drafts(
    *,
    shift: OperationalShift,
    requested_ids: Iterable[uuid.UUID],
) -> list[OperationalDraftEntry]:
    """Return requested drafts in journal chronology and reject gaps.

    Official numbering is append-only, so an earlier draft cannot be inserted
    after a later source row has already received a number.  A batch therefore
    must be the chronological prefix of all currently registerable, non-empty
    rows in the open shift.
    """

    requested = list(dict.fromkeys(requested_ids))
    if not requested:
        raise ValidationError("Выберите хотя бы одну строку черновика.")

    active_rows = list(
        OperationalDraftEntry.objects.select_for_update()
        .filter(shift=shift, is_removed=False)
        .select_related("shift", "shift__journal")
        .order_by("event_at", "position", "pk")
    )
    by_id = {row.public_id: row for row in active_rows}
    missing = [value for value in requested if value not in by_id]
    if missing:
        raise ValidationError("Одна из выбранных строк не относится к текущей смене.")

    registrations = _registered_draft_sequences(shift)
    registerable = [
        row
        for row in active_rows
        if row.content.strip()
        and str(row.public_id) not in registrations
    ]
    requested_set = set(requested)
    selected = [row for row in registerable if row.public_id in requested_set]
    if len(selected) != len(requested):
        raise ValidationError(
            "Одна из выбранных строк уже зарегистрирована или не содержит записи."
        )

    expected_prefix = registerable[: len(selected)]
    if [row.public_id for row in selected] != [row.public_id for row in expected_prefix]:
        first = registerable[0] if registerable else None
        detail = (
            f" Сначала зарегистрируйте запись {first.event_at:%d.%m.%Y %H:%M}."
            if first is not None
            else ""
        )
        raise ValidationError(
            "Нельзя оставлять хронологический разрыв в чистовике." + detail
        )

    registered_times = [event_at for _, event_at in registrations.values()]
    if registered_times and selected and selected[0].event_at < max(registered_times):
        raise ValidationError(
            "Более поздняя строка этой смены уже получила номер. "
            "Раннюю запись оформите как пропущенную запись без перенумерации журнала."
        )

    return selected
