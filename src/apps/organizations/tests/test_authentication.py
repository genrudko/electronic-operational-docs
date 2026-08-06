from datetime import date

from django.test import TestCase
from django.urls import reverse

from apps.organizations.models import AuthenticationEvent, ResponsibilityScope, Role, RoleAssignment
from tests.credential_fixtures import ephemeral_credential

from .factories import employee_with_user


class PersonalAuthenticationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.credential = ephemeral_credential("Authentication")
        cls.employee, cls.user = employee_with_user(credential=cls.credential)
        cls.scope = ResponsibilityScope.objects.create(
            organization=cls.employee.organization,
            code="STATION",
            name="Объект",
        )
        cls.role = Role.objects.create(code="operator", name="Оператор")
        RoleAssignment.objects.create(
            employee=cls.employee,
            role=cls.role,
            scope=cls.scope,
            valid_from=date(2026, 1, 1),
        )

    def test_directory_requires_authentication(self):
        response = self.client.get(reverse("organizations:directory"))
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("organizations:login"), response.url)

    def test_authenticated_employee_can_open_directory(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:directory"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.employee.organization.name)
        self.assertContains(response, self.employee.full_name)

    def test_successful_login_is_audited(self):
        logged_in = self.client.login(
            username=self.user.username,
            password=self.credential,
        )
        self.assertTrue(logged_in)
        event = AuthenticationEvent.objects.get(
            event_type=AuthenticationEvent.EventType.LOGIN_SUCCESS
        )
        self.assertEqual(event.user, self.user)
        self.assertEqual(event.employee, self.employee)
        self.assertEqual(event.username_snapshot, self.user.username)

    def test_failed_login_is_audited(self):
        invalid_credential = ephemeral_credential("InvalidAuthentication")
        logged_in = self.client.login(
            username=self.user.username,
            password=invalid_credential,
        )
        self.assertFalse(logged_in)
        event = AuthenticationEvent.objects.get(
            event_type=AuthenticationEvent.EventType.LOGIN_FAILURE
        )
        self.assertEqual(event.username_snapshot, self.user.username)
        self.assertIsNone(event.user)

    def test_logout_is_post_only_and_audited(self):
        self.client.force_login(self.user)
        get_response = self.client.get(reverse("organizations:logout"))
        self.assertEqual(get_response.status_code, 405)
        response = self.client.post(reverse("organizations:logout"))
        self.assertRedirects(response, reverse("system:home"))
        self.assertTrue(
            AuthenticationEvent.objects.filter(
                event_type=AuthenticationEvent.EventType.LOGOUT,
                user=self.user,
            ).exists()
        )

    def test_account_page_displays_effective_role(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:account"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.employee.full_name)
        self.assertContains(response, self.role.name)
