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

from apps.dispatching.models import DispatchLevel, DispatchSubject  # noqa: E402
from apps.equipment.models import (  # noqa: E402
    EnergySite,
    EquipmentNameRevision,
    PublicationStatus,
)
from apps.organizations.models import (  # noqa: E402
    Employee,
    InterfacePreference,
    Organization,
)

organization = Organization.objects.get(code="DEMO")
operator = Employee.objects.select_related("user").get(user__username="operator.demo")
if "Кочубеевская ВЭС" not in organization.name:
    raise SystemExit("Презентационное наименование организации не применено.")
if operator.full_name != "Кузнецов Илья Андреевич":
    raise SystemExit("Безопасное естественное демонстрационное ФИО не применено.")
if EnergySite.objects.filter(short_name="Кочубеевская ВЭС").count() != 1:
    raise SystemExit("Презентационный энергообъект не создан.")
if not EquipmentNameRevision.objects.filter(
    status=PublicationStatus.PUBLISHED,
    dispatcher_name__icontains="Кочубеевской ВЭС",
).exists():
    raise SystemExit("Узнаваемые диспетчерские наименования не опубликованы.")

level = DispatchLevel.objects.get(organization=organization, code="station-operational")
station_subject = DispatchSubject.objects.get(
    organization=organization,
    code="demo-station-shift",
)
if level.name != "Оперативно-технологический уровень Демо-ВЭС":
    raise SystemExit("Опубликованный уровень был неожиданно изменён.")
if level.presentation_label != "Оперативно-технологический уровень Кочубеевской ВЭС":
    raise SystemExit("Презентационная подпись уровня не применяется.")
if station_subject.short_name != "Смена Демо-ВЭС":
    raise SystemExit("Опубликованный субъект был неожиданно изменён.")
if station_subject.presentation_label != "Смена Кочубеевской ВЭС":
    raise SystemExit("Презентационная подпись субъекта не применяется.")

supervisor = Employee.objects.select_related("user").get(user__username="supervisor.demo")
default_preference, _ = InterfacePreference.objects.get_or_create(user=supervisor.user)
if default_preference.show_technical_details:
    raise SystemExit("Технические реквизиты должны быть скрыты по умолчанию.")

preference, _ = InterfacePreference.objects.get_or_create(user=operator.user)
preference.theme = InterfacePreference.Theme.LIGHT
preference.density = InterfacePreference.Density.COMPACT
preference.font_scale = InterfacePreference.FontScale.LARGE
preference.content_width = InterfacePreference.ContentWidth.WIDE
preference.show_technical_details = True
preference.save()

client = Client()
client.force_login(operator.user)
for path in ("/", "/accounts/me/", "/dispatching/", "/dispatching/subjects/"):
    response = client.get(path)
    if response.status_code != 200:
        raise SystemExit(f"Пользовательская страница недоступна: {path} status={response.status_code}")

home = client.get("/").content.decode("utf-8")
registry = client.get("/dispatching/").content.decode("utf-8")
account = client.get("/accounts/me/").content.decode("utf-8")
if "STAGE 2" in home or "PATCH 007" in home or "PATCH 007" in registry:
    raise SystemExit("Служебные подписи этапов остались в пользовательском интерфейсе.")
for marker in ("module-launcher", "icons.svg#icon-home", 'data-theme="light"'):
    if marker not in home:
        raise SystemExit(f"Не найден маркер презентационного интерфейса: {marker}")
for marker in (
    "dispatching-object-card",
    "Управляет",
    "Ведёт режим",
    "Смена Кочубеевской ВЭС",
):
    if marker not in registry:
        raise SystemExit(f"Не найден маркер упрощённого реестра: {marker}")
if "Показывать технические реквизиты" not in account:
    raise SystemExit("Персональные настройки интерфейса недоступны.")

css = (ROOT / "src/static/system/app.css").read_text(encoding="utf-8")
script = (ROOT / "src/static/system/app.js").read_text(encoding="utf-8")
sprite = (ROOT / "src/static/system/icons.svg").read_text(encoding="utf-8")
for marker in ('[data-technical="false"] .technical-only', 'html[data-theme="light"]'):
    if marker not in css:
        raise SystemExit(f"CSS-контракт настроек не выполнен: {marker}")
if "data-nav-toggle" not in script:
    raise SystemExit("Скрипт компактной навигации не подключён.")
for marker in ("icon-management", "icon-supervision", "icon-settings"):
    if marker not in sprite:
        raise SystemExit(f"В SVG-спрайте отсутствует символ: {marker}")

print(f"INTERFACE_PREFERENCE_COUNT={InterfacePreference.objects.count()}")
presentation_name_count = EquipmentNameRevision.objects.filter(
    status=PublicationStatus.PUBLISHED,
    dispatcher_name__icontains="Кочубеевской ВЭС",
).count()
print(f"PRESENTATION_DISPATCHER_NAME_COUNT={presentation_name_count}")
print("PERSONAL_INTERFACE_SETTINGS=PASSED")
print("TECHNICAL_DETAILS_HIDDEN_BY_DEFAULT=PASSED")
print("PRESENTATION_DEMO_PROFILE=PASSED")
print("PUBLISHED_DISPATCHING_REGISTRY_PRESERVED=PASSED")
print("SEMANTIC_CARD_LAYOUT=PASSED")
print("LOCAL_SVG_ICON_SYSTEM=PASSED")
print("PATCH_007_2_PRESENTATION_UX_GATE_PASSED")
