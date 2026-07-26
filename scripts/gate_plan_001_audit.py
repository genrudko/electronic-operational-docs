from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

from plan_001_audit.core import FULL_TEST_COMMAND, executed_tests, sanitize_text
from plan_001_audit.package import build_manifest, scan_for_secret_leaks, verify_manifest

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    require(
        FULL_TEST_COMMAND[-3:] == ("apps", "--verbosity", "2"),
        "PLAN-001 must execute the accepted full Django test label apps",
    )
    require(executed_tests("Ran 498 tests in 1.23s") == 498, "test count parsing failed")
    require(executed_tests("no test summary") is None, "missing test count must remain unknown")

    secret = "PLAN001_TEST_SECRET_123456"
    sanitized = sanitize_text(
        f"POSTGRES_PASSWORD={secret}\npostgresql://user:{secret}@db/eod",
        (secret,),
    )
    require(secret not in sanitized, "explicit secret value was not redacted")
    require("<redacted>" in sanitized, "redaction marker is absent")

    runner = (ROOT / "scripts/run_plan_001_audit.sh").read_text(encoding="utf-8")
    for forbidden in (
        "/srv/eod/development",
        "git branch --show-current",
        "docker compose",
        "sudo bash",
    ):
        require(forbidden not in runner, f"obsolete host runner marker remains: {forbidden}")
    for required in (
        "container-only",
        "EUID",
        "/repo/scripts/plan_001_evidence_audit.py",
        "PLAN_001_HEAD_SHA",
    ):
        require(required in runner, f"container runner marker is missing: {required}")

    completed = subprocess.run(
        [sys.executable, "scripts/plan_001_evidence_audit.py", "--help"],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    require(completed.returncode == 0, completed.stderr)
    require("exact-SHA PLAN-001 evidence package" in completed.stdout, "CLI help contract failed")

    with tempfile.TemporaryDirectory() as temp:
        output = Path(temp)
        (output / "REPORT.md").write_text("safe\n", encoding="utf-8")
        data = {"project": {"generated_at": "2026-07-26T00:00:00+00:00", "head_sha": "a" * 40}}
        manifest = build_manifest(output, data)
        verify_manifest(output, manifest)
        scan_for_secret_leaks(output, (secret,))
        (output / "REPORT.md").write_text(secret, encoding="utf-8")
        try:
            scan_for_secret_leaks(output, (secret,))
        except RuntimeError:
            pass
        else:
            raise AssertionError("secret leak gate did not fail")

    print("PLAN_001_AUDIT_TOOLING_GATE=PASSED")


if __name__ == "__main__":
    main()
