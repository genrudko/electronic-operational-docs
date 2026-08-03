from __future__ import annotations

from django.utils import timezone

from .models import OperationalLogEntry
from .opj_presentation import build_clean_journal_groups, entry_presentation


def build_print_journal_groups(
    *,
    entries: list[OperationalLogEntry],
    selected_shift: str = "",
):
    groups = build_clean_journal_groups(
        entries=entries,
        selected_shift=selected_shift,
    )
    for group in groups:
        print_rows = []
        for row in group.rows:
            original = dict(row)
            original["presentation"] = entry_presentation(
                row["entry"],
                lifecycle_entries=(),
            )
            original["is_lifecycle_event"] = False
            original["target_entry"] = None
            original["reason"] = ""
            print_rows.append(original)
            for event in row["lifecycle"].lifecycle_entries:
                payload = (
                    event.typed_payload
                    if isinstance(event.typed_payload, dict)
                    else {}
                )
                print_rows.append(
                    {
                        "entry": event,
                        "presentation": entry_presentation(event),
                        "is_lifecycle_event": True,
                        "target_entry": row["entry"],
                        "reason": str(payload.get("reason") or ""),
                        "show_date": False,
                    }
                )
        print_rows.sort(
            key=lambda row: (
                row["entry"].event_at,
                row["entry"].sequence_number,
            )
        )
        previous_date = None
        for row in print_rows:
            current_date = timezone.localtime(row["entry"].event_at).date()
            row["show_date"] = current_date != previous_date
            previous_date = current_date
        group.rows = print_rows
    return groups
