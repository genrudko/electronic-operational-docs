from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ["DJANGO_ALLOWED_HOSTS"] = "127.0.0.1,localhost,testserver"
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.test import Client  # noqa: E402

django.setup()

from apps.equipment.models import EquipmentAsset  # noqa: E402
from apps.normatives.models import NormativeDocument  # noqa: E402
from apps.organizations.models import Employee, InterfacePreference  # noqa: E402

operator = Employee.objects.select_related("user").get(user__username="operator.demo")
preference, _ = InterfacePreference.objects.get_or_create(user=operator.user)
preference.theme = InterfacePreference.Theme.LIGHT
preference.show_technical_details = False
preference.save()

client = Client()
client.force_login(operator.user)
registry = client.get("/dispatching/")
if registry.status_code != 200:
    raise SystemExit("Реестр управления и ведения недоступен.")
registry_html = registry.content.decode("utf-8")
for marker in (
    "Диспетчерское управление",
    "Технологическое управление",
    "Технологическое ведение",
    "Информационное ведение",
):
    if marker not in registry_html:
        raise SystemExit(f"Не найдена нормативная подпись: {marker}")
for forbidden in (">Управляет<", ">Ведёт режим<"):
    if forbidden in registry_html:
        raise SystemExit(f"Обнаружена устаревшая подпись: {forbidden}")

first_equipment = EquipmentAsset.objects.filter(management_object__isnull=False).first()
if first_equipment is None:
    raise SystemExit("Не найден объект для проверки карточки управления.")
detail = client.get(f"/dispatching/equipment/{first_equipment.public_id}/")
if detail.status_code != 200:
    raise SystemExit("Карточка объекта управления недоступна.")
detail_html = detail.content.decode("utf-8")
for marker in ("Вид управления", "Вид ведения", "Основание"):
    if marker not in detail_html:
        raise SystemExit(f"Карточка объекта не содержит маркер: {marker}")

for path in ("/equipment/", "/normatives/"):
    response = client.get(path)
    if response.status_code != 200:
        raise SystemExit(f"Презентационная страница недоступна: {path}")
    html = response.content.decode("utf-8")
    if "PATCH 005" in html or "PATCH 006" in html:
        raise SystemExit(f"На странице {path} осталась техническая подпись патча.")

normative = NormativeDocument.objects.get(code="demo-electronic-documentation")
if "Правила технической эксплуатации" not in normative.title:
    raise SystemExit("Презентационный нормативный документ не использует узнаваемое наименование ПТЭ.")

css = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
for marker in (
    "Patch 007.3: theme surface repair",
    "--topbar-bg",
    ".presentation-topbar",
    ".technical-disclosure",
):
    if marker not in css:
        raise SystemExit(f"Не найден CSS-маркер Patch 007.3: {marker}")

settings_source = (ROOT / "src/eod_config/settings.py").read_text(encoding="utf-8")
for marker in ("presentation.sqlite3", "gate_runtime.sqlite3", "Path(sys.argv[0]).name"):
    if marker not in settings_source:
        raise SystemExit(f"Не найден маркер разделения SQLite-профилей: {marker}")

document_template = (ROOT / "src/templates/documents/detail.html").read_text(encoding="utf-8")
for marker in ("Технические сведения о проверке", "История версий", "Системный аудит"):
    if marker not in document_template:
        raise SystemExit(f"Карточка документа не содержит сворачиваемый блок: {marker}")

print("LIGHT_THEME_SURFACE_CONTRACT=PASSED")
print("DISPATCHING_AND_TECHNOLOGICAL_TERMINOLOGY=PASSED")
print("INFORMATIONAL_SUPERVISION_CHARACTERISTIC=PASSED")
print("CLEAN_PRESENTATION_LABELS=PASSED")
print("SEPARATE_SQLITE_PROFILES=PASSED")
print("COLLAPSIBLE_TECHNICAL_DETAILS=PASSED")
print("PATCH_007_3_THEME_TERMINOLOGY_PROFILE_GATE_PASSED")
