import os

from django.contrib.auth import authenticate, get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.organizations.models import Employee, Organization


class PreviewReadinessTests(TestCase):
    def test_demo_seed_creates_authenticatable_linked_users(self):
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)

        user_model = get_user_model()
        usernames = ("operator.demo", "supervisor.demo")
        injected_password = os.environ["EOD_DEMO_USER_PASSWORD"]

        self.assertEqual(
            user_model.objects.filter(username__in=usernames, is_active=True).count(),
            2,
        )
        self.assertEqual(
            Employee.objects.filter(user__username__in=usernames, is_active=True).count(),
            2,
        )
        self.assertTrue(Organization.objects.filter(code="DEMO", is_active=True).exists())

        for username in usernames:
            with self.subTest(username=username):
                self.assertIsNotNone(
                    authenticate(username=username, password=injected_password)
                )
