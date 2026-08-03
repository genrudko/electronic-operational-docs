from __future__ import annotations

import uuid
from collections.abc import Iterable

from django.core.exceptions import ValidationError

from .models import OperationalDraftEntry, OperationalShift

REGISTERED_DRAFT_TYPES = ("opj-entry", "opj-communication")


def _registered_draft_ids(shift: OperationalShift) -> set[str]:
    result: set[str] = set()
    entries = shift.journal.entries.filter(
        type_code__in=REGISTERED_DRAFT_TYPES,
    ).only("typed_payload")
    for entry in entries:
        payload = entry.typed_payload if isinstance(entry.typed_payload, dict) else {}
        draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
        public_id = str(draft.get("public_id") or "")
        if public_id:
            result.add(public_id)
    return result


def ordered_registration_drafts(
    *,
    shift: OperationalShift,
    requested_ids: Iterable[uuid.UUID],
) -> list[OperationalDraftEntry]:
    """Return selected draft rows in event chronology.

    Registration time must not determine the visible journal number.  Rows may
    therefore be registered later than neighbouring rows; the clean journal
    computes its official continuous display order from event time and source
    position.  The immutable database sequence remains an internal identity.
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
    if any(value not in by_id for value in requested):
        raise ValidationError("Одна из выбранных строк не относится к текущей смене.")

    registered_ids = _registered_draft_ids(shift)
    selected = [by_id[value] for value in requested]
    if any(
        not row.content.strip() or str(row.public_id) in registered_ids
        for row in selected
    ):
        raise ValidationError(
            "Одна из выбранных строк уже зарегистрирована или не содержит записи."
        )

    return sorted(
        selected,
        key=lambda row: (row.event_at, row.position, row.pk),
    )
