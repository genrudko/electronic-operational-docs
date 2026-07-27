from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

from django.test import SimpleTestCase

ROOT = Path(__file__).resolve().parents[4]
PUBLIC_IP = "5.181.177.72"
PUBLIC_ORIGIN = f"https://{PUBLIC_IP}"

SETTINGS_PROBE = """
import json
from eod_config import settings

payload = {
    "debug": settings.DEBUG,
    "allowed_hosts": settings.ALLOWED_HOSTS,
    "csrf_trusted_origins": settings.CSRF_TRUSTED_ORIGINS,
    "public_https": settings.EOD_PUBLIC_HTTPS,
    "public_origin": settings.EOD_PUBLIC_HTTPS_ORIGIN,
    "proxy_header": getattr(settings, "SECURE_PROXY_SSL_HEADER", None),
    "session_cookie_secure": settings.SESSION_COOKIE_SECURE,
    "csrf_cookie_secure": settings.CSRF_COOKIE_SECURE,
}
print(json.dumps(payload, ensure_ascii=False))
"""

PUBLIC_ENV = {
    "EOD_DEPLOYMENT_MODE": "development",
    "DJANGO_SECRET_KEY": "access001-test-secret-not-for-deployment",
    "DJANGO_DEBUG": "0",
    "DJANGO_ALLOWED_HOSTS": f"127.0.0.1,localhost,{PUBLIC_IP}",
    "DJANGO_CSRF_TRUSTED_ORIGINS": PUBLIC_ORIGIN,
    "DJANGO_TRUST_PROXY_HTTPS": "1",
    "DJANGO_SECURE_COOKIES": "1",
    "EOD_PUBLIC_HTTPS": "1",
    "EOD_PUBLIC_HTTPS_ORIGIN": PUBLIC_ORIGIN,
    "DB_ENGINE": "postgresql",
    "POSTGRES_DB": "eod_access001_test",
    "POSTGRES_USER": "eod_access001_test",
    "POSTGRES_PASSWORD": "not-used-by-settings-probe",
    "POSTGRES_HOST": "127.0.0.1",
    "POSTGRES_PORT": "5432",
    "EOD_DATABASE_PROFILE": "development",
    "EOD_ALLOW_SQLITE_PATH_OVERRIDE": "0",
}

CONTROLLED_KEYS = {
    *PUBLIC_ENV,
    "EOD_TESTING",
}


class Access001PublicHttpsSettingsTests(SimpleTestCase):
    def run_settings_probe(
        self,
        overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        for key in CONTROLLED_KEYS:
            env.pop(key, None)
        env.update(PUBLIC_ENV)
        if overrides:
            env.update(overrides)
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = os.pathsep.join(
            value for value in (str(ROOT / "src"), existing_pythonpath) if value
        )
        return subprocess.run(
            [sys.executable, "-c", SETTINGS_PROBE],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_public_https_settings_are_fail_closed_and_complete(self):
        result = self.run_settings_probe()

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertFalse(payload["debug"])
        self.assertTrue(payload["public_https"])
        self.assertEqual(payload["public_origin"], PUBLIC_ORIGIN)
        self.assertIn(PUBLIC_IP, payload["allowed_hosts"])
        self.assertIn(PUBLIC_ORIGIN, payload["csrf_trusted_origins"])
        self.assertEqual(payload["proxy_header"], ["HTTP_X_FORWARDED_PROTO", "https"])
        self.assertTrue(payload["session_cookie_secure"])
        self.assertTrue(payload["csrf_cookie_secure"])

    def test_public_https_rejects_debug_mode(self):
        result = self.run_settings_probe({"DJANGO_DEBUG": "1"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_DEBUG должен быть отключён", result.stderr)
        self.assertIn("Небезопасная конфигурация публичного development", result.stderr)

    def test_public_https_rejects_missing_proxy_trust(self):
        result = self.run_settings_probe({"DJANGO_TRUST_PROXY_HTTPS": "0"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_TRUST_PROXY_HTTPS должен быть включён", result.stderr)

    def test_public_https_rejects_untrusted_origin(self):
        result = self.run_settings_probe({"DJANGO_CSRF_TRUSTED_ORIGINS": ""})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("публичный HTTPS origin отсутствует в CSRF trusted origins", result.stderr)

    def test_public_https_rejects_insecure_cookies(self):
        result = self.run_settings_probe({"DJANGO_SECURE_COOKIES": "0"})

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("secure session и CSRF cookies должны быть включены", result.stderr)


@unittest.skipUnless(
    (ROOT / "deploy" / "access").is_dir(),
    "repository infrastructure files are not copied into the application image",
)
class Access001InfrastructureContractTests(SimpleTestCase):
    def read(self, relative: str) -> str:
        path = ROOT / relative
        self.assertTrue(path.is_file(), f"missing ACCESS-001 file: {relative}")
        return path.read_text(encoding="utf-8")

    def test_host_compose_keeps_private_ports_and_enables_public_https_settings(self):
        compose = self.read("deploy/automation/compose.development.yaml")

        self.assertIn('DJANGO_DEBUG: "0"', compose)
        self.assertIn("DJANGO_CSRF_TRUSTED_ORIGINS", compose)
        self.assertIn("DJANGO_TRUST_PROXY_HTTPS", compose)
        self.assertIn("DJANGO_SECURE_COOKIES", compose)
        self.assertIn("EOD_PUBLIC_HTTPS", compose)
        self.assertIn("127.0.0.1:${EOD_DEVELOPMENT_PORT:-8766}:8766", compose)
        self.assertNotIn("0.0.0.0:${EOD_DEVELOPMENT_PORT", compose)
        db_section = compose.split("  app:", 1)[0]
        self.assertNotIn("    ports:", db_section)

    def test_nginx_proxy_closes_external_health_and_preserves_acme(self):
        http_config = self.read("deploy/access/nginx/eod-development-http.conf")
        tls_config = self.read("deploy/access/nginx/eod-development.conf")

        self.assertIn("/.well-known/acme-challenge/", http_config)
        self.assertIn("return 308 https://5.181.177.72$request_uri", http_config)
        self.assertIn("proxy_pass http://127.0.0.1:8766", tls_config)
        self.assertIn("proxy_set_header X-Forwarded-Proto https", tls_config)
        self.assertIn("location ^~ /_health", tls_config)
        self.assertIn("return 404", tls_config)
        self.assertIn("limit_req zone=eod_access001_login", tls_config)
        self.assertIn("proxy_cookie_flags ~ secure httponly samesite=lax", tls_config)
        health_block = tls_config.split("location ^~ /_health", 1)[1].split("}", 1)[0]
        self.assertNotIn("proxy_pass", health_block)

    def test_bootstrap_is_syntactically_valid_and_preserves_host_boundaries(self):
        relative = "deploy/access/bootstrap_access001.sh"
        bootstrap_path = ROOT / relative
        bootstrap = self.read(relative)
        result = subprocess.run(
            ["bash", "-n", str(bootstrap_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("HOST INVENTORY — NO MUTATIONS YET", bootstrap)
        self.assertIn("sshd -T", bootstrap)
        self.assertIn("ACCESS001_CI_CONFIRMED", bootstrap)
        self.assertIn("ACCESS001_SCRIPT_SHA256", bootstrap)
        self.assertIn("--preferred-profile shortlived", bootstrap)
        self.assertIn("--ip-address", bootstrap)
        self.assertIn("Certbot $version is too old", bootstrap)
        self.assertIn("capture_preview_state", bootstrap)
        self.assertIn('controller_command "deploy refresh', bootstrap)
        self.assertIn('controller_command "confirm', bootstrap)
        self.assertIn("find_active_certbot_timer", bootstrap)
        self.assertIn("HTTPS_CSRF_POST=PASSED", bootstrap)
        self.assertLess(
            bootstrap.rfind('INVENTORY_SNAPSHOT="$(print_inventory)"'),
            bootstrap.rfind("    deploy_exact_head"),
        )
        self.assertNotIn("22/tcp", bootstrap)
        self.assertNotIn("ufw reset", bootstrap.lower())
        self.assertNotIn("ufw default", bootstrap.lower())
        self.assertNotIn("base64", bootstrap.lower())
        self.assertNotIn(".part", bootstrap.lower())

        digest = hashlib.sha256(bootstrap_path.read_bytes()).hexdigest()
        self.assertRegex(digest, r"^[0-9a-f]{64}$")
        print(f"ACCESS001_BOOTSTRAP_SHA256={digest}")

    def test_fresh_nginx_install_loads_virtual_host_before_acme_probe(self):
        bootstrap = self.read("deploy/access/bootstrap_access001.sh")
        nginx_block = bootstrap.split("ensure_nginx() {", 1)[1].split(
            "\n}\n\nufw_rule_exists() {", 1
        )[0]

        config_test = nginx_block.index("    nginx -t")
        enable = nginx_block.index("    systemctl enable nginx", config_test)
        active_branch = nginx_block.index(
            "    if systemctl is-active --quiet nginx; then", enable
        )
        reload = nginx_block.index("        systemctl reload nginx", active_branch)
        start = nginx_block.index("        systemctl start nginx", reload)
        host_header = nginx_block.index('--header "Host: $EXPECTED_IP"', start)
        loopback_probe = nginx_block.index(
            '"http://127.0.0.1/.well-known/acme-challenge/$token"', host_header
        )

        self.assertLess(config_test, enable)
        self.assertLess(enable, active_branch)
        self.assertLess(active_branch, reload)
        self.assertLess(reload, start)
        self.assertLess(start, host_header)
        self.assertLess(host_header, loopback_probe)
        self.assertIn("for attempt in $(seq 1 10); do", nginx_block)
        self.assertIn(
            'rm -f "$ACME_ROOT/.well-known/acme-challenge/$token"', nginx_block
        )
        self.assertNotIn("systemctl enable --now nginx", nginx_block)
        self.assertNotIn('--resolve "$EXPECTED_IP:80:127.0.0.1"', nginx_block)

    def test_runbook_documents_manual_gate_and_https_only_user_session(self):
        runbook = self.read("docs/runbooks/PUBLIC_DEVELOPMENT_ACCESS.md")

        self.assertIn("all five workflows are green", runbook)
        self.assertIn("only through HTTPS", runbook)
        self.assertIn("factual SSH port", runbook)
        self.assertIn("/_health/", runbook)
        self.assertIn("preview", runbook.lower())
        self.assertIn("PR #16", runbook)
