from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import resolve, reverse

from .test_deployment_profile import safe_production_environment

ROOT = Path(__file__).resolve().parents[4]


class SecurityBaselineRouteTests(TestCase):
    def test_development_and_ci_keep_django_admin_available(self) -> None:
        self.assertTrue(settings.EOD_DJANGO_ADMIN_ENABLED)
        self.assertEqual(reverse("admin:index"), "/admin/")
        self.assertEqual(resolve("/admin/").url_name, "index")

    def test_real_logout_mutation_rejects_missing_csrf_token(self) -> None:
        user = get_user_model().objects.create_user(
            username="security-baseline-csrf-user",
            password="temporary-test-password-only",
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(reverse("organizations:logout"))

        self.assertEqual(response.status_code, 403)


class ProductionSecuritySettingsTests(TestCase):
    def test_production_admin_is_unrouted_and_http_session_decisions_are_explicit(self) -> None:
        env = os.environ.copy()
        env.update(safe_production_environment())
        # This variable is intentionally unsupported. A stray environment value
        # must not turn the privileged admin surface back on in production.
        env["EOD_DJANGO_ADMIN_ENABLED"] = "1"
        env["DJANGO_SETTINGS_MODULE"] = "eod_config.settings"
        env["PYTHONPATH"] = str(ROOT / "src")

        script = r'''
import django

django.setup()

from django.conf import settings
from django.urls import Resolver404, resolve

assert settings.EOD_DJANGO_ADMIN_ENABLED is False
assert settings.DEBUG is False
assert settings.SECURE_SSL_REDIRECT is True
assert settings.SESSION_COOKIE_SECURE is True
assert settings.CSRF_COOKIE_SECURE is True
assert settings.SESSION_COOKIE_HTTPONLY is True
assert settings.CSRF_COOKIE_HTTPONLY is True
assert settings.SESSION_COOKIE_SAMESITE == "Lax"
assert settings.CSRF_COOKIE_SAMESITE == "Lax"
assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
assert settings.SECURE_REFERRER_POLICY == "same-origin"
assert settings.X_FRAME_OPTIONS == "DENY"
assert settings.SECURE_HSTS_SECONDS >= 3600
assert settings.SECURE_PROXY_SSL_HEADER == ("HTTP_X_FORWARDED_PROTO", "https")
assert settings.USE_X_FORWARDED_HOST is False

try:
    resolve("/admin/")
except Resolver404:
    pass
else:
    raise AssertionError("production /admin/ unexpectedly resolved")
'''
        result = subprocess.run(
            [sys.executable, "-c", script],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(
            result.returncode,
            0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
