from __future__ import annotations

from types import SimpleNamespace

from .models import InterfacePreference

DEFAULT_INTERFACE_PREFERENCES = SimpleNamespace(
    theme=InterfacePreference.Theme.DARK,
    density=InterfacePreference.Density.COMFORTABLE,
    font_scale=InterfacePreference.FontScale.NORMAL,
    content_width=InterfacePreference.ContentWidth.STANDARD,
    show_technical_details=False,
)


def interface_preferences(request):
    preferences = DEFAULT_INTERFACE_PREFERENCES
    if getattr(request, "user", None) is not None and request.user.is_authenticated:
        preferences, _ = InterfacePreference.objects.get_or_create(user=request.user)
    return {"ui_preferences": preferences}
