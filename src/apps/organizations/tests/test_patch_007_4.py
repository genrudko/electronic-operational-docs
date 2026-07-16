from __future__ import annotations

from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.dispatching.models import DispatchLevel, DispatchSubject
from apps.equipment.models import EnergySite
from apps.organizations.models import (
    Division,
    DivisionEnergySiteService,
    DivisionServiceProfile,
    Employee,
    EmployeeEnergySiteAuthorization,
    OperationalReportingLine,
    Organization,
)


class Patch0074OrganizationalStructureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_dispatching", verbosity=0)
        cls.organization = Organization.objects.get(code="DEMO")
        cls.user = Employee.objects.get(personnel_number="DEMO-001").user

    def test_official_center_name_is_present(self):
        center = Division.objects.get(
            organization=self.organization,
            code="CENTER",
            name="ЦОТУиЭ ВЭС Невинномысск",
        )
        self.assertFalse(
            Division.objects.filter(
                organization=self.organization,
                code="CENTER_MANAGEMENT",
            ).exists()
        )
        self.assertEqual(
            Employee.objects.get(personnel_number="DEMO-003").division,
            center,
        )

    def test_blade_service_is_separate_sibling(self):
        center = Division.objects.get(organization=self.organization, code="CENTER")
        blade = Division.objects.get(organization=self.organization, code="BLADE_SERVICE")
        self.assertNotEqual(blade.parent, center)
        self.assertEqual(blade.parent, center.parent)

    def test_blade_profile_marks_cross_territory_service(self):
        profile = DivisionServiceProfile.objects.get(division__code="BLADE_SERVICE")
        self.assertTrue(profile.is_cross_territory)
        self.assertIn("не входит в ЦОТУиЭ", profile.service_scope)

    def test_three_internal_energy_sites_exist(self):
        sites = EnergySite.objects.filter(organization=self.organization, is_external=False)
        self.assertEqual(sites.count(), 3)
        self.assertSetEqual(
            set(sites.values_list("short_name", flat=True)),
            {"Кочубеевская ВЭС", "Кузьминская ВЭС", "ПС 330 кВ Барсуки"},
        )

    def test_division_service_matrix_is_explicit(self):
        services = DivisionEnergySiteService.objects.filter(
            division__organization=self.organization,
            is_active=True,
        )
        self.assertEqual(services.count(), 22)
        blade_sites = services.filter(division__code="BLADE_SERVICE")
        self.assertEqual(blade_sites.count(), 2)
        self.assertFalse(blade_sites.filter(energy_site__short_name="ПС 330 кВ Барсуки").exists())

    def test_direct_operational_reporting_is_explicit(self):
        line = OperationalReportingLine.objects.get(
            subordinate_division__code="OPS",
            is_active=True,
        )
        self.assertEqual(line.supervisor.personnel_number, "DEMO-003")
        self.assertEqual(
            line.supervisor.position.name,
            "Заместитель технического директора по оперативной работе",
        )
        self.assertEqual(line.relation_type, OperationalReportingLine.RelationType.DIRECT)

    def test_common_operational_staff_are_authorized_for_all_sites(self):
        for personnel_number in ("DEMO-001", "DEMO-002", "DEMO-012", "DEMO-013"):
            self.assertEqual(
                EmployeeEnergySiteAuthorization.objects.filter(
                    employee__personnel_number=personnel_number,
                    is_active=True,
                ).count(),
                3,
            )

    def test_directory_explains_hierarchy_and_service_relations(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:directory"))
        self.assertContains(response, "ЦОТУиЭ ВЭС Невинномысск")
        self.assertContains(response, "Отдельное подразделение")
        self.assertContains(response, "Энергообъекты и обслуживающие подразделения")
        self.assertContains(response, "Непосредственное оперативное руководство")
        self.assertContains(response, "Руководство центра")
        self.assertContains(response, "Кузьминская ВЭС")
        self.assertContains(response, "ПС 330 кВ Барсуки")

    def test_presentation_seed_is_idempotent(self):
        before = (
            Division.objects.count(),
            Employee.objects.count(),
            DivisionEnergySiteService.objects.count(),
            EmployeeEnergySiteAuthorization.objects.count(),
        )
        call_command("seed_demo_dispatching", verbosity=0)
        after = (
            Division.objects.count(),
            Employee.objects.count(),
            DivisionEnergySiteService.objects.count(),
            EmployeeEnergySiteAuthorization.objects.count(),
        )
        self.assertEqual(before, after)

    def test_cross_organization_service_relation_is_rejected(self):
        foreign = Organization.objects.create(code="FOREIGN", name="Другая организация")
        foreign_division = Division.objects.create(
            organization=foreign,
            code="UNIT",
            name="Чужое подразделение",
        )
        local_site = EnergySite.objects.get(code="demo-wpp")
        with self.assertRaises(ValidationError):
            DivisionEnergySiteService.objects.create(
                division=foreign_division,
                energy_site=local_site,
                service_kind=DivisionEnergySiteService.ServiceKind.MAINTENANCE,
                valid_from=date(2026, 1, 1),
            )

    def test_runtime_profile_protects_presentation_database(self):
        settings_source = (settings.BASE_DIR / "src/eod_config/settings.py").read_text(
            encoding="utf-8"
        )
        launcher = (settings.BASE_DIR / "scripts/run_dev.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('EOD_DATABASE_PROFILE = os.getenv("EOD_DATABASE_PROFILE"', settings_source)
        self.assertIn('EOD_ALLOW_SQLITE_PATH_OVERRIDE", False', settings_source)
        self.assertIn('$env:EOD_DATABASE_PROFILE = "presentation"', launcher)
        self.assertIn("Remove-Item Env:SQLITE_PATH", launcher)

    def test_dispatching_presentation_labels_use_center_scope(self):
        level = DispatchLevel.objects.get(code="station-operational")
        subject = DispatchSubject.objects.get(code="demo-station-shift")
        self.assertEqual(
            level.presentation_label,
            "Оперативно-технологический уровень ЦОТУиЭ ВЭС Невинномысск",
        )
        self.assertEqual(
            subject.presentation_label,
            "Оперативный персонал ЦОТУиЭ ВЭС Невинномысск",
        )
