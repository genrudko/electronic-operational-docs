from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402

from apps.dispatching.models import DispatchLevel, DispatchSubject  # noqa: E402
from apps.equipment.models import EnergySite  # noqa: E402
from apps.organizations.models import (  # noqa: E402
    Division,
    DivisionEnergySiteService,
    DivisionServiceProfile,
    Employee,
    EmployeeEnergySiteAuthorization,
    OperationalReportingLine,
    Organization,
)

organization = Organization.objects.get(code="DEMO")
center = Division.objects.get(organization=organization, code="CENTER")
blade = Division.objects.get(organization=organization, code="BLADE_SERVICE")
if center.name != "ЦОТУиЭ ВЭС Невинномысск":
    raise SystemExit("Official center abbreviation is not used.")
if Division.objects.filter(organization=organization, code="CENTER_MANAGEMENT").exists():
    raise SystemExit("Center leadership must not be modeled as a separate structural division.")
if Employee.objects.get(personnel_number="DEMO-003").division_id != center.pk:
    raise SystemExit("Operational deputy must belong directly to the center.")
if blade.parent_id == center.pk or blade.parent_id != center.parent_id:
    raise SystemExit("Blade service must be a separate sibling of the center.")

blade_profile = DivisionServiceProfile.objects.get(division=blade)
if not blade_profile.is_cross_territory or "не входит в ЦОТУиЭ" not in blade_profile.service_scope:
    raise SystemExit("Blade service territorial profile is incomplete.")

sites = EnergySite.objects.filter(organization=organization, is_external=False)
if sites.count() != 3:
    raise SystemExit("Exactly three internal presentation energy sites are required.")
site_names = set(sites.values_list("short_name", flat=True))
expected_sites = {"Кочубеевская ВЭС", "Кузьминская ВЭС", "ПС 330 кВ Барсуки"}
if site_names != expected_sites:
    raise SystemExit(f"Unexpected energy-site set: {sorted(site_names)}")

services = DivisionEnergySiteService.objects.filter(
    division__organization=organization,
    is_active=True,
)
if services.count() != 22:
    raise SystemExit(f"Expected 22 division-to-site service links, got {services.count()}.")
if services.filter(division=blade).count() != 2:
    raise SystemExit("Blade service must serve the two wind power plants.")

reporting_line = OperationalReportingLine.objects.get(
    subordinate_division__code="OPS",
    is_active=True,
)
if reporting_line.supervisor.personnel_number != "DEMO-003":
    raise SystemExit("Operational service supervisor is incorrect.")
if reporting_line.supervisor.position.name != (
    "Заместитель технического директора по оперативной работе"
):
    raise SystemExit("Operational superior position is incorrect.")

operational_staff = Employee.objects.filter(
    organization=organization,
    personnel_number__in=("DEMO-001", "DEMO-002", "DEMO-012", "DEMO-013"),
)
if operational_staff.count() != 4:
    raise SystemExit("Expected four presentation operational employees.")
for employee in operational_staff:
    if employee.energy_site_authorizations.filter(is_active=True).count() != 3:
        raise SystemExit(f"Employee {employee.personnel_number} is not authorized for all sites.")
if EmployeeEnergySiteAuthorization.objects.filter(employee__organization=organization).count() != 12:
    raise SystemExit("Expected twelve presentation energy-site authorizations.")

level = DispatchLevel.objects.get(organization=organization, code="station-operational")
subject = DispatchSubject.objects.get(organization=organization, code="demo-station-shift")
if level.presentation_label != (
    "Оперативно-технологический уровень ЦОТУиЭ ВЭС Невинномысск"
):
    raise SystemExit("Technological level presentation label is incorrect.")
if subject.presentation_label != "Оперативный персонал ЦОТУиЭ ВЭС Невинномысск":
    raise SystemExit("Operational personnel presentation label is incorrect.")

settings_source = (ROOT / "src/eod_config/settings.py").read_text(encoding="utf-8")
launcher = (ROOT / "scripts/run_dev.ps1").read_text(encoding="utf-8-sig")
for marker in (
    'EOD_DATABASE_PROFILE = os.getenv("EOD_DATABASE_PROFILE"',
    'EOD_ALLOW_SQLITE_PATH_OVERRIDE", False',
    'default_name = "presentation.sqlite3"',
    'default_name = "gate_runtime.sqlite3"',
):
    if marker not in settings_source:
        raise SystemExit(f"Runtime database marker is missing: {marker}")
for marker in (
    '$env:EOD_DATABASE_PROFILE = "presentation"',
    '$env:EOD_ALLOW_SQLITE_PATH_OVERRIDE = "0"',
    "Remove-Item Env:SQLITE_PATH",
    "data\\presentation.sqlite3",
):
    if marker not in launcher:
        raise SystemExit(f"Launcher database marker is missing: {marker}")

if getattr(settings, "EOD_DATABASE_PROFILE", "") not in {
    "presentation",
    "development",
    "gate",
    "explicit",
}:
    raise SystemExit("Unknown active database profile.")

directory_template = (ROOT / "src/templates/organizations/directory.html").read_text(
    encoding="utf-8"
)
for marker in (
    "Организационная иерархия",
    "Отдельное подразделение",
    "Энергообъекты и обслуживающие подразделения",
    "Непосредственное оперативное руководство",
    "Допуски к работе на энергообъектах",
):
    if marker not in directory_template:
        raise SystemExit(f"Organization directory marker is missing: {marker}")

print(f"DIVISION_COUNT={Division.objects.filter(organization=organization).count()}")
print(f"EMPLOYEE_COUNT={Employee.objects.filter(organization=organization).count()}")
print(f"INTERNAL_ENERGY_SITE_COUNT={sites.count()}")
print(f"DIVISION_SITE_SERVICE_COUNT={services.count()}")
print(f"EMPLOYEE_SITE_AUTHORIZATION_COUNT={EmployeeEnergySiteAuthorization.objects.count()}")
print("OFFICIAL_CENTER_STRUCTURE=PASSED")
print("SEPARATE_BLADE_SERVICE_PROFILE=PASSED")
print("MULTI_SITE_PERSONNEL_AUTHORIZATION=PASSED")
print("DIRECT_OPERATIONAL_REPORTING=PASSED")
print("PRESENTATION_RUNTIME_PROFILE=PASSED")
print("PATCH_007_4_ORGANIZATIONAL_STRUCTURE_GATE_PASSED")
