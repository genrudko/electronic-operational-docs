from django.core.management import call_command
from django.test import TestCase

from ..models import (
    AdjacentSubjectRelation,
    DispatchLevel,
    DispatchSubject,
    ManagementRevision,
    PublicationStatus,
    SupervisionRevision,
)


class DispatchingSeedTests(TestCase):
    def test_seed_is_idempotent(self):
        call_command("seed_demo_dispatching", verbosity=0)
        first = (
            DispatchLevel.objects.count(),
            DispatchSubject.objects.count(),
            ManagementRevision.objects.count(),
            SupervisionRevision.objects.count(),
            AdjacentSubjectRelation.objects.count(),
        )
        call_command("seed_demo_dispatching", verbosity=0)
        second = (
            DispatchLevel.objects.count(),
            DispatchSubject.objects.count(),
            ManagementRevision.objects.count(),
            SupervisionRevision.objects.count(),
            AdjacentSubjectRelation.objects.count(),
        )
        self.assertEqual(first, second)

    def test_seed_creates_expected_published_demo_records(self):
        call_command("seed_demo_dispatching", verbosity=0)
        self.assertGreaterEqual(DispatchLevel.objects.count(), 2)
        self.assertGreaterEqual(DispatchSubject.objects.count(), 3)
        self.assertEqual(
            ManagementRevision.objects.filter(status=PublicationStatus.PUBLISHED).count(),
            3,
        )
        self.assertEqual(
            SupervisionRevision.objects.filter(status=PublicationStatus.PUBLISHED).count(),
            4,
        )
        self.assertTrue(SupervisionRevision.objects.filter(is_information_only=True).exists())
