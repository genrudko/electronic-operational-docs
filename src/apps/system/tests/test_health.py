from django.test import TestCase
from django.urls import reverse


class HealthEndpointTests(TestCase):
    def test_health_endpoint_confirms_database_access(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
