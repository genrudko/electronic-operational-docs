from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse

from apps.dispatching.models import DispatchLevel, DispatchSubject
from apps.organizations.context_processors import interface_preferences
from apps.organizations.models import Employee, InterfacePreference, Organization

from .factories import employee_with_user


class InterfacePreferenceModelTests(TestCase):
    def test_defaults_hide_technical_details(self):
        user = get_user_model().objects.create_user(username="ui-default")
        preference = InterfacePreference.objects.create(user=user)
        self.assertEqual(preference.theme, InterfacePreference.Theme.DARK)
        self.assertEqual(preference.density, InterfacePreference.Density.COMFORTABLE)
        self.assertEqual(preference.font_scale, InterfacePreference.FontScale.NORMAL)
        self.assertFalse(preference.show_technical_details)
        self.assertEqual(
            preference.journal_heading_mode,
            InterfacePreference.JournalHeadingMode.COMPACT,
        )
        self.assertEqual(
            preference.journal_font_family,
            InterfacePreference.JournalFontFamily.SYSTEM,
        )
        self.assertEqual(
            preference.journal_font_size,
            InterfacePreference.JournalFontSize.NORMAL,
        )
        self.assertEqual(
            preference.journal_time_font_size,
            InterfacePreference.JournalFontSize.NORMAL,
        )
        self.assertEqual(
            preference.journal_date_font_size,
            InterfacePreference.JournalFontSize.NORMAL,
        )
        self.assertEqual(
            preference.journal_table_header_font_size,
            InterfacePreference.JournalFontSize.NORMAL,
        )
        self.assertEqual(
            preference.journal_title_font_size,
            InterfacePreference.JournalFontSize.NORMAL,
        )
        self.assertEqual(
            preference.journal_density,
            InterfacePreference.JournalDensity.NORMAL,
        )
        self.assertEqual(
            preference.journal_width,
            InterfacePreference.JournalWidth.WIDE,
        )
        self.assertTrue(preference.journal_show_authors)
        self.assertTrue(preference.journal_show_links)
        self.assertFalse(preference.journal_simplified_time_input)

    def test_preference_is_one_to_one_with_user(self):
        user = get_user_model().objects.create_user(username="ui-unique")
        InterfacePreference.objects.create(user=user)
        with self.assertRaises(ValidationError):
            InterfacePreference.objects.create(user=user)


class InterfacePreferenceViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employee, cls.user = employee_with_user(username="ui-user")

    def _valid_payload(self) -> dict[str, str]:
        return {
            "theme": InterfacePreference.Theme.LIGHT,
            "density": InterfacePreference.Density.COMPACT,
            "font_scale": InterfacePreference.FontScale.LARGE,
            "content_width": InterfacePreference.ContentWidth.WIDE,
            "show_technical_details": "on",
        }

    def test_account_page_contains_only_general_interface_form(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:account"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Общий интерфейс системы")
        self.assertContains(response, "Показывать технические реквизиты")
        self.assertContains(response, "Открыть настройки журнала")
        self.assertNotContains(response, "Отображение оперативного журнала")
        self.assertNotContains(response, "Режим шапки журнала")
        self.assertNotContains(response, "Шрифт записей")

    def test_post_saves_general_preferences_and_preserves_journal_settings(self):
        InterfacePreference.objects.create(
            user=self.user,
            journal_heading_mode=InterfacePreference.JournalHeadingMode.HIDDEN,
            journal_font_family=InterfacePreference.JournalFontFamily.ARIAL,
            journal_font_size=InterfacePreference.JournalFontSize.LARGE,
            journal_time_font_size=InterfacePreference.JournalFontSize.SMALL,
            journal_date_font_size=InterfacePreference.JournalFontSize.EXTRA_LARGE,
            journal_table_header_font_size=InterfacePreference.JournalFontSize.LARGE,
            journal_title_font_size=InterfacePreference.JournalFontSize.EXTRA_LARGE,
            journal_density=InterfacePreference.JournalDensity.COMPACT,
            journal_width=InterfacePreference.JournalWidth.FULL,
            journal_show_authors=False,
            journal_show_links=False,
        )
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("organizations:account"),
            self._valid_payload(),
        )
        self.assertRedirects(response, reverse("organizations:account"))
        preference = InterfacePreference.objects.get(user=self.user)
        self.assertEqual(preference.theme, InterfacePreference.Theme.LIGHT)
        self.assertEqual(preference.density, InterfacePreference.Density.COMPACT)
        self.assertEqual(preference.font_scale, InterfacePreference.FontScale.LARGE)
        self.assertTrue(preference.show_technical_details)
        self.assertEqual(
            preference.journal_heading_mode,
            InterfacePreference.JournalHeadingMode.HIDDEN,
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
            InterfacePreference.JournalDensity.COMPACT,
        )
        self.assertEqual(
            preference.journal_width,
            InterfacePreference.JournalWidth.FULL,
        )
        self.assertFalse(preference.journal_show_authors)
        self.assertFalse(preference.journal_show_links)

    def test_invalid_post_does_not_save_unknown_choice(self):
        self.client.force_login(self.user)
        payload = self._valid_payload()
        payload["theme"] = "NEON"
        response = self.client.post(reverse("organizations:account"), payload)
        self.assertEqual(response.status_code, 200)
        preference = InterfacePreference.objects.get(user=self.user)
        self.assertEqual(preference.theme, InterfacePreference.Theme.DARK)

    def test_base_template_receives_saved_data_attributes(self):
        InterfacePreference.objects.create(
            user=self.user,
            theme=InterfacePreference.Theme.LIGHT,
            density=InterfacePreference.Density.COMPACT,
            font_scale=InterfacePreference.FontScale.LARGE,
            content_width=InterfacePreference.ContentWidth.WIDE,
            show_technical_details=True,
            journal_heading_mode=InterfacePreference.JournalHeadingMode.FULL,
            journal_font_family=InterfacePreference.JournalFontFamily.TIMES,
            journal_font_size=InterfacePreference.JournalFontSize.EXTRA_LARGE,
            journal_time_font_size=InterfacePreference.JournalFontSize.LARGE,
            journal_date_font_size=InterfacePreference.JournalFontSize.SMALL,
            journal_table_header_font_size=InterfacePreference.JournalFontSize.LARGE,
            journal_title_font_size=InterfacePreference.JournalFontSize.EXTRA_LARGE,
            journal_density=InterfacePreference.JournalDensity.RELAXED,
            journal_width=InterfacePreference.JournalWidth.FULL,
            journal_show_authors=False,
            journal_show_links=False,
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("system:home"))
        self.assertContains(response, 'data-theme="light"')
        self.assertContains(response, 'data-density="compact"')
        self.assertContains(response, 'data-technical="true"')
        self.assertContains(response, 'data-journal-heading="full"')
        self.assertContains(response, 'data-journal-font="times"')
        self.assertContains(response, 'data-journal-size="extra_large"')
        self.assertContains(response, 'data-journal-time-size="large"')
        self.assertContains(response, 'data-journal-date-size="small"')
        self.assertContains(
            response,
            'data-journal-table-header-size="large"',
        )
        self.assertContains(
            response,
            'data-journal-title-size="extra_large"',
        )
        self.assertContains(response, 'data-journal-density="relaxed"')
        self.assertContains(response, 'data-journal-width="full"')

    def test_context_processor_creates_default_for_authenticated_user(self):
        request = RequestFactory().get("/")
        request.user = self.user
        result = interface_preferences(request)
        self.assertEqual(result["ui_preferences"].user, self.user)
        self.assertTrue(InterfacePreference.objects.filter(user=self.user).exists())


class PresentationUxTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_dispatching", verbosity=0)
        cls.employee = Employee.objects.select_related("user").get(
            user__username="operator.demo"
        )
        cls.user = cls.employee.user

    def setUp(self):
        self.client.force_login(self.user)

    def test_home_has_presentation_launcher_without_stage_labels(self):
        response = self.client.get(reverse("system:home"))
        self.assertContains(response, "Рабочее пространство")
        self.assertContains(response, "module-launcher")
        self.assertNotContains(response, "STAGE 2")
        self.assertNotContains(response, "PATCH 007")

    def test_navigation_uses_icon_sprite_and_compact_menus(self):
        response = self.client.get(reverse("system:home"))
        self.assertContains(response, "icons.svg#icon-home")
        self.assertContains(response, "Справочники")
        self.assertContains(response, "user-menu")

    def test_dispatching_registry_uses_semantic_cards(self):
        response = self.client.get(reverse("dispatching:registry"))
        self.assertContains(response, "dispatching-object-card")
        self.assertContains(response, "Управление")
        self.assertContains(response, "Ведение")
        self.assertContains(response, "Диспетчерское управление")
        self.assertContains(response, "Технологическое ведение")
        self.assertNotContains(response, ">Управляет<")
        self.assertNotContains(response, ">Ведёт режим<")
        self.assertNotContains(response, "ДОВЕРЕННОЕ СИСТЕМНОЕ ЯДРО")

    def test_dispatching_detail_collapses_history_and_digest(self):
        response = self.client.get(reverse("dispatching:registry"))
        detail_url = response.context["rows"][0]["equipment"].public_id
        detail = self.client.get(
            reverse("dispatching:equipment_detail", args=[detail_url])
        )
        self.assertContains(detail, "history-disclosure")
        self.assertContains(detail, "record-details")
        self.assertContains(detail, "technical-only")

    def test_presentation_seed_uses_recognizable_safe_names(self):
        organization = Organization.objects.get(code="DEMO")
        self.assertEqual(
            organization.short_name,
            "АО «Росатом Возобновляемая энергия»",
        )
        self.assertEqual(self.employee.last_name, "Кузнецов")
        self.assertNotIn("Операторов", self.employee.full_name)

    def test_presentation_seed_is_idempotent(self):
        before = Organization.objects.count(), Employee.objects.count()
        call_command("seed_demo_dispatching", verbosity=0)
        after = Organization.objects.count(), Employee.objects.count()
        self.assertEqual(before, after)

    def test_presentation_labels_preserve_published_dispatching_records(self):
        level = DispatchLevel.objects.get(code="station-operational")
        subject = DispatchSubject.objects.get(code="demo-station-shift")
        self.assertEqual(
            level.name,
            "Оперативно-технологический уровень ЦОТУиЭ ВЭС Невинномысск",
        )
        self.assertEqual(
            level.presentation_label,
            "Оперативно-технологический уровень ЦОТУиЭ ВЭС Невинномысск",
        )
        self.assertEqual(
            subject.short_name,
            "Оперативный персонал ЦОТУиЭ ВЭС Невинномысск",
        )
        self.assertEqual(
            subject.presentation_label,
            "Оперативный персонал ЦОТУиЭ ВЭС Невинномысск",
        )
        response = self.client.get(reverse("dispatching:registry"))
        self.assertContains(
            response,
            "Оперативный персонал ЦОТУиЭ ВЭС Невинномысск",
        )
        self.assertNotContains(response, ">Смена Демо-ВЭС<")

    def test_icon_sprite_contains_required_symbols(self):
        from django.conf import settings

        sprite = (settings.BASE_DIR / "src/static/system/icons.svg").read_text(
            encoding="utf-8"
        )
        for symbol in (
            "icon-management",
            "icon-supervision",
            "icon-settings",
            "icon-menu",
        ):
            self.assertIn(f'id="{symbol}"', sprite)
