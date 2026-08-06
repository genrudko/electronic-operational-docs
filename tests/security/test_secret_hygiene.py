from __future__ import annotations

import datetime as dt
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from scripts.secret_hygiene import (
    AllowEntry,
    apply_allowlist,
    clean_tree_residue,
    history_inventory,
    load_allowlist,
    redact_text,
    scan_repository,
    scan_text,
    validate_demo_bootstrap_sources,
    verify_sanitized_text,
)

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads(
    (ROOT / "tests/security/fixtures/secret_hygiene_cases.json").read_text(
        encoding="utf-8"
    )
)


def _credential_value(label: str = "Runtime") -> str:
    return "".join((label, "Credential", "!2026", "-", "LongValue"))


def _sensitive_name(prefix: str = "ADMIN") -> str:
    return "".join((prefix, "_PASS", "WORD"))


def _build_case(builder: str) -> str:
    value = _credential_value("Committed")
    name = _sensitive_name()
    if builder == "runtime-placeholder":
        return "POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?required}"
    if builder == "exact-placeholder":
        return "DJANGO_SECRET_KEY=replace-with-a-long-random-secret"
    if builder == "generated-shell":
        return "POSTGRES_PASSWORD=\"$(python -c 'import secrets; print(secrets.token_urlsafe(32))')\""
    if builder == "error-message":
        return "echo \"Unsafe configuration: POSTGRES_PASSWORD is required.\" >&2"
    if builder == "verified-artifact":
        return "\n".join(
            (
                "steps:",
                "  - name: Sanitize",
                "    run: |",
                "      python scripts/secret_hygiene.py redact --input raw.log --output diagnostics.sanitized.txt",
                "      python scripts/secret_hygiene.py verify-sanitized --input diagnostics.sanitized.txt",
                "      cat diagnostics.sanitized.txt",
                "  - name: Upload",
                "    uses: actions/upload-artifact@v7",
                "    with:",
                "      path: diagnostics.sanitized.txt",
            )
        )
    if builder == "credential-assignment":
        return f"{name}={value}"
    if builder == "workflow-assignment":
        return f"POSTGRES_PASSWORD: {value}"
    if builder == "token":
        return "".join(("gh", "p_", "abcdefghijklmnopqrstuvwxyz123456"))
    if builder == "private-key":
        return "".join(("-----BEGIN OPENSSH PRI", "VATE KEY-----"))
    if builder == "dsn":
        return "".join(("DATABASE_URL=postgresql://user:", value, "@db/eod"))
    if builder == "demo-assignment":
        return f"EOD_DEMO_PASSWORD={value}"
    if builder == "shell-output":
        return "".join(("echo \"$ADMIN_PASS", "WORD\""))
    if builder == "shell-trace":
        return "".join(("set -x\nprintf '%s' \"$API_", "TOKEN\""))
    if builder == "summary-leak":
        return "\n".join(
            (
                "steps:",
                "  - name: Unsafe summary",
                "    run: |",
                "      cat raw-output.log >>\"$GITHUB_STEP_SUMMARY\"",
            )
        )
    if builder == "artifact-leak":
        return "\n".join(
            (
                "steps:",
                "  - name: Unsafe artifact",
                "    uses: actions/upload-artifact@v7",
                "    with:",
                "      path: diagnostic.log",
            )
        )
    if builder == "unverified-redaction":
        return "\n".join(
            (
                "steps:",
                "  - name: Incomplete redaction",
                "    run: |",
                "      python scripts/secret_hygiene.py redact --input raw.log --output result.sanitized.txt",
                "      cat result.sanitized.txt",
            )
        )
    raise AssertionError(f"Unknown builder: {builder}")


def _git(directory: Path, *args: str) -> None:
    subprocess.run(
        ["git", "-C", str(directory), *args],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


class SecretHygieneTests(unittest.TestCase):
    def test_generated_fixture_matrix(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for case in CASES["cases"]:
                with self.subTest(case=case["id"]):
                    path = root / case["path"]
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(_build_case(case["builder"]), encoding="utf-8")
                    findings = scan_text(case["path"], path.read_text(encoding="utf-8"))
                    rules = {item.rule for item in findings}
                    if case["expected_rule"] is None:
                        self.assertEqual(findings, [])
                    else:
                        self.assertIn(case["expected_rule"], rules)

    def test_real_credential_literal_in_test_file_is_blocked(self) -> None:
        value = _credential_value("Production")
        text = f"{_sensitive_name()} = {value!r}"
        findings = scan_text("tests/test_authentication.py", text)
        self.assertIn("explicit-credential-assignment", {item.rule for item in findings})

    def test_test_or_fixture_substring_does_not_make_value_safe(self) -> None:
        for label in ("ContainsTest", "ContainsFixture"):
            with self.subTest(label=label):
                value = _credential_value(label)
                findings = scan_text(
                    "tests/test_authentication.py",
                    f"{_sensitive_name()} = {value!r}",
                )
                self.assertIn(
                    "explicit-credential-assignment",
                    {item.rule for item in findings},
                )

    def test_password_assignment_inside_authentication_tests_is_blocked(self) -> None:
        value = _credential_value("ClassLevel")
        source = "\n".join(
            (
                "class AuthenticationTests:",
                f"    {_sensitive_name('')} = {value!r}",
            )
        )
        findings = scan_text("tests/test_authentication.py", source)
        self.assertIn("explicit-credential-assignment", {item.rule for item in findings})

    def test_new_credential_in_fixture_directory_is_blocked_by_repository_scan(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _git(root, "init")
            _git(root, "config", "user.name", "Secret Hygiene Test")
            _git(root, "config", "user.email", "secret-hygiene@example.invalid")
            fixture = root / "tests/security/fixtures/new_case.json"
            fixture.parent.mkdir(parents=True)
            fixture.write_text(
                json.dumps({_sensitive_name(): _credential_value("FixtureDirectory")}),
                encoding="utf-8",
            )
            allowlist = root / ".github/secret-hygiene-allowlist.json"
            allowlist.parent.mkdir(parents=True)
            allowlist.write_text('{"schema":1,"entries":[]}\n', encoding="utf-8")
            _git(root, "add", ".")
            findings = scan_repository(root)
            self.assertIn("explicit-credential-assignment", {item.rule for item in findings})

    def test_diagnostic_does_not_reveal_full_value(self) -> None:
        value = _credential_value("Diagnostic")
        finding = scan_text("x.env", f"{_sensitive_name()}={value}")[0]
        self.assertNotIn(value, finding.diagnostic())
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
                                "rationale": "Synthetic rationale for regression",
                                "owner": "SECURITY_OWNER",
                                "expires": "2099-01-01",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )
            _, errors = load_allowlist(path, today=dt.date(2026, 8, 6))
            self.assertTrue(
                any("rule=overly-broad-allowlist" in error for error in errors)
            )

    def test_changed_synthetic_fixture_does_not_inherit_exact_allowlist(self) -> None:
        first = scan_text(
            "tests/security/fixtures/case.json",
            f"{_sensitive_name()}={_credential_value('First')}",
        )[0]
        second = scan_text(
            "tests/security/fixtures/case.json",
            f"{_sensitive_name()}={_credential_value('Second')}",
        )[0]
        entry = AllowEntry(
            path=first.path,
            rule=first.rule,
            identifier=first.identifier,
            rationale="Exact synthetic fixture exception",
            owner="SECURITY_OWNER",
            expires="2099-01-01",
        )
        remaining, errors = apply_allowlist([second], [entry], Path("allowlist.json"))
        self.assertEqual(remaining, [second])
        self.assertTrue(
            any("rule=stale-allowlist-entry" in error for error in errors)
        )

    def test_repository_and_history_use_identical_classification(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _git(root, "init")
            _git(root, "config", "user.name", "Secret Hygiene Test")
            _git(root, "config", "user.email", "secret-hygiene@example.invalid")
            (root / "config.env").write_text(
                f"{_sensitive_name()}={_credential_value('History')}\n",
                encoding="utf-8",
            )
            allowlist = root / ".github/secret-hygiene-allowlist.json"
            allowlist.parent.mkdir(parents=True)
            allowlist.write_text('{"schema":1,"entries":[]}\n', encoding="utf-8")
            _git(root, "add", ".")
            _git(root, "commit", "-m", "fixture")
            repository_rules = {item.rule for item in scan_repository(root)}
            report = history_inventory(root, 1)
            history_rules = set(report["counts_by_rule"])
            self.assertEqual(repository_rules, history_rules)

    def test_clean_tree_gate_rejects_untracked_probe(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _git(root, "init")
            _git(root, "config", "user.name", "Secret Hygiene Test")
            _git(root, "config", "user.email", "secret-hygiene@example.invalid")
            (root / "tracked.txt").write_text("tracked\n", encoding="utf-8")
            _git(root, "add", "tracked.txt")
            _git(root, "commit", "-m", "baseline")
            self.assertEqual(clean_tree_residue(root), [])
            (root / "transport-probe.tmp").write_text("probe\n", encoding="utf-8")
            residue = clean_tree_residue(root)
            self.assertEqual([path for _, path in residue], ["transport-probe.tmp"])

    def test_post_redaction_verification_checks_dynamic_values(self) -> None:
        value = _credential_value("Injected")
        raw = f"controller result value={value}\n"
        insufficient = redact_text(raw)
        findings = verify_sanitized_text("controller.sanitized.txt", insufficient, [value])
        self.assertIn("known-injected-secret", {item.rule for item in findings})
        complete = redact_text(raw, [value])
        self.assertEqual(
            verify_sanitized_text("controller.sanitized.txt", complete, [value]),
            [],
        )

    def test_unverified_redaction_cannot_be_published(self) -> None:
        workflow = _build_case("unverified-redaction")
        findings = scan_text(".github/workflows/check.yml", workflow)
        self.assertIn(
            "post-redaction-verification-missing",
            {item.rule for item in findings},
        )


if __name__ == "__main__":
    unittest.main()
