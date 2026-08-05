from __future__ import annotations

import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

from scripts.secret_hygiene import (
    AllowEntry,
    apply_allowlist,
    load_allowlist,
    redact_text,
    scan_text,
    validate_demo_bootstrap_sources,
)

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(
    (ROOT / "tests/security/fixtures/secret_hygiene_cases.json").read_text(
        encoding="utf-8"
    )
)


class SecretHygieneTests(unittest.TestCase):
    def test_scanner_fixtures(self) -> None:
        for case in CASES["cases"]:
            with self.subTest(case=case["id"]):
                text = "".join(case["fragments"])
                findings = scan_text(case["path"], text)
                rules = {item.rule for item in findings}
                if case["expected_rule"] is None:
                    self.assertEqual(findings, [])
                else:
                    self.assertIn(case["expected_rule"], rules)
                    for finding in findings:
                        self.assertNotIn("Fixture", finding.diagnostic())

    def test_diagnostic_does_not_reveal_full_secret(self) -> None:
        secret = "FixtureDiagnosticCredential!2026"
        finding = scan_text("x.env", f"ADMIN_PASSWORD={secret}")[0]
        self.assertNotIn(secret, finding.diagnostic())
        self.assertRegex(finding.identifier, r"^finding-[0-9a-f]{16}$")

    def test_missing_mandatory_injection(self) -> None:
        errors = validate_demo_bootstrap_sources(
            {
                "policy": "def set_password(): pass",
                "command": "class CommandError(Exception): pass",
                "signals": "post_migrate = object()",
            }
        )
        self.assertTrue(
            any("rule=missing-mandatory-injection" in error for error in errors)
        )

    def test_overly_broad_allowlist(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "allowlist.json"
            path.write_text(
                json.dumps(
                    {
                        "schema": 1,
                        "entries": [
                            {
                                "path": "docs/**",
                                "rule": "*",
                                "identifier": "finding-0000000000000000",
                                "rationale": "Fixture rationale only",
                                "owner": "SECURITY_OWNER",
                                "expires": "2099-01-01",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            _, errors = load_allowlist(path, today=dt.date(2026, 8, 5))
            self.assertTrue(
                any("rule=overly-broad-allowlist" in error for error in errors)
            )

    def test_exact_allowlist_cannot_hide_changed_value(self) -> None:
        first = scan_text("a.env", "ADMIN_PASSWORD=FirstFixtureCredential!")[0]
        second = scan_text("a.env", "ADMIN_PASSWORD=SecondFixtureCredential!")[0]
        entry = AllowEntry(
            path=first.path,
            rule=first.rule,
            identifier=first.identifier,
            rationale="Named fixture exception",
            owner="SECURITY_OWNER",
            expires="2099-01-01",
        )
        remaining, errors = apply_allowlist(
            [second], [entry], Path("allowlist.json")
        )
        self.assertEqual(remaining, [second])
        self.assertTrue(
            any("rule=stale-allowlist-entry" in error for error in errors)
        )

    def test_redaction_removes_all_values(self) -> None:
        first = "FixtureRedactionOne!"
        second = "FixtureRedactionTwo!"
        text = (
            f"ADMIN_PASSWORD={first}\n"
            f"API_TOKEN={second}\n"
            f"postgresql://user:{first}@db/eod\n"
        )
        redacted = redact_text(text, [first, second])
        self.assertNotIn(first, redacted)
        self.assertNotIn(second, redacted)
        self.assertGreaterEqual(redacted.count("[REDACTED]"), 3)


if __name__ == "__main__":
    unittest.main()
