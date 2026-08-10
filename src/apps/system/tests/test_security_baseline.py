from __future__ import annotations

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import resolve, reverse

from eod_config.urls import build_urlpatterns


class SecurityBaselineRouteTests(TestCase):
    def test_development_and_ci_keep_django_admin_available(self) -> None:
        self.assertTrue(settings.EOD_DJANGO_ADMIN_ENABLED)
        self.assertEqual(reverse("admin:index"), "/admin/")
        self.assertEqual(resolve("/admin/").url_name, "index")

    def test_admin_route_builder_omits_privileged_surface_when_disabled(self) -> None:
        routes = {
            str(pattern.pattern)
            for pattern in build_urlpatterns(django_admin_enabled=False)
        }
        self.assertNotIn("admin/", routes)

    def test_admin_route_builder_requires_explicit_true_value(self) -> None:
        routes = {
            str(pattern.pattern)
            for pattern in build_urlpatterns(django_admin_enabled=True)
        }
        self.assertIn("admin/", routes)

    def test_real_logout_mutation_rejects_missing_csrf_token(self) -> None:
        user = get_user_model().objects.create_user(
            username="security-baseline-csrf-user"
        )
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)

        response = client.post(reverse("organizations:logout"))

        self.assertEqual(response.status_code, 403)
