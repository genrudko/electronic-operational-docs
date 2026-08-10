from __future__ import annotations

from unittest.mock import patch

from django.test import SimpleTestCase


class DeploymentHealthContractTests(SimpleTestCase):
    def test_liveness_is_process_only(self) -> None:
        with patch(
            "eod_config.health.connection.cursor",
            side_effect=AssertionError("liveness must not access database"),
        ):
            response = self.client.get("/_health/live/")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "alive"})

    def test_readiness_passes_when_mandatory_dependencies_are_ready(self) -> None:
        with patch("eod_config.health._deployment_dependencies_ready", return_value=True):
            response = self.client.get("/_health/ready/")
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"status": "ready"})

    def test_readiness_fails_closed_without_backend_details(self) -> None:
        diagnostic_marker = "backend-diagnostic-marker"
        with patch(
            "eod_config.health._deployment_dependencies_ready",
            side_effect=RuntimeError(diagnostic_marker),
        ):
            response = self.client.get("/_health/ready/")
        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(response.content, {"status": "unavailable"})
        self.assertNotIn(diagnostic_marker.encode(), response.content)

    def test_legacy_health_endpoint_remains_readiness_alias(self) -> None:
        with patch("eod_config.health._deployment_dependencies_ready", return_value=False):
            response = self.client.get("/_health/")
        self.assertEqual(response.status_code, 503)
        self.assertJSONEqual(response.content, {"status": "unavailable"})
