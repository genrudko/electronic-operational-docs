from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
from collections.abc import Iterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FULL_TEST_COMMAND = (sys.executable, "manage.py", "test", "apps", "--verbosity", "2")
DEFAULT_REPO_ROOT = Path(os.environ.get("PLAN_001_REPO_ROOT", "/repo"))
DEFAULT_APP_ROOT = Path(os.environ.get("PLAN_001_APP_ROOT", "/app"))
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "backups",
    "data",
    "logs",
    "media",
    "node_modules",
    "staticfiles",
}
TEXT_SUFFIXES = {
    ".css",
    ".html",
    ".js",
    ".json",
    ".md",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
SECRET_KEY_RE = re.compile(
    r"(?i)(password|secret|token|private[_-]?key|api[_-]?key|credential)"
)
SECRET_ASSIGNMENT_RE = re.compile(
    r"(?i)\b([A-Z0-9_]*(?:PASSWORD|SECRET|TOKEN|PRIVATE_KEY|API_KEY|CREDENTIAL)[A-Z0-9_]*)"
    r"\s*[:=]\s*([^\s,;]+)"
)
URI_CREDENTIAL_RE = re.compile(
    r"(?i)([a-z][a-z0-9+.-]*://[^\s:/@]+:)([^\s@]+)(@)"
)
PEM_RE = re.compile(
    r"-----BEGIN [^-]+-----.*?-----END [^-]+-----",
    re.DOTALL,
)
RAN_TESTS_RE = re.compile(r"Ran\s+(\d+)\s+tests?", re.IGNORECASE)


def now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def digest(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def validate_sha(value: str, label: str) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", value):
        raise argparse.ArgumentTypeError(f"{label} must be a lowercase 40-hex SHA")
    return value


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def relative(path: Path, root: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (OSError, ValueError):
        return path.as_posix()


def repo_files(root: Path, suffixes: set[str] | None = None) -> Iterator[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in parts):
            continue
        if suffixes is not None and path.suffix.lower() not in suffixes:
            continue
        yield path


def secret_values() -> tuple[str, ...]:
    names = (
        "DJANGO_SECRET_KEY",
        "POSTGRES_PASSWORD",
        "DATABASE_URL",
        "EOD_VPS_SSH_PRIVATE_KEY",
        "GITHUB_TOKEN",
        "TELEGRAM_BOT_TOKEN",
    )
    values = {os.environ.get(name, "") for name in names}
    return tuple(
        sorted((item for item in values if len(item) >= 6), key=len, reverse=True)
    )


def sanitize_text(value: str, secrets: Sequence[str] = ()) -> str:
    value = PEM_RE.sub("<redacted-pem>", value)
    value = URI_CREDENTIAL_RE.sub(r"\1<redacted>\3", value)
    value = SECRET_ASSIGNMENT_RE.sub(r"\1=<redacted>", value)
    for secret in secrets:
        value = value.replace(secret, "<redacted-secret>")
    return value


def sanitize(value: Any, secrets: Sequence[str]) -> Any:
    if isinstance(value, str):
        return sanitize_text(value, secrets)
    if isinstance(value, Mapping):
        return {
            str(key): (
                "<redacted>"
                if SECRET_KEY_RE.search(str(key))
                else sanitize(item, secrets)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [sanitize(item, secrets) for item in value]
    return value


def executed_tests(output: str) -> int | None:
    matches = RAN_TESTS_RE.findall(output)
    return int(matches[-1]) if matches else None


def run_command(
    args: Sequence[str],
    *,
    cwd: Path,
    secrets: Sequence[str],
    timeout: int = 3600,
) -> dict[str, Any]:
    started = now()
    try:
        result = subprocess.run(
            list(args),
            cwd=cwd,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
        output = sanitize_text(result.stdout or "", secrets)
        return {
            "command": list(args),
            "started_at": started,
            "finished_at": now(),
            "returncode": result.returncode,
            "timed_out": False,
            "executed_test_count": executed_tests(output),
            "output": output,
        }
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else exc.stdout or ""
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else exc.stderr or ""
        output = sanitize_text(stdout + stderr, secrets)
        return {
            "command": list(args),
            "started_at": started,
            "finished_at": now(),
            "returncode": None,
            "timed_out": True,
            "executed_test_count": executed_tests(output),
            "output": output,
        }
