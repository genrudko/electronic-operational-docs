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
from apps.organizations.management.commands.seed_demo_personnel_authority import (
    RIGHT_DEFINITIONS,
)
from apps.organizations.models import (
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    OperationalRightDefinition,
    Organization,
)


class DemoAuthoritySeedCommandTests(TestCase):
    def assert_demo_authority_state(self) -> None:
        host = Organization.objects.get(code="DEMO")
        contractor = Organization.objects.get(code="DEMO-CONTRACTOR")
        external_employee = Employee.objects.get(
            organization=contractor,
            personnel_number="DEMO-EXT-001",
        )
        host_employees = Employee.objects.filter(
            organization=host,
            personnel_number__startswith="DEMO-",
        )
        source_rights = EmployeeOperationalRight.objects.filter(
            employee__organization=host,
            source_file_sha256="d" * 64,
            is_active=True,
        )
        qualifications = EmployeeQualification.objects.filter(
            employee__organization=host,
            source_file_sha256="d" * 64,
            is_active=True,
        )
        linked_grants = OperationalAuthorityGrant.objects.filter(
            organization=host,
            source_operational_right__in=source_rights,
            is_active=True,
        )

        self.assertEqual(host_employees.count(), 17)
        self.assertEqual(qualifications.count(), 17)
        self.assertGreater(source_rights.count(), 100)
        self.assertEqual(linked_grants.count(), source_rights.count())
        expected_right_codes = [item[0] for item in RIGHT_DEFINITIONS]
        self.assertEqual(
            OperationalRightDefinition.objects.filter(
                code__in=expected_right_codes,
                is_active=True,
            ).count(),
            len(expected_right_codes),
        )
        self.assertTrue(
            source_rights.filter(source_marker="+1").exists()
        )
        self.assertTrue(
            source_rights.filter(
                right_definition__code="switching_operation",
                employee__personnel_number="DEMO-001",
            ).exists()
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
        self.assertGreaterEqual(evaluations.count(), 4)
        self.assertTrue(
            {
                AuthorityDecision.ALLOW,
                AuthorityDecision.DENY,
                AuthorityDecision.VERIFY,
            }.issubset(set(evaluations.values_list("decision", flat=True)))
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
            source_rights.filter(
                source_reference__startswith="DEMO-ONLY"
            ).count(),
            source_rights.count(),
        )

    def test_seed_is_idempotent_and_publishes_matrix(self) -> None:
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)
        call_command("seed_demo_personnel_authority", verbosity=0)
        first_right_count = EmployeeOperationalRight.objects.count()
        first_grant_count = OperationalAuthorityGrant.objects.count()

        call_command("seed_demo_personnel_authority", verbosity=0)

        self.assertEqual(EmployeeOperationalRight.objects.count(), first_right_count)
        self.assertEqual(OperationalAuthorityGrant.objects.count(), first_grant_count)
        self.assert_demo_authority_state()

    def test_matrix_publication_migration_populates_demo_database(self) -> None:
        call_command("seed_demo_organization", reset_passwords=True, verbosity=0)
        migration = importlib.import_module(
            "apps.organizations.migrations.0010_publish_demo_personnel_authority_matrix"
        )

        migration.publish_demo_matrix(django_apps, None)
        migration.publish_demo_matrix(django_apps, None)

        self.assert_demo_authority_state()
