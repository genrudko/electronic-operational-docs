from __future__ import annotations

import hashlib
import re

from django.contrib.auth import authenticate, get_user_model
from django.test import Client

from .demo_access import (
    DEMO_USERNAMES,
    injected_demo_password,
    validate_demo_password,
)

_CSRF_PATTERN = re.compile(
    rb'name=["\']csrfmiddlewaretoken["\'][^>]*value=["\']([^"\']+)["\']'
)
_verified_fingerprint: str | None = None


def verify_development_demo_authentication_state() -> bool:
    """Verify persistent Development principals and the configured auth backend.

    This bounded readiness check deliberately does not instantiate Django's test
    client or perform an HTTP request. The live published login path is proved
    separately by ``verify_development_demo_login`` against the running server.
    """

    password = injected_demo_password()
    validate_demo_password(password)

    user_model = get_user_model()
    users = {
        user.username: user
        for user in user_model.objects.filter(username__in=DEMO_USERNAMES)
    }
    if set(users) != set(DEMO_USERNAMES):
        return False

    for username in DEMO_USERNAMES:
        user = users[username]
        if not user.is_active or not user.has_usable_password():
            return False
        if not user.check_password(password):
            return False
        authenticated = authenticate(username=username, password=password)
        if authenticated is None or authenticated.pk != user.pk:
            return False

    return True


def verify_development_demo_login_path() -> bool:
    """Verify the rendered Development credential through the Django login view.

    This in-process acceptance helper is retained for focused Django tests. The
    trusted deployment smoke uses the management command that performs the same
    flow through the live HTTP endpoint. The credential never leaves process
    memory in either path.
    """

    global _verified_fingerprint

    password = injected_demo_password()
    validate_demo_password(password)
    fingerprint = hashlib.sha256(password.encode("utf-8")).hexdigest()
    if _verified_fingerprint == fingerprint:
        return True

    if not verify_development_demo_authentication_state():
        return False

    for username in DEMO_USERNAMES:
        client = Client(enforce_csrf_checks=True)
        login_response = client.get("/accounts/login/", HTTP_HOST="127.0.0.1")
        if login_response.status_code != 200:
            return False
        body = login_response.content
        if username.encode("utf-8") not in body or password.encode("utf-8") not in body:
            return False
        csrf_match = _CSRF_PATTERN.search(body)
        if csrf_match is None:
            return False
        csrf_token = csrf_match.group(1).decode("utf-8")

        response = client.post(
            "/accounts/login/",
            {
                "username": username,
                "password": password,
                "csrfmiddlewaretoken": csrf_token,
                "next": "/accounts/me/",
            },
            HTTP_HOST="127.0.0.1",
            HTTP_REFERER="http://127.0.0.1/accounts/login/",
            follow=False,
        )
        if response.status_code not in {301, 302, 303}:
            return False
        account_response = client.get("/accounts/me/", HTTP_HOST="127.0.0.1")
        if account_response.status_code != 200:
            return False

    _verified_fingerprint = fingerprint
    return True
