from __future__ import annotations

from django import template

from ..opj_lifecycle import (
    draft_registration_context,
    entry_lifecycle_context,
    registered_entry_for_draft,
)

register = template.Library()


@register.simple_tag
def opj_draft_registration(draft):
    return draft_registration_context(draft)


@register.simple_tag
def opj_entry_lifecycle(entry):
    return entry_lifecycle_context(entry)


@register.simple_tag
def opj_registered_removed_drafts(drafts):
    return [
        {"draft": draft, "entry": entry}
        for draft in drafts
        if (entry := registered_entry_for_draft(draft)) is not None
    ]
