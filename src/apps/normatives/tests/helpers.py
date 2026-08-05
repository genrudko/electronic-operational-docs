import os

from django.core.management import call_command

from apps.organizations.models import Employee


class NormativeDemoMixin:
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_organization", verbosity=0)
        call_command("seed_demo_normatives", verbosity=0)
        cls.employee = Employee.objects.select_related(
            "user",
            "organization",
            "division",
            "position",
            "workplace",
        ).get(user__username="operator.demo")
        cls.user = cls.employee.user
        cls.password = os.environ["EOD_DEMO_USER_PASSWORD"]
