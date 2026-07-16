from __future__ import annotations

import os
import re
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

from apps.organizations.models import Employee  # noqa: E402

operator = Employee.objects.select_related("user").get(
    personnel_number="DEMO-001"
)
client = Client()
client.force_login(operator.user)

documents_page = client.get(reverse("documents:list")).content.decode("utf-8")
if "Без регистрационного номера" not in documents_page:
    raise SystemExit("The document list still uses the draft status as a number.")
if "<code>черновик</code>" in documents_page:
    raise SystemExit("The old lowercase draft number placeholder remains.")

account_page = client.get(reverse("organizations:account")).content.decode(
    "utf-8"
)
for marker in (
    "role-assignment direct",
    "role-assignment substituted",
    "role-assignment-basis",
    "Область действия",
):
    if marker not in account_page:
        raise SystemExit(f"Role presentation marker is missing: {marker}")

document_template = (
    ROOT / "src/templates/documents/detail.html"
).read_text(encoding="utf-8")
if 'class="document-actions"' not in document_template:
    raise SystemExit("Document actions are not grouped in one toolbar.")

normative_template = (
    ROOT / "src/templates/normatives/revision_detail.html"
).read_text(encoding="utf-8")
if normative_template.count("SHA-256 редакции") != 1:
    raise SystemExit("The revision SHA-256 label must occur exactly once.")
for marker in (
    "Технические реквизиты редакции",
    "revision-technical-details technical-only",
    "technical-traceability technical-only",
    'data-default-collapsed="true"',
):
    if marker not in normative_template:
        raise SystemExit(f"Normative technical marker is missing: {marker}")
if re.search(
    r"<details[^>]*technical-traceability[^>]*\sopen(?:\s|=|>)",
    normative_template,
    flags=re.DOTALL,
):
    raise SystemExit("Traceability disclosures must not start open.")

css = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
for marker in (
    "Patch 007.6: visual acceptance fixes.",
    ".site-card:hover",
    ".equipment-tree-row:hover",
    ".document-actions {",
    "flex-wrap: nowrap;",
    ".role-assignment.substituted",
    ".revision-technical-details",
):
    if marker not in css:
        raise SystemExit(f"Visual acceptance CSS marker is missing: {marker}")

script = (ROOT / "src/static/system/app.js").read_text(encoding="utf-8")
if "closeDefaultCollapsedDisclosures" not in script:
    raise SystemExit("Default-collapsed disclosure initializer is missing.")

print("EQUIPMENT_INTERACTIVE_SURFACES=PASSED")
print("DOCUMENT_ACTION_TOOLBAR=PASSED")
print("DOCUMENT_NUMBER_PLACEHOLDER=PASSED")
print("ROLE_ASSIGNMENT_PRESENTATION=PASSED")
print("NORMATIVE_TECHNICAL_DETAILS=PASSED")
print("TRACEABILITY_DEFAULT_COLLAPSED=PASSED")
print("PATCH_007_6_VISUAL_ACCEPTANCE_GATE_PASSED")
