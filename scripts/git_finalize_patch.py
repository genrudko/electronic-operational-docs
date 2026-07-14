
#!/usr/bin/env python3
"""Safely commit and push a patch after its functional gates have passed."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

BLOCKED_EXACT = {".env"}
BLOCKED_PREFIXES = (
    ".venv/",
    "backups/",
    "logs/",
    "media/",
    "staticfiles/",
)
BLOCKED_SUFFIXES = (
    ".sqlite3",
    ".db",
    ".log",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
)
SECRET_PATTERNS = (
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--patch-id", required=True)
    parser.add_argument("--message", required=True)
    parser.add_argument("--amend", action="store_true")
    parser.add_argument("--skip-push", action="store_true")
    return parser.parse_args()


def run(command: list[str], root: Path) -> subprocess.CompletedProcess[str]:
    print("$", subprocess.list2cmdline(command))
    result = subprocess.run(
        command,
        cwd=root,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip())
    if result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr)
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed with exit code {result.returncode}: "
            f"{subprocess.list2cmdline(command)}"
        )
    return result


def normalize(path: str) -> str:
    return path.replace("\\", "/")


def blocked(path: str) -> bool:
    normalized = normalize(path)
    lowered = normalized.lower()
    if normalized in BLOCKED_EXACT:
        return True
    if any(normalized.startswith(prefix) for prefix in BLOCKED_PREFIXES):
        return True
    if normalized.startswith("data/") and normalized != "data/.gitkeep":
        return True
    return any(lowered.endswith(suffix) for suffix in BLOCKED_SUFFIXES)


def validate(paths: Iterable[str]) -> None:
    invalid = sorted({normalize(path) for path in paths if blocked(path)})
    if invalid:
        listing = "\n".join(f" - {path}" for path in invalid)
        raise RuntimeError(f"Blocked staged files:\n{listing}")


def scan(root: Path, paths: list[str]) -> None:
    findings: list[str] = []
    for relative in paths:
        path = root / relative
        if not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if any(pattern.search(content) for pattern in SECRET_PATTERNS):
            findings.append(relative)
    if findings:
        listing = "\n".join(f" - {path}" for path in sorted(set(findings)))
        raise RuntimeError(f"Possible credentials detected:\n{listing}")


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()

    if not (root / ".git").is_dir():
        raise RuntimeError(f"Not a Git repository: {root}")

    run(["git", "diff", "--check"], root)
    run(["git", "add", "-A"], root)

    staged = run(
        ["git", "diff", "--cached", "--name-only"],
        root,
    ).stdout.splitlines()
    staged = [path.strip() for path in staged if path.strip()]

    if not staged:
        print("No changes to commit.")
        return 0

    validate(staged)
    scan(root, staged)

    print("Staged files:")
    for path in staged:
        print(" -", path)

    if args.amend:
        run(["git", "commit", "--amend", "--no-edit"], root)
    else:
        run(["git", "commit", "-m", args.message], root)

    commit = run(["git", "rev-parse", "HEAD"], root).stdout.strip()
    print("Commit:", commit)

    if not args.skip_push:
        run(["git", "push", "origin", "main"], root)
        print("Push: OK")

    print(f"{args.patch_id.upper()}_GIT_FINALIZED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"GIT FINALIZE FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
