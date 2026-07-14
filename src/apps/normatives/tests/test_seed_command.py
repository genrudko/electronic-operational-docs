from django.core.management import call_command
from django.test import TestCase

from ..models import (
    NormativeDocument,
    NormativeRequirement,
    NormativeRevision,
    OrganizationConfigurationRevision,
    OrganizationNameRevision,
    RequirementTrace,
)


class NormativeSeedTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed_demo_normatives", verbosity=0)
        counts = (
            NormativeDocument.objects.count(),
            NormativeRevision.objects.count(),
            NormativeRequirement.objects.count(),
            RequirementTrace.objects.count(),
            OrganizationNameRevision.objects.count(),
            OrganizationConfigurationRevision.objects.count(),
        )
        call_command("seed_demo_normatives", verbosity=0)
        self.assertEqual(
            counts,
            (
                NormativeDocument.objects.count(),
                NormativeRevision.objects.count(),
                NormativeRequirement.objects.count(),
                RequirementTrace.objects.count(),
                OrganizationNameRevision.objects.count(),
                OrganizationConfigurationRevision.objects.count(),
            ),
        )
