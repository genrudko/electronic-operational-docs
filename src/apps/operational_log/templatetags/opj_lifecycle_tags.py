from __future__ import annotations

from django import template
from django.utils.html import json_script

from ..opj_lifecycle import (
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
    return entry_lifecycle_context(entry)


@register.simple_tag
def opj_entry_presentation(entry, lifecycle_entries=None):
    return entry_presentation(entry, lifecycle_entries=lifecycle_entries)


@register.simple_tag
def opj_editor_presentation(editor_payload):
    return present_editor_document(editor_payload)


@register.simple_tag
def opj_editor_payload_script(presentation, element_id: str):
    return json_script(presentation.editor_payload, element_id)


@register.simple_tag
def opj_registered_removed_drafts(drafts):
    return [
        {"draft": draft, "entry": entry}
        for draft in drafts
        if (entry := registered_entry_for_draft(draft)) is not None
    ]
