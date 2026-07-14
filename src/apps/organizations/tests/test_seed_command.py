from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase

from apps.organizations.models import Employee, Organization, Role, RoleAssignment, Substitution


class DemoSeedCommandTests(TestCase):
    def test_seed_is_idempotent_and_creates_personal_accounts(self):
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)

        self.assertEqual(Organization.objects.filter(code="DEMO").count(), 1)
        users = get_user_model().objects.filter(username__endswith=".demo")
        self.assertEqual(users.count(), 2)
        self.assertEqual(Employee.objects.filter(user__in=users).count(), 2)
        self.assertEqual(Role.objects.filter(is_system=True).count(), 3)
        self.assertGreaterEqual(RoleAssignment.objects.count(), 3)
        self.assertEqual(Substitution.objects.filter(is_active=True).count(), 1)
