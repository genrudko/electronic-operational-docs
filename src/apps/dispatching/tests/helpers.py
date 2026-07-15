from django.core.management import call_command

from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee

from ..models import DispatchLevel, DispatchSubject


class DispatchingDemoMixin:
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_dispatching", verbosity=0)
        cls.employee = Employee.objects.select_related("user", "organization").get(
            user__username="operator.demo"
        )
        cls.user = cls.employee.user
        cls.organization = cls.employee.organization
        cls.ktp = EquipmentAsset.objects.get(code="DEMO-KL35-01")
        cls.wtg = EquipmentAsset.objects.get(code="DEMO-WTG-01")
        cls.regional_level = DispatchLevel.objects.get(code="regional-dispatch")
        cls.station_level = DispatchLevel.objects.get(code="station-operational")
        cls.regional_subject = DispatchSubject.objects.get(code="demo-regional-center")
        cls.station_subject = DispatchSubject.objects.get(code="demo-station-shift")
