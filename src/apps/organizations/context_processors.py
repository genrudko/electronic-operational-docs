from __future__ import annotations

from types import SimpleNamespace

from .models import Employee, InterfacePreference

DEFAULT_INTERFACE_PREFERENCES = SimpleNamespace(
    theme=InterfacePreference.Theme.DARK,
    density=InterfacePreference.Density.COMFORTABLE,
    font_scale=InterfacePreference.FontScale.NORMAL,
    content_width=InterfacePreference.ContentWidth.STANDARD,
    show_technical_details=False,
    journal_heading_mode=InterfacePreference.JournalHeadingMode.COMPACT,
    journal_font_family=InterfacePreference.JournalFontFamily.SYSTEM,
    journal_font_size=InterfacePreference.JournalFontSize.NORMAL,
    journal_density=InterfacePreference.JournalDensity.NORMAL,
    journal_width=InterfacePreference.JournalWidth.WIDE,
    journal_show_authors=True,
    journal_show_links=True,
    journal_simplified_time_input=False,
)


def interface_preferences(request):
    preferences = DEFAULT_INTERFACE_PREFERENCES
    current_employee = None
    user_display_name = ""
    user_display_role = ""
    user_initial = ""

    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        preferences, _ = InterfacePreference.objects.get_or_create(user=request.user)
        current_employee = (
            Employee.objects.select_related("position")
            .filter(user=request.user, is_active=True)
            .first()
        )
        user_display_name = (
            current_employee.full_name
            if current_employee
            else request.user.get_full_name().strip() or request.user.get_username()
        )
        user_display_role = (
            current_employee.position.name
            if current_employee and current_employee.position_id
            else ""
        )
        user_initial = user_display_name[:1].upper()

    return {
        "ui_preferences": preferences,
        "current_employee": current_employee,
        "user_display_name": user_display_name,
        "user_display_role": user_display_role,
        "user_initial": user_initial,
    }
