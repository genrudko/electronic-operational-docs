from __future__ import annotations

from dataclasses import replace

from django import template
from django.core.exceptions import ValidationError
from django.utils.html import json_script

from ..opj_integrity import verify_registered_snapshot
from ..opj_lifecycle import (
    TYPE_COMMUNICATION,
    TYPE_ENTRY,
    draft_registration_context,
    entry_lifecycle_context,
    registered_entry_for_draft,
)
from ..opj_presentation import entry_presentation, present_editor_document

register = template.Library()


@register.simple_tag
def opj_draft_registration(draft):
    return draft_registration_context(draft)


@register.simple_tag
def opj_entry_lifecycle(entry):
    lifecycle = entry_lifecycle_context(entry)
    try:
        verify_registered_snapshot(entry)
        for event in lifecycle.lifecycle_entries:
            verify_registered_snapshot(event)
    except ValidationError:
        integrity_ok = False
    else:
        integrity_ok = True
    return replace(lifecycle, integrity_ok=integrity_ok)


@register.simple_tag
def opj_entry_presentation(entry, lifecycle_entries=None):
    return entry_presentation(entry, lifecycle_entries=lifecycle_entries)


@register.simple_tag
def opj_editor_presentation(editor_payload):
    return present_editor_document(editor_payload)


@register.simple_tag
def opj_editor_payload_script(presentation, sequence_number):
    return json_script(
        presentation.editor_payload,
        f"opj-editor-payload-{sequence_number}",
    )


@register.simple_tag
def opj_registered_removed_drafts(drafts):
    return [
        {"draft": draft, "entry": entry}
        for draft in drafts
        if (entry := registered_entry_for_draft(draft)) is not None
    ]


@register.simple_tag
def opj_shift_clean_summary(shift):
    draft_ids = {
        str(value)
        for value in shift.draft_entries.values_list("public_id", flat=True)
    }
    entries = []
    for entry in (
        shift.journal.entries.filter(type_code__in=(TYPE_ENTRY, TYPE_COMMUNICATION))
        .only("sequence_number", "registered_at", "typed_payload")
        .order_by("sequence_number")
    ):
        payload = entry.typed_payload if isinstance(entry.typed_payload, dict) else {}
        draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
        if str(draft.get("public_id") or "") in draft_ids:
            entries.append(entry)
    last = entries[-1] if entries else None
    return {
        "count": len(entries),
        "last_sequence": last.sequence_number if last else None,
        "last_registered_at": last.registered_at if last else None,
    }
