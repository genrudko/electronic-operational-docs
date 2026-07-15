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

    def test_preference_is_one_to_one_with_user(self):
        user = get_user_model().objects.create_user(username="ui-unique")
        InterfacePreference.objects.create(user=user)
        with self.assertRaises(ValidationError):
            InterfacePreference.objects.create(user=user)


class InterfacePreferenceViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.employee, cls.user = employee_with_user(username="ui-user")

    def test_account_page_contains_interface_form(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("organizations:account"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Настройки интерфейса")
        self.assertContains(response, "Показывать технические реквизиты")

    def test_post_saves_personal_preferences(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("organizations:account"),
            {
                "theme": InterfacePreference.Theme.LIGHT,
                "density": InterfacePreference.Density.COMPACT,
                "font_scale": InterfacePreference.FontScale.LARGE,
                "content_width": InterfacePreference.ContentWidth.WIDE,
                "show_technical_details": "on",
            },
        )
        self.assertRedirects(response, reverse("organizations:account"))
        preference = InterfacePreference.objects.get(user=self.user)
        self.assertEqual(preference.theme, InterfacePreference.Theme.LIGHT)
        self.assertEqual(preference.density, InterfacePreference.Density.COMPACT)
        self.assertEqual(preference.font_scale, InterfacePreference.FontScale.LARGE)
        self.assertTrue(preference.show_technical_details)

    def test_invalid_post_does_not_save_unknown_choice(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("organizations:account"),
            {
                "theme": "NEON",
                "density": InterfacePreference.Density.COMFORTABLE,
                "font_scale": InterfacePreference.FontScale.NORMAL,
                "content_width": InterfacePreference.ContentWidth.STANDARD,
            },
        )
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
        )
        self.client.force_login(self.user)
        response = self.client.get(reverse("system:home"))
        self.assertContains(response, 'data-theme="light"')
        self.assertContains(response, 'data-density="compact"')
        self.assertContains(response, 'data-technical="true"')

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
        cls.employee = Employee.objects.select_related("user").get(user__username="operator.demo")
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
        self.assertContains(response, "Управляет")
        self.assertContains(response, "Ведёт режим")
        self.assertNotContains(response, "ДОВЕРЕННОЕ СИСТЕМНОЕ ЯДРО")

    def test_dispatching_detail_collapses_history_and_digest(self):
        response = self.client.get(reverse("dispatching:registry"))
        detail_url = response.context["rows"][0]["equipment"].public_id
        detail = self.client.get(reverse("dispatching:equipment_detail", args=[detail_url]))
        self.assertContains(detail, "history-disclosure")
        self.assertContains(detail, "record-details")
        self.assertContains(detail, "technical-only")

    def test_presentation_seed_uses_recognizable_safe_names(self):
        organization = Organization.objects.get(code="DEMO")
        self.assertIn("Кочубеевская ВЭС", organization.name)
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
        self.assertEqual(level.name, "Оперативно-технологический уровень Демо-ВЭС")
        self.assertEqual(
            level.presentation_label,
            "Оперативно-технологический уровень Кочубеевской ВЭС",
        )
        self.assertEqual(subject.short_name, "Смена Демо-ВЭС")
        self.assertEqual(subject.presentation_label, "Смена Кочубеевской ВЭС")

        response = self.client.get(reverse("dispatching:registry"))
        self.assertContains(response, "Смена Кочубеевской ВЭС")
        self.assertNotContains(response, ">Смена Демо-ВЭС<")

    def test_icon_sprite_contains_required_symbols(self):
        from django.conf import settings

        sprite = (settings.BASE_DIR / "src/static/system/icons.svg").read_text(encoding="utf-8")
        for symbol in ("icon-management", "icon-supervision", "icon-settings", "icon-menu"):
            self.assertIn(f'id="{symbol}"', sprite)
