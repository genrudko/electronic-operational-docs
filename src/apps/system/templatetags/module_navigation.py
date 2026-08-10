from __future__ import annotations

from django import template

from apps.organizations.models import Employee
from apps.system.module_registry import (
    EntryPointClass,
    ModuleOperation,
    decide_module_access,
    normalize_context,
)

register = template.Library()


@register.simple_tag(takes_context=True)
def module_navigation_allowed(
    context: template.Context,
    module_id: str,
    capability_id: str,
) -> bool:
    """Project central module-access semantics into shared navigation.

    Navigation intentionally asks for READ rather than inventing a second
    "active module" rule. The accepted registry contract may keep retained
    history readable when a module is read-only/inactive/retired.
    """

    request = context.get("request")
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return False
    try:
        employee = Employee.objects.select_related(
            "organization",
            "workplace",
        ).get(user=user)
    except Employee.DoesNotExist:
        return False

    scope = normalize_context(
        organization=employee.organization,
        workplace=employee.workplace,
    )
    decision = decide_module_access(
        context=scope,
        module_id=module_id,
        capability_id=capability_id,
        operation=ModuleOperation.READ,
        entry_point_class=EntryPointClass.NAVIGATION_UI,
    )
    return decision.allowed
