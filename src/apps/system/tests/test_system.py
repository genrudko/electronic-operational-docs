from django.test import TestCase
from django.urls import reverse


class SystemSmokeTests(TestCase):
    def test_home_page(self):
        response = self.client.get(reverse("system:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Электронная оперативная документация")
        self.assertContains(response, "Базовые реестры готовы к демонстрации")
        self.assertContains(response, "Управление и ведение")
        self.assertNotContains(response, "Локальный профиль разработки")

    def test_health_endpoint(self):
        response = self.client.get(reverse("system:health"))

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["database"])
        self.assertIn(payload["database_vendor"], {"sqlite", "postgresql"})
        self.assertIn(payload["profile"], {"development", "postgresql"})
        self.assertIn("local_server_time", payload)
        self.assertIn("time_zone", payload)
