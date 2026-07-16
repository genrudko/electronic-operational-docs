from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from apps.equipment.models import EquipmentAsset
from apps.normatives.models import NormativeDocument
from apps.organizations.models import Employee


class Patch0073PresentationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_dispatching", verbosity=0)
        cls.employee = Employee.objects.select_related("user").get(user__username="operator.demo")
        cls.user = cls.employee.user

    def setUp(self):
        self.client.force_login(self.user)

    def test_registry_uses_noun_headings_and_explicit_contours(self):
        response = self.client.get(reverse("dispatching:registry"))
        self.assertContains(response, ">Управление<")
        self.assertContains(response, ">Ведение<")
        self.assertContains(response, "Диспетчерское управление")
        self.assertContains(response, "Технологическое ведение")
        self.assertNotContains(response, ">Управляет<")
        self.assertNotContains(response, ">Ведёт режим<")

    def test_information_only_is_characteristic_of_supervision(self):
        response = self.client.get(reverse("dispatching:registry"))
        self.assertContains(response, "Информационное ведение")
        self.assertContains(response, "В том числе информационное ведение")

    def test_detail_history_names_assignment_kind(self):
        equipment = EquipmentAsset.objects.filter(management_object__isnull=False).first()
        response = self.client.get(
            reverse("dispatching:equipment_detail", args=[equipment.public_id])
        )
        self.assertContains(response, "Вид управления")
        self.assertContains(response, "Вид ведения")

    def test_light_theme_contract_uses_surface_tokens(self):
        css = (settings.BASE_DIR / "src/static/system/app.css").read_text(encoding="utf-8")
        for marker in (
            "Patch 007.3: theme surface repair",
            "--topbar-bg",
            "background: var(--surface)",
            "color: var(--surface-text)",
        ):
            self.assertIn(marker, css)

    def test_topbar_keeps_readable_contrast_in_both_themes(self):
        css = (settings.BASE_DIR / "src/static/system/app.css").read_text(encoding="utf-8")
        self.assertIn(".presentation-topbar", css)
        self.assertIn("--topbar-text", css)
        self.assertIn("color: var(--topbar-text)", css)

    def test_default_sqlite_profile_is_presentation_database(self):
        source = (settings.BASE_DIR / "src/eod_config/settings.py").read_text(encoding="utf-8")
        self.assertIn('default_name = "presentation.sqlite3"', source)
        self.assertIn('default_name = "gate_runtime.sqlite3"', source)

    def test_document_technical_sections_are_collapsible(self):
        template = (settings.BASE_DIR / "src/templates/documents/detail.html").read_text(
            encoding="utf-8"
        )
        self.assertIn("Технические сведения о проверке", template)
        self.assertIn("История версий", template)
        self.assertIn("Системный аудит", template)
        self.assertIn("technical-disclosure", template)

    def test_equipment_and_normative_pages_hide_patch_labels(self):
        equipment = self.client.get(reverse("equipment:registry"))
        normatives = self.client.get(reverse("normatives:registry"))
        self.assertNotContains(equipment, "PATCH 006")
        self.assertNotContains(normatives, "PATCH 005")

    def test_presentation_normative_uses_public_pte_name(self):
        call_command("seed_demo_normatives", verbosity=0)
        document = NormativeDocument.objects.get(code="demo-electronic-documentation")
        self.assertIn("Правила технической эксплуатации", document.title)
        self.assertIn("Минэнерго России", document.issuer)

    def test_navigation_names_full_module(self):
        response = self.client.get(reverse("system:home"))
        self.assertContains(response, "Управление и ведение")


class Patch0073StaticContractTests(TestCase):
    def test_gate_script_exists(self):
        gate = Path(settings.BASE_DIR / "scripts/gate_patch_007_3.py")
        self.assertTrue(gate.is_file())
        self.assertIn(
            "PATCH_007_3_THEME_TERMINOLOGY_PROFILE_GATE_PASSED",
            gate.read_text(encoding="utf-8"),
        )
