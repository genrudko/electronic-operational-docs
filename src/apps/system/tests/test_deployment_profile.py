from __future__ import annotations

import secrets
import unittest
from pathlib import Path

from eod_config.deployment import (
    DeploymentConfigurationError,
    validate_deployment_environment,
)

ROOT = Path(__file__).resolve().parents[4]


def safe_production_environment() -> dict[str, str]:
    return {
        "EOD_DEPLOYMENT_MODE": "production",
        "DJANGO_DEBUG": "0",
        "DJANGO_SECRET_KEY": secrets.token_urlsafe(48),
        "DJANGO_ALLOWED_HOSTS": "eod-pilot.example.invalid",
        "DJANGO_CSRF_TRUSTED_ORIGINS": "https://eod-pilot.example.invalid",
        "DJANGO_SECURE_HSTS_SECONDS": "3600",
        "EOD_TLS_TERMINATION": "reverse-proxy",
        "EOD_TRUST_PROXY_HEADERS": "1",
        "EOD_TRUST_X_FORWARDED_HOST": "0",
        "DB_ENGINE": "postgresql",
        "POSTGRES_DB": "eod_ci",
        "POSTGRES_USER": "eod_ci",
        "POSTGRES_PASSWORD": secrets.token_urlsafe(32),
        "POSTGRES_HOST": "127.0.0.1",
        "POSTGRES_PORT": "5432",
        "EOD_DATABASE_PROFILE": "production",
        "EOD_ALLOW_SQLITE_PATH_OVERRIDE": "0",
        "EOD_TESTING": "0",
        "TIME_ZONE": "Europe/Moscow",
    }


class DeploymentEnvironmentContractTests(unittest.TestCase):
    def assert_rejected(self, updates: dict[str, str], marker: str) -> None:
        env = safe_production_environment()
        env.update(updates)
        with self.assertRaisesRegex(DeploymentConfigurationError, marker):
            validate_deployment_environment(env)

    def test_safe_production_profile_is_accepted(self) -> None:
        contract = validate_deployment_environment(safe_production_environment())
        self.assertTrue(contract.production_capable)
        self.assertEqual(contract.mode, "production")
        self.assertEqual(contract.hsts_seconds, 3600)

    def test_preview_is_explicitly_nonproduction(self) -> None:
        contract = validate_deployment_environment({"EOD_DEPLOYMENT_MODE": "preview"})
        self.assertFalse(contract.production_capable)
        self.assertEqual(contract.mode, "preview")

    def test_debug_zero_does_not_make_development_production_capable(self) -> None:
        contract = validate_deployment_environment(
            {"EOD_DEPLOYMENT_MODE": "development", "DJANGO_DEBUG": "0"}
        )
        self.assertFalse(contract.production_capable)

    def test_unknown_mode_is_rejected(self) -> None:
        with self.assertRaisesRegex(DeploymentConfigurationError, "EOD_DEPLOYMENT_MODE"):
            validate_deployment_environment({"EOD_DEPLOYMENT_MODE": "unknown"})

    def test_debug_true_is_rejected(self) -> None:
        self.assert_rejected({"DJANGO_DEBUG": "1"}, "DJANGO_DEBUG")

    def test_testing_mode_is_rejected(self) -> None:
        self.assert_rejected({"EOD_TESTING": "1"}, "EOD_TESTING")

    def test_missing_secret_is_rejected(self) -> None:
        env = safe_production_environment()
        del env["DJANGO_SECRET_KEY"]
        with self.assertRaisesRegex(DeploymentConfigurationError, "DJANGO_SECRET_KEY"):
            validate_deployment_environment(env)

    def test_short_secret_is_rejected_without_echoing_value(self) -> None:
        env = safe_production_environment()
        value = "short-value"
        env["DJANGO_SECRET_KEY"] = value
        with self.assertRaises(DeploymentConfigurationError) as context:
            validate_deployment_environment(env)
        self.assertNotIn(value, str(context.exception))

    def test_wildcard_host_is_rejected(self) -> None:
        self.assert_rejected({"DJANGO_ALLOWED_HOSTS": "*"}, "wildcard")

    def test_subdomain_wildcard_host_is_rejected(self) -> None:
        self.assert_rejected({"DJANGO_ALLOWED_HOSTS": ".example.invalid"}, "wildcard")

    def test_http_csrf_origin_is_rejected(self) -> None:
        self.assert_rejected(
            {"DJANGO_CSRF_TRUSTED_ORIGINS": "http://eod-pilot.example.invalid"},
            "HTTPS origins",
        )

    def test_credentialed_csrf_origin_is_rejected(self) -> None:
        self.assert_rejected(
            {"DJANGO_CSRF_TRUSTED_ORIGINS": "https://user@eod-pilot.example.invalid"},
            "HTTPS origins",
        )

    def test_sqlite_fallback_is_rejected(self) -> None:
        self.assert_rejected({"DB_ENGINE": "sqlite"}, "SQLite fallback")

    def test_missing_postgres_password_is_rejected(self) -> None:
        self.assert_rejected({"POSTGRES_PASSWORD": ""}, "POSTGRES_PASSWORD")

    def test_missing_reverse_proxy_contract_is_rejected(self) -> None:
        self.assert_rejected({"EOD_TLS_TERMINATION": ""}, "EOD_TLS_TERMINATION")

    def test_invalid_tls_termination_mode_is_rejected(self) -> None:
        self.assert_rejected({"EOD_TLS_TERMINATION": "direct"}, "EOD_TLS_TERMINATION")

    def test_missing_proxy_header_trust_is_rejected(self) -> None:
        self.assert_rejected({"EOD_TRUST_PROXY_HEADERS": "0"}, "EOD_TRUST_PROXY_HEADERS")

    def test_forwarded_host_trust_is_rejected(self) -> None:
        self.assert_rejected({"EOD_TRUST_X_FORWARDED_HOST": "1"}, "canonical Host")

    def test_weak_hsts_contract_is_rejected(self) -> None:
        self.assert_rejected({"DJANGO_SECURE_HSTS_SECONDS": "0"}, "HSTS")


class ProductionComposeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.compose = (ROOT / "compose.production.yaml").read_text(encoding="utf-8")

    def test_production_mode_cannot_be_replaced_by_environment(self) -> None:
        self.assertIn("EOD_DEPLOYMENT_MODE: production", self.compose)
        self.assertNotIn("EOD_DEPLOYMENT_MODE: ${", self.compose)
        self.assertIn('EOD_TESTING: "0"', self.compose)

    def test_database_has_no_host_port(self) -> None:
        db_section, app_section = self.compose.split("  app:", 1)
        self.assertNotIn("ports:", db_section)
        self.assertIn("127.0.0.1:${EOD_PRODUCTION_PORT:-8767}:8765", app_section)

    def test_compose_requires_credentials_hosts_and_origins(self) -> None:
        for marker in (
            "DJANGO_SECRET_KEY:?",
            "DJANGO_ALLOWED_HOSTS:?",
            "DJANGO_CSRF_TRUSTED_ORIGINS:?",
            "POSTGRES_PASSWORD:?",
        ):
            self.assertIn(marker, self.compose)

    def test_internal_liveness_probe_marks_trusted_proxy_protocol(self) -> None:
        self.assertIn("X-Forwarded-Proto':'https", self.compose)
        self.assertIn("DJANGO_ALLOWED_HOSTS", self.compose)


if __name__ == "__main__":
    unittest.main()
