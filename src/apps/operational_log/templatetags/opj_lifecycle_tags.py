from __future__ import annotations

from django import template

from ..opj_lifecycle import (
    draft_registration_context,
    entry_lifecycle_context,
)

register = template.Library()


@register.simple_tag
def opj_draft_registration(draft):
    return draft_registration_context(draft)


@register.simple_tag
def opj_entry_lifecycle(entry):
    return entry_lifecycle_context(entry)
