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
from django import forms  # noqa: E402
from django.test import Client  # noqa: E402
from django.test.utils import (  # noqa: E402
    setup_test_environment,
    teardown_test_environment,
)
from django.urls import reverse  # noqa: E402

django.setup()

from apps.documents.forms import DocumentDraftForm  # noqa: E402
from apps.equipment.models import EquipmentAsset  # noqa: E402
from apps.organizations.models import Employee  # noqa: E402

employee = Employee.objects.select_related("user").get(
    user__username="operator.demo"
)

# django.test.Client() only works against hosts listed in
# settings.ALLOWED_HOSTS. The Django test runner (manage.py test /
# DiscoverRunner.run_tests) adds 'testserver' automatically via
# setup_test_environment(). This script runs outside that runner, so we
# bracket the HTTP calls with the same helper instead of hand-editing
# ALLOWED_HOSTS, keeping this gate faithful to how Django itself runs
# Client-based checks.
setup_test_environment()
try:
    client = Client()
    client.force_login(employee.user)

    response = client.get(
        reverse("equipment:selector_options"),
        {"q": "КТП 1"},
    )
    if response.status_code != 200:
        raise SystemExit(f"Selector endpoint returned {response.status_code}.")
    payload = response.json()
    if payload["page_size"] != 50:
        raise SystemExit("Selector page size must be 50.")
    if payload["total"] != 1:
        raise SystemExit("Alias search did not resolve exactly one equipment item.")
    if payload["items"][0]["code"] != "DEMO-KTP-01":
        raise SystemExit("Alias search returned unexpected equipment.")
    if not payload["filters"]["categories"]:
        raise SystemExit("Selector categories are missing.")
finally:
    teardown_test_environment()

form = DocumentDraftForm(employee=employee)
if not isinstance(
    form.fields["equipment_assets"].widget,
    forms.MultipleHiddenInput,
):
    raise SystemExit("Document form still uses a visible multiple select.")

template = (ROOT / "src/templates/documents/form.html").read_text(
    encoding="utf-8"
)
javascript = (ROOT / "src/static/system/app.js").read_text(encoding="utf-8")
css = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
for marker in (
    "СЕРВЕРНЫЙ СЕЛЕКТОР",
    "data-equipment-selector",
    "data-equipment-categories",
    "data-equipment-load-more",
):
    if marker not in template:
        raise SystemExit(f"Selector template marker is missing: {marker}")
if "<select multiple" in template:
    raise SystemExit("The old visible multiple select remains in the template.")
for marker in (
    "const selected = new Map()",
    "URLSearchParams",
    "page: String(currentPage)",
    "equipment-category-button",
):
    if marker not in javascript:
        raise SystemExit(f"Selector JavaScript marker is missing: {marker}")
for marker in (
    "Patch 006.1",
    ".equipment-selector-dialog",
    ".equipment-category-button.active",
):
    if marker not in css:
        raise SystemExit(f"Selector CSS marker is missing: {marker}")

print(f"SELECTOR_AVAILABLE_ASSET_COUNT={EquipmentAsset.objects.count()}")
print("SERVER_SIDE_SEARCH=PASSED")
print("CATEGORY_FILTERS=PASSED")
print("FIFTY_ITEM_PAGINATION=PASSED")
print("HIDDEN_SELECTION_FIELD=PASSED")
print("PATCH_006_1_SCALABLE_EQUIPMENT_SELECTOR_GATE_PASSED")
