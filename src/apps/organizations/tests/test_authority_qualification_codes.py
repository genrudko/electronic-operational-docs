from datetime import date

from django.test import SimpleTestCase

from apps.organizations.authority_services import qualification_codes_for_model
from apps.organizations.models import EmployeeQualification


class AuthorityQualificationCodeTests(SimpleTestCase):
    def test_only_controlled_ascii_values_become_authority_codes(self) -> None:
        qualification = EmployeeQualification(
            personnel_category="оперативный персонал",
            electrical_safety_group="IV",
            voltage_scope="до и выше 1000 В",
            valid_from=date(2026, 1, 1),
        )

        self.assertEqual(
            qualification_codes_for_model(qualification),
            ("ELECTRICAL_SAFETY_GROUP:IV",),
        )

    def test_ascii_catalog_values_remain_stable_and_namespaced(self) -> None:
        qualification = EmployeeQualification(
            personnel_category="OPERATIVE",
            electrical_safety_group="V",
            voltage_scope="ABOVE_1000V",
            valid_from=date(2026, 1, 1),
        )

        self.assertEqual(
            qualification_codes_for_model(qualification),
            (
                "ELECTRICAL_SAFETY_GROUP:V",
                "PERSONNEL_CATEGORY:OPERATIVE",
                "VOLTAGE_SCOPE:ABOVE_1000V",
            ),
        )
