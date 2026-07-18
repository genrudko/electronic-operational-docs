from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.organizations.models import InterfacePreference

from .base import OperationalLogTestCase


class OperationalLogViewTests(OperationalLogTestCase):
    def setUp(self) -> None:
        self.client = Client()
        self.user = get_user_model().objects.get(username="operator.demo")

    def test_registry_requires_authentication(self) -> None:
        response = self.client.get(reverse("operational_log:registry"))
        self.assertEqual(response.status_code, 302)

    def test_registry_shows_journal_and_approved_form_source(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:registry"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Оперативные журналы")
        self.assertContains(response, "Оперативный журнал сменного персонала")
        self.assertContains(response, "Утверждённая форма является обязательным контрактом")
        self.assertContains(response, "И-00-007-ОР-2025")
        self.assertContains(response, "приложение № 2")

    def test_detail_uses_exact_three_column_approved_form(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Дата и время записи")
        self.assertContains(
            response,
            "Содержание записей в течение смены, подписи о приемке и сдаче смены",
        )
        self.assertContains(
            response,
            "Визы и замечания административно-технического персонала",
        )
        self.assertEqual(response.content.count(b'<th scope="col">'), 3)
        self.assertEqual(len(response.context["form_contract"].columns), 3)
        self.assertContains(response, 'data-approved-column="date_time"')
        self.assertContains(response, "width: 14%")
        self.assertContains(response, "width: 66%")
        self.assertContains(response, "width: 20%")

    def test_detail_preserves_chronological_order_and_links(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        text = response.content.decode("utf-8")
        self.assertLess(
            text.index("Демонстрационное дежурство начато"),
            text.index("Получена вымышленная информация"),
        )
        for marker in ("КТП-01", "ДЕМО-2026-000001", "Автор записи:", "№ 1", "№ 5"):
            self.assertIn(marker, text)

    def test_detail_does_not_replace_form_with_audit_cards(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        text = response.content.decode("utf-8")
        for forbidden in (
            "ХРОНОЛОГИЧЕСКАЯ ЛЕНТА",
            "Типизированных",
            "Свободных",
            "Целостность подтверждена",
            "Событие:",
            "Регистрация:",
            "operational-entry",
        ):
            self.assertNotIn(forbidden, text)

    def test_detail_has_print_contract_and_hides_technical_data_by_default(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(reverse("operational_log:detail", args=(self.journal.pk,)))
        self.assertContains(response, "Печать формы")
        self.assertContains(response, "data-approved-journal-form=")
        self.assertContains(response, "approved-journal-table")
        self.assertNotContains(response, "Технические реквизиты зарегистрированных записей")
        self.assertNotContains(response, "SHA-256")

    def test_ui_remains_read_only(self) -> None:
        self.client.force_login(self.user)
        registry = self.client.get(reverse("operational_log:registry")).content.decode("utf-8")
        detail = self.client.get(
            reverse("operational_log:detail", args=(self.journal.pk,))
        ).content.decode("utf-8")
        for forbidden in (
            "Создать запись",
            "Редактировать запись",
            "Аннулировать запись",
            "Исправить запись",
        ):
            self.assertNotIn(forbidden, registry + detail)

    def test_detail_defaults_to_compact_workspace(self) -> None:
        self.client.force_login(self.user)
        response = self.client.get(
            reverse("operational_log:detail", args=(self.journal.pk,))
        )
        self.assertContains(response, "journal-workspace-bar")
        self.assertContains(response, "journal-heading-compact")
        self.assertContains(response, "Настроить вид")
        self.assertContains(response, "journal-settings-dialog")
        self.assertContains(response, "Шапка и ширина")
        self.assertNotContains(response, "journal-heading-mode-form")
        self.assertNotContains(
            response,
            "Просмотр зарегистрированных записей по утверждённой форме.",
        )

    def test_display_settings_require_authentication(self) -> None:
        response = self.client.post(
            reverse("operational_log:update_display", args=(self.journal.pk,)),
            {
                "journal_heading_mode": (
                    InterfacePreference.JournalHeadingMode.FULL
                ),
                "journal_width": InterfacePreference.JournalWidth.WIDE,
                "journal_font_family": (
                    InterfacePreference.JournalFontFamily.SYSTEM
                ),
                "journal_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_time_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_date_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_table_header_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_title_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_density": InterfacePreference.JournalDensity.NORMAL,
                "journal_show_authors": "on",
                "journal_show_links": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_display_settings_post_saves_and_applies_all_preferences(
        self,
    ) -> None:
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("operational_log:update_display", args=(self.journal.pk,)),
            {
                "journal_heading_mode": (
                    InterfacePreference.JournalHeadingMode.FULL
                ),
                "journal_width": InterfacePreference.JournalWidth.FULL,
                "journal_font_family": (
                    InterfacePreference.JournalFontFamily.ARIAL
                ),
                "journal_font_size": (
                    InterfacePreference.JournalFontSize.LARGE
                ),
                "journal_time_font_size": (
                    InterfacePreference.JournalFontSize.SMALL
                ),
                "journal_date_font_size": (
                    InterfacePreference.JournalFontSize.EXTRA_LARGE
                ),
                "journal_table_header_font_size": (
                    InterfacePreference.JournalFontSize.LARGE
                ),
                "journal_title_font_size": (
                    InterfacePreference.JournalFontSize.EXTRA_LARGE
                ),
                "journal_density": (
                    InterfacePreference.JournalDensity.RELAXED
                ),
            },
        )
        self.assertRedirects(
            response,
            reverse("operational_log:detail", args=(self.journal.pk,)),
        )
        preference = InterfacePreference.objects.get(user=self.user)
        self.assertEqual(
            preference.journal_heading_mode,
            InterfacePreference.JournalHeadingMode.FULL,
        )
        self.assertEqual(
            preference.journal_font_family,
            InterfacePreference.JournalFontFamily.ARIAL,
        )
        self.assertEqual(
            preference.journal_font_size,
            InterfacePreference.JournalFontSize.LARGE,
        )
        self.assertEqual(
            preference.journal_time_font_size,
            InterfacePreference.JournalFontSize.SMALL,
        )
        self.assertEqual(
            preference.journal_date_font_size,
            InterfacePreference.JournalFontSize.EXTRA_LARGE,
        )
        self.assertEqual(
            preference.journal_table_header_font_size,
            InterfacePreference.JournalFontSize.LARGE,
        )
        self.assertEqual(
            preference.journal_title_font_size,
            InterfacePreference.JournalFontSize.EXTRA_LARGE,
        )
        self.assertEqual(
            preference.journal_density,
            InterfacePreference.JournalDensity.RELAXED,
        )
        self.assertEqual(
            preference.journal_width,
            InterfacePreference.JournalWidth.FULL,
        )
        self.assertFalse(preference.journal_show_authors)
        self.assertFalse(preference.journal_show_links)

        detail = self.client.get(
            reverse("operational_log:detail", args=(self.journal.pk,))
        )
        for marker in (
            "journal-heading-full",
            "journal-font-arial",
            "journal-size-large",
            "journal-entry-size-large",
            "journal-time-size-small",
            "journal-date-size-extra_large",
            "journal-table-header-size-large",
            "journal-title-size-extra_large",
            "journal-density-relaxed",
            "journal-main-width-full",
            "journal-authors-hidden",
            "journal-links-hidden",
        ):
            self.assertContains(detail, marker)

    def test_display_settings_post_rejects_unknown_choice(self) -> None:
        self.client.force_login(self.user)
        InterfacePreference.objects.get_or_create(user=self.user)
        response = self.client.post(
            reverse("operational_log:update_display", args=(self.journal.pk,)),
            {
                "journal_heading_mode": "FLOATING",
                "journal_width": InterfacePreference.JournalWidth.WIDE,
                "journal_font_family": (
                    InterfacePreference.JournalFontFamily.SYSTEM
                ),
                "journal_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_time_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_date_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_table_header_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_title_font_size": (
                    InterfacePreference.JournalFontSize.NORMAL
                ),
                "journal_density": InterfacePreference.JournalDensity.NORMAL,
                "journal_show_authors": "on",
                "journal_show_links": "on",
            },
        )
        self.assertEqual(response.status_code, 400)
        preference = InterfacePreference.objects.get(user=self.user)
        self.assertEqual(
            preference.journal_heading_mode,
            InterfacePreference.JournalHeadingMode.COMPACT,
        )
