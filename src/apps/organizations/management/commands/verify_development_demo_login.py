from __future__ import annotations

import re
import time
from http.cookiejar import CookieJar
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urljoin, urlsplit
from urllib.request import HTTPCookieProcessor, Request, build_opener

from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.core.management.base import BaseCommand, CommandError

from apps.organizations.demo_access import (
    DEMO_USERNAMES,
    DemoAccessPolicyError,
    injected_demo_password,
    validate_demo_password,
)

_CSRF_PATTERN = re.compile(
    rb'name=["\']csrfmiddlewaretoken["\'][^>]*value=["\']([^"\']+)["\']'
)


class Command(BaseCommand):
    help = (
        "Проверяет реальный Development demo-login через живой HTTP endpoint, "
        "не выводя credential в stdout/stderr."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--base-url",
            default="http://127.0.0.1:8765",
            help="Локальный URL запущенного Development web process.",
        )
        parser.add_argument(
            "--wait-seconds",
            type=int,
            default=45,
            help="Максимальное время ожидания живого web process.",
        )

    def handle(self, *args, **options) -> None:
        if settings.EOD_DEPLOYMENT_MODE != "development":
            raise CommandError(
                "Development authentication smoke is allowed only in development mode."
            )

        password = injected_demo_password()
        try:
            validate_demo_password(password)
        except DemoAccessPolicyError as exc:
            raise CommandError("Development demo credential is not usable.") from exc

        user_model = get_user_model()
        users = {
            user.username: user
            for user in user_model.objects.filter(username__in=DEMO_USERNAMES)
        }
        if set(users) != set(DEMO_USERNAMES):
            raise CommandError("Development demo accounts are incomplete.")

        for username in DEMO_USERNAMES:
            user = users[username]
            if not user.is_active:
                raise CommandError("Development demo account is inactive.")
            if not user.has_usable_password() or not user.check_password(password):
                raise CommandError("Development demo account password state is invalid.")
            authenticated = authenticate(username=username, password=password)
            if authenticated is None or authenticated.pk != user.pk:
                raise CommandError("Development authentication backend rejected demo access.")

        base_url = str(options["base_url"]).rstrip("/") + "/"
        wait_seconds = max(1, int(options["wait_seconds"]))
        deadline = time.monotonic() + wait_seconds
        last_error: Exception | None = None
        while time.monotonic() < deadline:
            try:
                self._probe_login_page(base_url)
                last_error = None
                break
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                last_error = exc
                time.sleep(1)
        if last_error is not None:
            raise CommandError("Development login endpoint did not become ready.") from last_error

        for username in DEMO_USERNAMES:
            self._verify_http_session(base_url, username, password)

        self.stdout.write(
            "DEVELOPMENT_AUTHENTICATION_SMOKE=PASS "
            "accounts=2 path=/accounts/login/ credential=MASKED"
        )

    def _probe_login_page(self, base_url: str) -> None:
        opener = build_opener(HTTPCookieProcessor(CookieJar()))
        response = opener.open(urljoin(base_url, "accounts/login/"), timeout=3)
        if response.status != 200:
            raise CommandError("Development login endpoint returned a non-200 status.")

    def _verify_http_session(self, base_url: str, username: str, password: str) -> None:
        jar = CookieJar()
        opener = build_opener(HTTPCookieProcessor(jar))
        login_url = urljoin(base_url, "accounts/login/")
        response = opener.open(login_url, timeout=5)
        body = response.read()
        csrf_match = _CSRF_PATTERN.search(body)
        if csrf_match is None:
            raise CommandError("Development login form does not expose a CSRF token.")
        csrf_token = csrf_match.group(1).decode("utf-8")

        # The published Development credential must be the same injected value.
        # The value is compared only in memory and is never printed.
        if username.encode("utf-8") not in body or password.encode("utf-8") not in body:
            raise CommandError("Development login page does not publish the active demo credential.")

        payload = urlencode(
            {
                "username": username,
                "password": password,
                "csrfmiddlewaretoken": csrf_token,
                "next": "/accounts/me/",
            }
        ).encode("utf-8")
        request = Request(
            login_url,
            data=payload,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": login_url,
            },
            method="POST",
        )
        response = opener.open(request, timeout=8)
        final_path = urlsplit(response.geturl()).path
        if final_path.startswith("/accounts/login/"):
            raise CommandError("Development demo login was rejected by the live application.")

        account = opener.open(urljoin(base_url, "accounts/me/"), timeout=5)
        if account.status != 200 or urlsplit(account.geturl()).path != "/accounts/me/":
            raise CommandError("Development authenticated owner route is not reachable.")
