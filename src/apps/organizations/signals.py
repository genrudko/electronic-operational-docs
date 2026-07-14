from __future__ import annotations

from typing import Any

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .models import AuthenticationEvent


def _request_context(request) -> dict[str, str | None]:
    if request is None:
        return {
            "ip_address": None,
            "user_agent": "",
            "session_key": "",
        }
    forwarded = request.META.get("HTTP_X_FORWARDED_FOR", "")
    ip_address = forwarded.split(",", 1)[0].strip() if forwarded else request.META.get("REMOTE_ADDR")
    session = getattr(request, "session", None)
    return {
        "ip_address": ip_address or None,
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:512],
        "session_key": (session.session_key or "") if session is not None else "",
    }


def _employee_for(user):
    if user is None:
        return None
    try:
        return user.employee_profile
    except AttributeError:
        return None


@receiver(user_logged_in, dispatch_uid="organizations.audit_user_logged_in")
def audit_user_logged_in(sender: Any, request, user, **kwargs: Any) -> None:
    AuthenticationEvent.objects.create(
        event_type=AuthenticationEvent.EventType.LOGIN_SUCCESS,
        user=user,
        employee=_employee_for(user),
        username_snapshot=user.get_username(),
        **_request_context(request),
    )


@receiver(user_login_failed, dispatch_uid="organizations.audit_user_login_failed")
def audit_user_login_failed(sender: Any, credentials: dict[str, Any], request, **kwargs: Any) -> None:
    username = credentials.get("username") or credentials.get("email") or ""
    AuthenticationEvent.objects.create(
        event_type=AuthenticationEvent.EventType.LOGIN_FAILURE,
        username_snapshot=str(username)[:150],
        **_request_context(request),
    )


@receiver(user_logged_out, dispatch_uid="organizations.audit_user_logged_out")
def audit_user_logged_out(sender: Any, request, user, **kwargs: Any) -> None:
    AuthenticationEvent.objects.create(
        event_type=AuthenticationEvent.EventType.LOGOUT,
        user=user,
        employee=_employee_for(user),
        username_snapshot=user.get_username() if user is not None else "",
        **_request_context(request),
    )
