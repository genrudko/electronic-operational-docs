from django.test import TestCase, override_settings
from django.urls import reverse


class HealthEndpointTests(TestCase):
    @override_settings(EOD_DEPLOYMENT_MODE="production")
    def test_health_endpoint_confirms_database_access(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})
