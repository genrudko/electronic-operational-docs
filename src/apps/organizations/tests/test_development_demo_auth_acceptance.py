from __future__ import annotations

from unittest import mock

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings

from apps.organizations.demo_access import (
    DEMO_ACCESS_ENV,
    DEMO_USERNAMES,
    development_demo_access_presentation,
    ensure_development_demo_accounts,
    reconcile_demo_access,
)
from apps.organizations.development_auth_smoke import (
    verify_development_demo_login_path,
)
from tests.credential_fixtures import ephemeral_credential

TEST_CREDENTIAL = ephemeral_credential("OwnerAcceptanceDemo")


class DevelopmentDemoAuthenticationAcceptanceTests(TestCase):
    def setUp(self) -> None:
        # Reset the independent per-process smoke caches so every test proves its
        # own persistent account state and live login path.
        from apps.organizations import development_auth_smoke

        development_auth_smoke._verified_fingerprint = None
        development_auth_smoke._verified_authentication_state_fingerprint = None

    @mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: TEST_CREDENTIAL}, clear=False)
    @override_settings(EOD_DEPLOYMENT_MODE="development")
    def test_missing_principals_are_bootstrapped_active_and_authenticatable(self) -> None:
        self.assertEqual(get_user_model().objects.filter(username__in=DEMO_USERNAMES).count(), 0)
        self.assertEqual(ensure_development_demo_accounts(), 2)
        result = reconcile_demo_access(require_injection=True)
        self.assertEqual(result.status, "ENABLED_LOCAL_INJECTION")
        for user in get_user_model().objects.filter(username__in=DEMO_USERNAMES):
            self.assertTrue(user.is_active)
            self.assertTrue(user.has_usable_password())
            self.assertTrue(user.check_password(TEST_CREDENTIAL))

    @mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: TEST_CREDENTIAL}, clear=False)
    @override_settings(EOD_DEPLOYMENT_MODE="development")
    def test_development_page_publishes_same_injected_credential_used_by_auth(self) -> None:
        ensure_development_demo_accounts()
        reconcile_demo_access(require_injection=True)
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "operator.demo")
        self.assertContains(response, "supervisor.demo")
        self.assertContains(response, TEST_CREDENTIAL)
        self.assertContains(response, 'data-development-demo-credentials')
        self.assertNotContains(response, 'class="auth-shell"')
        self.assertNotContains(response, 'class="auth-card"')
        self.assertNotContains(response, 'class="auth-form"')
        self.assertNotContains(response, 'class="button full"')
        self.assertNotContains(response, 'class="demo-credentials"')

    @mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: TEST_CREDENTIAL}, clear=False)
    @override_settings(EOD_DEPLOYMENT_MODE="production")
    def test_non_development_login_never_publishes_injected_demo_credential(self) -> None:
        presentation = development_demo_access_presentation(deployment_mode="production")
        self.assertIsNone(presentation)
        response = self.client.get("/accounts/login/")
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, TEST_CREDENTIAL)
        self.assertNotContains(response, 'data-development-demo-credentials')

    @mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: TEST_CREDENTIAL}, clear=False)
    @override_settings(EOD_DEPLOYMENT_MODE="development", ALLOWED_HOSTS=["127.0.0.1", "testserver"])
    def test_real_login_path_and_trusted_health_pass_for_both_demo_accounts(self) -> None:
        ensure_development_demo_accounts()
        reconcile_demo_access(require_injection=True)
        self.assertTrue(verify_development_demo_login_path())

        response = Client().get("/_health/", HTTP_HOST="127.0.0.1")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["development_authentication"], "verified")

    @mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: TEST_CREDENTIAL}, clear=False)
    @override_settings(EOD_DEPLOYMENT_MODE="development", ALLOWED_HOSTS=["127.0.0.1", "testserver"])
    def test_trusted_health_reuses_successful_authentication_while_account_state_is_unchanged(self) -> None:
        from apps.organizations import development_auth_smoke

        ensure_development_demo_accounts()
        reconcile_demo_access(require_injection=True)

        with mock.patch.object(
            development_auth_smoke,
            "authenticate",
            wraps=development_auth_smoke.authenticate,
        ) as authenticate_spy:
            first = Client().get("/_health/", HTTP_HOST="127.0.0.1")
            self.assertEqual(first.status_code, 200)
            self.assertEqual(authenticate_spy.call_count, len(DEMO_USERNAMES))

            second = Client().get("/_health/", HTTP_HOST="127.0.0.1")
            self.assertEqual(second.status_code, 200)
            self.assertEqual(authenticate_spy.call_count, len(DEMO_USERNAMES))

    @mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: ""}, clear=False)
    @override_settings(EOD_DEPLOYMENT_MODE="development", ALLOWED_HOSTS=["127.0.0.1", "testserver"])
    def test_trusted_health_fails_when_development_credential_is_missing(self) -> None:
        response = Client().get("/_health/", HTTP_HOST="127.0.0.1")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["development_authentication"], "failed")

    @mock.patch.dict("os.environ", {DEMO_ACCESS_ENV: TEST_CREDENTIAL}, clear=False)
    @override_settings(EOD_DEPLOYMENT_MODE="development", ALLOWED_HOSTS=["127.0.0.1", "testserver"])
    def test_trusted_health_invalidates_cached_success_when_account_becomes_inactive(self) -> None:
        ensure_development_demo_accounts()
        reconcile_demo_access(require_injection=True)

        first = Client().get("/_health/", HTTP_HOST="127.0.0.1")
        self.assertEqual(first.status_code, 200)

        user = get_user_model().objects.get(username="operator.demo")
        user.is_active = False
        user.save(update_fields=["is_active"])

        response = Client().get("/_health/", HTTP_HOST="127.0.0.1")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["development_authentication"], "failed")
