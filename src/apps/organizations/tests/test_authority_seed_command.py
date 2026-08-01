import importlib

from django.apps import apps as django_apps
from django.core.management import call_command
from django.test import TestCase

from apps.organizations.authority_models import (
    AuthorityDecision,
    AuthorityEvaluationRecord,
    ExternalPersonnelEngagement,
    OperationalAuthorityGrant,
)
from apps.organizations.models import Employee, Organization


class DemoAuthoritySeedCommandTests(TestCase):
    def assert_demo_authority_state(self) -> None:
        host = Organization.objects.get(code="DEMO")
        contractor = Organization.objects.get(code="DEMO-CONTRACTOR")
        external_employee = Employee.objects.get(
            organization=contractor,
            personnel_number="DEMO-EXT-001",
        )

        self.assertEqual(
            OperationalAuthorityGrant.objects.filter(organization=host).count(),
            4,
        )
        self.assertEqual(
            ExternalPersonnelEngagement.objects.filter(
                employee=external_employee,
                host_organization=host,
            ).count(),
            1,
        )
        evaluations = AuthorityEvaluationRecord.objects.filter(
            organization=host,
            subject_type="DEMO_SCENARIO",
        )
        self.assertEqual(evaluations.count(), 4)
        self.assertEqual(
            set(evaluations.values_list("decision", flat=True)),
            {
                AuthorityDecision.ALLOW,
                AuthorityDecision.DENY,
                AuthorityDecision.VERIFY,
            },
        )
        self.assertTrue(
            evaluations.filter(
                actor=external_employee,
                decision=AuthorityDecision.ALLOW,
            ).exists()
        )
        self.assertFalse(
            OperationalAuthorityGrant.objects.filter(
                basis_reference__icontains="приказ предприятия"
            ).exists()
        )
        self.assertEqual(
            OperationalAuthorityGrant.objects.filter(
                basis_reference__startswith="DEMO-ONLY"
            ).count(),
            4,
        )

    def test_seed_is_idempotent_and_covers_decisions(self) -> None:
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)
        call_command("seed_demo_personnel_authority", verbosity=0)
        call_command("seed_demo_personnel_authority", verbosity=0)

        self.assert_demo_authority_state()

    def test_forward_migration_populates_demo_database(self) -> None:
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)
        migration = importlib.import_module(
            "apps.organizations.migrations.0009_seed_demo_personnel_authority"
        )

        migration.seed_demo_authority(django_apps, None)
        migration.seed_demo_authority(django_apps, None)

        self.assert_demo_authority_state()
