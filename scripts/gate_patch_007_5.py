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

from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

from apps.documents.models import Document  # noqa: E402
from apps.equipment.models import EnergySite  # noqa: E402
from apps.organizations.models import (  # noqa: E402
    Division,
    Employee,
    InterfacePreference,
)

operator = Employee.objects.select_related("user", "position").get(
    personnel_number="DEMO-001"
)
preferences = InterfacePreference.objects.get(user=operator.user)
if preferences.theme != InterfacePreference.Theme.LIGHT:
    raise SystemExit("Presentation users must start with the light theme.")
if preferences.show_technical_details:
    raise SystemExit("Technical details must be disabled for presentation users.")

chief_block = Division.objects.get(code="CHIEF_ENGINEER_BLOCK")
if chief_block.name != "Блок ЗГД — главного инженера":
    raise SystemExit("The official chief engineer block name is not used.")

client = Client()
client.force_login(operator.user)

home = client.get(reverse("system:home")).content.decode("utf-8")
if operator.full_name not in home:
    raise SystemExit("The header does not show the employee full name.")
if "operator.demo" in home:
    raise SystemExit("The presentation header still exposes the login.")
if 'data-technical="false"' not in home:
    raise SystemExit("Technical presentation mode is not disabled.")

for view_name in ("organizations:directory", "normatives:registry"):
    page = client.get(reverse(view_name)).content.decode("utf-8")
    if 'class="nav-menu active"' not in page:
        raise SystemExit(
            f"The reference navigation is not active on {view_name}."
        )

draft = Document.objects.filter(status=Document.Status.DRAFT).first()
if draft is None:
    raise SystemExit("A presentation draft document is required.")
draft_html = client.get(
    reverse("documents:detail", args=[draft.public_id])
).content.decode("utf-8")
if "Черновик без регистрационного номера" not in draft_html:
    raise SystemExit("The draft page still uses an internal label.")
if f"Черновик <code>{draft.public_id}</code>" in draft_html:
    raise SystemExit("The draft UUID is still the primary visible label.")

site = EnergySite.objects.get(code="demo-wpp")
site_html = client.get(
    reverse("equipment:site_detail", args=[site.code])
).content.decode("utf-8")
if "Системный код</dt><dd><code>" in site_html:
    raise SystemExit("The energy-site code is still always visible.")
if '<dt class="technical-only">Системный код</dt>' not in site_html:
    raise SystemExit("The energy-site code is not marked as technical.")
if '<code class="technical-only">' not in site_html:
    raise SystemExit("Equipment codes are not marked as technical.")

dispatching = client.get(reverse("dispatching:registry")).content.decode(
    "utf-8"
)
for marker in (
    "Оборудование с назначенным управлением",
    "Оборудование с назначенным ведением",
    "В том числе информационное ведение",
):
    if marker not in dispatching:
        raise SystemExit(f"Dispatching summary marker is missing: {marker}")

base_template = (ROOT / "src/templates/base.html").read_text(
    encoding="utf-8"
)
for marker in (
    "user_display_name",
    "user_display_role",
    "request.resolver_match.namespace == 'normatives'",
):
    if marker not in base_template:
        raise SystemExit(f"Base presentation marker is missing: {marker}")

normative_templates = []
for template_path in sorted(
    (ROOT / "src/templates/normatives").glob("*.html")
):
    source = template_path.read_text(encoding="utf-8")
    if "Техническая трассируемость" in source:
        normative_templates.append(template_path)
if len(normative_templates) != 1:
    raise SystemExit(
        "Expected one normative traceability template, "
        f"got {len(normative_templates)}."
    )
normative_source = normative_templates[0].read_text(encoding="utf-8")
if "technical-traceability technical-only" not in normative_source:
    raise SystemExit("Normative traceability is not technical-only.")
if "Связь с реализацией и испытаниями</h3>" in normative_source:
    raise SystemExit("The old expanded traceability heading remains.")

css_source = (ROOT / "src/static/system/app.css").read_text(
    encoding="utf-8"
)
for marker in (
    'html[data-technical="false"] .technical-only',
    ".nav-menu.active > summary",
    ".user-menu-identity",
):
    if marker not in css_source:
        raise SystemExit(f"Presentation CSS marker is missing: {marker}")

equipment_seed = (
    ROOT / "src/apps/equipment/management/commands/seed_demo_equipment.py"
).read_text(encoding="utf-8")
for forbidden in (
    "ячейка № 1 КЛ 35 кВ КТП-01",
    "комплект РЗА ячейки № 1 КЛ 35 кВ",
):
    if forbidden in equipment_seed:
        raise SystemExit(f"Lowercase dispatcher name remains: {forbidden}")

print("PRESENTATION_DEFAULTS=PASSED")
print("HUMAN_USER_HEADER=PASSED")
print("REFERENCE_NAVIGATION_STATE=PASSED")
print("TECHNICAL_DETAILS_POLICY=PASSED")
print("OFFICIAL_ORGANIZATION_NAME=PASSED")
print("OPERATIONAL_SUMMARY_LABELS=PASSED")
print("NORMATIVE_TRACEABILITY_DISCLOSURE=PASSED")
print("PATCH_007_5_CLEAN_PRESENTATION_GATE_PASSED")
