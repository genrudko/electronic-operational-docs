from __future__ import annotations

from typing import Any

from django import template

from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee
from apps.system.module_registry import EntryPointClass

from ..services import defect_opj_link_access_decision

register = template.Library()


@register.simple_tag(takes_context=True)
def operational_defect_entry_rows(context: dict[str, Any]) -> list[dict[str, Any]]:
    request = context.get("request")
    if request is None or not getattr(request.user, "is_authenticated", False):
        return []
    resolver_match = getattr(request, "resolver_match", None)
    if (
        resolver_match is None
        or resolver_match.namespace != "operational_log"
        or resolver_match.url_name != "detail"
    ):
        return []
    journal_id = resolver_match.kwargs.get("journal_id")
    if journal_id is None:
        return []
    try:
        employee = request.user.employee_profile
    except (AttributeError, Employee.DoesNotExist):
        return []

    entries = (
        OperationalLogEntry.objects.filter(
            journal_id=journal_id,
            journal__organization=employee.organization,
        )
        .select_related("journal", "journal__workplace")
        .prefetch_related(
            "equipment_defect_links",
            "equipment_defect_links__record",
        )
        .order_by("-sequence_number", "-pk")[:100]
    )
    rows: list[dict[str, Any]] = []
    for entry in entries:
        defect_links = list(entry.equipment_defect_links.all())
        can_create_defect = defect_opj_link_access_decision(
            organization_id=entry.journal.organization_id,
            workplace_id=entry.journal.workplace_id,
            entry_point_class=EntryPointClass.NAVIGATION_UI,
        ).allowed
        # Retained historical links remain visible while inactive, but an empty row
        # whose only purpose would be the new-action button is not offered.
        if not defect_links and not can_create_defect:
            continue
        rows.append(
            {
                "entry": entry,
                "defect_links": defect_links,
                "can_create_defect": can_create_defect,
            }
        )
    return rows
