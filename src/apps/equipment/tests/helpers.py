from django.core.management import call_command

from apps.organizations.models import Employee

from ..models import EquipmentAsset


class EquipmentDemoMixin:
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_equipment", verbosity=0)
        cls.employee = Employee.objects.select_related(
            "user",
            "organization",
            "division",
            "position",
            "workplace",
        ).get(user__username="operator.demo")
        cls.user = cls.employee.user
        cls.ktp = EquipmentAsset.objects.get(code="DEMO-KTP-01")
        cls.wtg = EquipmentAsset.objects.get(code="DEMO-WTG-01")
        cls.cell = EquipmentAsset.objects.get(code="DEMO-CELL-01")
