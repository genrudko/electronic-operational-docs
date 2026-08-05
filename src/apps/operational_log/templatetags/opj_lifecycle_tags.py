from __future__ import annotations

from dataclasses import replace

from django import template
from django.core.exceptions import ValidationError
from django.utils.html import json_script

from ..models import OperationalDraftEntry
from ..opj_integrity import verify_registered_snapshot
from ..opj_lifecycle import (
    TYPE_COMMUNICATION,
    TYPE_ENTRY,
    draft_registration_context,
    entry_lifecycle_context,
    registered_entry_for_draft,
)
from ..opj_presentation import (
    entry_presentation,
    journal_number_map,
    present_editor_document,
)

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


def _journal_number_cache(context, journal):
    cache = context.render_context.setdefault(
        "opj_journal_number_cache",
        {},
    )
    if journal.pk in cache:
        return cache[journal.pk]

    entries = list(journal.entries.all())
    draft_ids = set()
    for entry in entries:
        payload = entry.typed_payload if isinstance(entry.typed_payload, dict) else {}
        draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
        public_id = str(draft.get("public_id") or "")
        if public_id:
            draft_ids.add(public_id)
    drafts = {
        str(draft.public_id): draft
        for draft in OperationalDraftEntry.objects.filter(
            public_id__in=draft_ids,
        ).only("public_id", "position")
    }
    cache[journal.pk] = journal_number_map(entries, drafts)
    return cache[journal.pk]


@register.simple_tag(takes_context=True)
def opj_journal_number(context, entry):
    return _journal_number_cache(context, entry.journal).get(
        entry.pk,
        entry.sequence_number,
    )


@register.simple_tag
def opj_shift_clean_summary(shift):
    draft_ids = {
        str(value)
        for value in shift.draft_entries.values_list("public_id", flat=True)
    }
    entries = []
    for entry in (
        shift.journal.entries.filter(type_code__in=(TYPE_ENTRY, TYPE_COMMUNICATION))
        .only("registered_at", "typed_payload")
        .order_by("registered_at", "pk")
    ):
        payload = entry.typed_payload if isinstance(entry.typed_payload, dict) else {}
        draft = payload.get("draft") if isinstance(payload.get("draft"), dict) else {}
        if str(draft.get("public_id") or "") in draft_ids:
            entries.append(entry)
    last = entries[-1] if entries else None
    return {
        "count": len(entries),
        "last_registered_at": last.registered_at if last else None,
    }
