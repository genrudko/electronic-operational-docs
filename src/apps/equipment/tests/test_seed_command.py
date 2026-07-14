from django.core.management import call_command
from django.test import TestCase

from apps.normatives.models import (
    OrganizationConfigurationRevision,
)
from apps.normatives.models import (
    PublicationStatus as NormativePublicationStatus,
)

from ..models import (
    EnergySite,
    EquipmentAlias,
    EquipmentAsset,
    EquipmentNameRevision,
    EquipmentRelation,
    EquipmentType,
)


class EquipmentSeedTests(TestCase):
    def test_seed_is_idempotent_and_enables_equipment_module(self):
        call_command("seed_demo_equipment", verbosity=0)
        counts = (
            EnergySite.objects.count(),
            EquipmentType.objects.count(),
            EquipmentAsset.objects.count(),
            EquipmentNameRevision.objects.count(),
            EquipmentAlias.objects.count(),
            EquipmentRelation.objects.count(),
        )
        call_command("seed_demo_equipment", verbosity=0)
        self.assertEqual(
            counts,
            (
                EnergySite.objects.count(),
                EquipmentType.objects.count(),
                EquipmentAsset.objects.count(),
                EquipmentNameRevision.objects.count(),
                EquipmentAlias.objects.count(),
                EquipmentRelation.objects.count(),
            ),
        )
        configuration = OrganizationConfigurationRevision.objects.get(
            organization__code="DEMO",
            revision_number=2,
            status=NormativePublicationStatus.PUBLISHED,
        )
        self.assertTrue(
            configuration.configuration["modules"]["equipment"]
        )
