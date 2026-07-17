from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.contrib.auth import get_user_model  # noqa: E402
from django.core.management import call_command  # noqa: E402
from django.test import Client  # noqa: E402
from django.urls import reverse  # noqa: E402

django.setup()

from apps.operational_log.form_contracts import (  # noqa: E402
    OPERATIONAL_JOURNAL_FORM,
)
from apps.operational_log.models import OperationalJournal  # noqa: E402
from apps.organizations.models import InterfacePreference  # noqa: E402

call_command("seed_demo_operational_log", verbosity=0)

user = get_user_model().objects.get(username="operator.demo")
journal = OperationalJournal.objects.get(
    organization__code="DEMO",
    code="shift-operational-log",
)
preferences, _ = InterfacePreference.objects.get_or_create(user=user)
preferences.journal_heading_mode = (
    InterfacePreference.JournalHeadingMode.COMPACT
)
preferences.journal_font_family = (
    InterfacePreference.JournalFontFamily.SYSTEM
)
preferences.journal_font_size = (
    InterfacePreference.JournalFontSize.NORMAL
)
preferences.journal_density = (
    InterfacePreference.JournalDensity.NORMAL
)
preferences.journal_width = InterfacePreference.JournalWidth.WIDE
preferences.journal_show_authors = True
preferences.journal_show_links = True
preferences.save()

assert tuple(
    column.title for column in OPERATIONAL_JOURNAL_FORM.columns
) == (
    "Дата и время записи",
    (
        "Содержание записей в течение смены, подписи "
        "о приемке и сдаче смены"
    ),
    (
        "Визы и замечания "
        "административно-технического персонала"
    ),
)
assert tuple(
    column.width_percent
    for column in OPERATIONAL_JOURNAL_FORM.columns
) == (14, 66, 20)
assert "И-00-007-ОР-2025" in OPERATIONAL_JOURNAL_FORM.source_reference
assert "приложение № 2" in OPERATIONAL_JOURNAL_FORM.source_reference
print("LOCAL_APPROVED_FORM_SOURCE=PASSED")

client = Client()
client.force_login(user)
detail_url = reverse("operational_log:detail", args=(journal.pk,))
update_url = reverse(
    "operational_log:update_display",
    args=(journal.pk,),
)

detail = client.get(detail_url)
assert detail.status_code == 200
detail_text = detail.content.decode("utf-8")
for marker in (
    "journal-workspace-bar",
    "journal-heading-compact",
    "journal-main-width-wide",
    'data-journal-heading-mode="compact"',
    "Настроить вид",
    "journal-settings-dialog",
    "Шапка и ширина",
    "Текст записей",
    "Служебные сведения",
    "Дата и время записи",
    "Визы и замечания административно-технического персонала",
):
    assert marker in detail_text, marker
for forbidden in (
    "journal-heading-mode-form",
    "Просмотр зарегистрированных записей по утверждённой форме.",
):
    assert forbidden not in detail_text, forbidden
print("JOURNAL_LOCAL_SETTINGS_DRAWER=PASSED")

response = client.post(
    update_url,
    {
        "journal_heading_mode": "FULL",
        "journal_width": "FULL",
        "journal_font_family": "TIMES",
        "journal_font_size": "EXTRA_LARGE",
        "journal_density": "RELAXED",
    },
)
assert response.status_code == 302
preferences.refresh_from_db()
assert (
    preferences.journal_heading_mode
    == InterfacePreference.JournalHeadingMode.FULL
)
assert (
    preferences.journal_width
    == InterfacePreference.JournalWidth.FULL
)
assert (
    preferences.journal_font_family
    == InterfacePreference.JournalFontFamily.TIMES
)
assert (
    preferences.journal_font_size
    == InterfacePreference.JournalFontSize.EXTRA_LARGE
)
assert (
    preferences.journal_density
    == InterfacePreference.JournalDensity.RELAXED
)
assert not preferences.journal_show_authors
assert not preferences.journal_show_links

customized = client.get(detail_url).content.decode("utf-8")
for marker in (
    "journal-heading-full",
    "journal-font-times",
    "journal-size-extra_large",
    "journal-density-relaxed",
    "journal-main-width-full",
    "journal-authors-hidden",
    "journal-links-hidden",
):
    assert marker in customized, marker
print("JOURNAL_DRAWER_PREFERENCES=PASSED")

invalid = client.post(
    update_url,
    {
        "journal_heading_mode": "FLOATING",
        "journal_width": "WIDE",
        "journal_font_family": "SYSTEM",
        "journal_font_size": "NORMAL",
        "journal_density": "NORMAL",
        "journal_show_authors": "on",
        "journal_show_links": "on",
    },
)
assert invalid.status_code == 400
preferences.refresh_from_db()
assert (
    preferences.journal_heading_mode
    == InterfacePreference.JournalHeadingMode.FULL
)
print("INVALID_JOURNAL_SETTINGS_REJECTED=PASSED")

account = client.get(reverse("organizations:account"))
assert account.status_code == 200
account_text = account.content.decode("utf-8")
for marker in (
    "Общий интерфейс системы",
    "Открыть настройки журнала",
    "Показывать технические реквизиты",
):
    assert marker in account_text, marker
for forbidden in (
    "Отображение оперативного журнала",
    "Режим шапки журнала",
    "Шрифт записей",
    "Плотность строк журнала",
    "Ширина журнала",
):
    assert forbidden not in account_text, forbidden
print("ACCOUNT_GENERAL_SETTINGS_ONLY=PASSED")

css_text = (ROOT / "src/static/system/app.css").read_text(
    encoding="utf-8"
)
for marker in (
    "/* Patch 010.2 Repair 2: настройки рядом с журналом */",
    ".journal-settings-dialog",
    ".journal-settings-dialog::backdrop",
    ".journal-heading-choice-grid",
    ".account-general-settings-grid",
    ".journal-heading-hidden > .approved-journal-heading",
    "@media print",
    "display: block !important;",
):
    assert marker in css_text, marker
for forbidden in (
    ".journal-heading-mode-form",
    ".journal-mode-button",
):
    assert forbidden not in css_text, forbidden
print("JOURNAL_DRAWER_VISUAL_CONTRACT=PASSED")
print("SCREEN_AND_PRINT_SEPARATION=PASSED")
print(
    "PATCH_010_2_REPAIR2_JOURNAL_LOCAL_SETTINGS_GATE_PASSED"
)
