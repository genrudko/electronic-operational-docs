from django.test import TestCase
from django.urls import reverse

from .helpers import DispatchingDemoMixin


class DispatchingViewTests(DispatchingDemoMixin, TestCase):
    def test_registry_requires_login(self):
        response = self.client.get(reverse("dispatching:registry"))
        self.assertEqual(response.status_code, 302)

    def test_registry_is_russian_and_contains_assignments(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dispatching:registry"))
        self.assertContains(response, "Управление и ведение")
        self.assertContains(response, "Информационное ведение")
        self.assertContains(response, "Демо-РДЦ")

    def test_equipment_from_other_organization_is_hidden(self):
        # Organization scoping must return 404 for an unknown public identifier.
        self.client.force_login(self.user)
        response = self.client.get(
            reverse(
                "dispatching:equipment_detail",
                kwargs={"public_id": "11111111-1111-1111-1111-111111111111"},
            )
        )
        self.assertEqual(response.status_code, 404)

    def test_subjects_page_shows_explicit_adjacent_interaction(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("dispatching:subjects"))
        self.assertContains(response, "Взаимодействие смежных субъектов")
        self.assertContains(response, "Демо-смежный ДЦ")
        self.assertContains(response, "Правила")
