from datetime import datetime, timedelta

from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import (
    Employee,
    Organization,
    Workplace,
)

from ..models import (
    OperationalJournal,
    OperationalShift,
    ShiftStatus,
)


@override_settings(DEBUG=True)
class OperationalLogTestCase(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        call_command("seed_demo_operational_log", verbosity=0)
        cls.organization = Organization.objects.get(code="DEMO")
        cls.workplace = Workplace.objects.get(
            organization=cls.organization,
            code="SHIFT_POOL",
        )
        cls.actor = Employee.objects.select_related(
            "position",
            "workplace",
        ).get(
            organization=cls.organization,
            user__username="operator.demo",
        )
        cls.journal = OperationalJournal.objects.get(
            organization=cls.organization,
            code="shift-operational-log",
        )
        cls.shift = OperationalShift.objects.get(
            journal=cls.journal,
            status=ShiftStatus.OPEN,
        )
        cls.equipment = EquipmentAsset.objects.get(
            organization=cls.organization,
            code="DEMO-KTP-01",
        )
        cls.document = (
            Document.objects.filter(
                organization=cls.organization,
                status=Document.Status.REGISTERED,
            )
            .order_by("sequence_number")
            .first()
        )

    def event_time(self, minutes: int = 1) -> datetime:
        return timezone.now() - timedelta(minutes=minutes)

    def planned_period(
        self,
        *,
        offset_hours: int = 1,
    ) -> tuple[datetime, datetime]:
        start_at = timezone.now() - timedelta(hours=offset_hours)
        return start_at, start_at + timedelta(hours=12, minutes=15)
