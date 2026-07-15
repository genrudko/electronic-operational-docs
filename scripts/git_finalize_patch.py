#!/usr/bin/env python3
"""Safely commit and push an EOD patch after every gate has passed."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

REPOSITORY_FULL_NAME = "genrudko/electronic-operational-docs"
EXPECTED_BRANCH = "main"

BLOCKED_EXACT = {".env"}
BLOCKED_PREFIXES = (
    ".venv/",
    "backups/",
    "logs/",
    "media/",
    "staticfiles/",
    "Инструкции/",
)
BLOCKED_SUFFIXES = (
    ".sqlite3",
    ".db",
    ".log",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".doc",
    ".docx",
    ".xls",
    ".xlsx",
    ".pdf",
    ".ppt",
    ".pptx",
    ".zip",
    ".7z",
    ".rar",
)
BLOCKED_BASENAME_PREFIXES = (
    "chatgpt-",
    "eod_full_project_plan_v2_",
)
SECRET_PATTERNS = (
    re.compile(r"\bgh[opusr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)

# Every staged path, including an already tracked modification or deletion,
# must belong to the program code/documentation allowlist. This closes the
# historical gap where `git add -u` could stage a previously tracked foreign
# document even though new untracked files were protected.
ALLOWLIST_PREFIXES = ("src/", "scripts/", "docs/")
ALLOWLIST_EXACT = {
    "manage.py",
    "pyproject.toml",
    "README.md",
    "compose.yaml",
    ".gitattributes",
    ".gitignore",
    ".env.example",
}


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
    return path.replace("\\", "/").strip("/")


def split_nul_paths(value: str) -> list[str]:
    return [normalize(path) for path in value.split("\0") if path]


def in_allowlist(path: str) -> bool:
    normalized = normalize(path)
    if normalized in ALLOWLIST_EXACT:
        return True
    return any(normalized.startswith(prefix) for prefix in ALLOWLIST_PREFIXES)


def blocked(path: str) -> bool:
    normalized = normalize(path)
    lowered = normalized.casefold()
    basename = Path(normalized).name.casefold()
    if normalized in BLOCKED_EXACT:
        return True
    if any(lowered.startswith(prefix.casefold()) for prefix in BLOCKED_PREFIXES):
        return True
    if normalized.startswith("data/") and normalized != "data/.gitkeep":
        return True
    if any(basename.startswith(prefix) for prefix in BLOCKED_BASENAME_PREFIXES):
        return True
    return any(lowered.endswith(suffix) for suffix in BLOCKED_SUFFIXES)


def validate_allowlisted(paths: Iterable[str]) -> None:
    invalid = sorted({normalize(path) for path in paths if not in_allowlist(path)})
    if invalid:
        listing = "\n".join(f" - {path}" for path in invalid)
        raise RuntimeError(f"Files outside the project allowlist:\n{listing}")


def validate_not_blocked(paths: Iterable[str]) -> None:
    invalid = sorted({normalize(path) for path in paths if blocked(path)})
    if invalid:
        listing = "\n".join(f" - {path}" for path in invalid)
        raise RuntimeError(f"Blocked files:\n{listing}")


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


def verify_repository(root: Path) -> None:
    branch = run(["git", "branch", "--show-current"], root).stdout.strip()
    if branch != EXPECTED_BRANCH:
        raise RuntimeError(f"Expected branch {EXPECTED_BRANCH!r}, got {branch!r}.")

    origin = run(["git", "remote", "get-url", "origin"], root).stdout.strip()
    normalized = origin.casefold().removesuffix(".git")
    expected = REPOSITORY_FULL_NAME.casefold()
    if not normalized.endswith(expected):
        raise RuntimeError(f"Unexpected origin remote: {origin}")


def verify_private_repository(root: Path) -> None:
    if shutil.which("gh") is None:
        raise RuntimeError("GitHub CLI (gh) is required for safe finalization.")
    output = run(
        [
            "gh",
            "repo",
            "view",
            REPOSITORY_FULL_NAME,
            "--json",
            "nameWithOwner,visibility",
            "--jq",
            '.nameWithOwner + " " + .visibility',
        ],
        root,
    ).stdout.strip()
    expected = f"{REPOSITORY_FULL_NAME} PRIVATE"
    if output != expected:
        raise RuntimeError(
            "Repository finalization is allowed only for the expected private "
            f"repository. Expected {expected!r}, got {output!r}."
        )


def changed_paths(root: Path) -> tuple[list[str], list[str], list[str]]:
    unstaged = split_nul_paths(
        run(["git", "diff", "--name-only", "-z"], root).stdout
    )
    staged = split_nul_paths(
        run(["git", "diff", "--cached", "--name-only", "-z"], root).stdout
    )
    untracked = split_nul_paths(
        run(["git", "ls-files", "--others", "--exclude-standard", "-z"], root).stdout
    )
    return unstaged, staged, untracked


def main() -> int:
    args = parse_args()
    root = args.root.expanduser().resolve()

    if not (root / ".git").is_dir():
        raise RuntimeError(f"Not a Git repository: {root}")

    verify_repository(root)
    verify_private_repository(root)
    run(["git", "diff", "--check"], root)

    unstaged, staged_before, untracked = changed_paths(root)
    tracked_candidates = sorted(set(unstaged) | set(staged_before))
    validate_allowlisted(tracked_candidates)
    validate_not_blocked(tracked_candidates)

    allowed_untracked = [
        path for path in untracked if in_allowlist(path) and not blocked(path)
    ]
    skipped_untracked = [path for path in untracked if path not in allowed_untracked]

    if unstaged:
        run(["git", "add", "-u"], root)
    if allowed_untracked:
        run(["git", "add", "--", *allowed_untracked], root)

    if skipped_untracked:
        print("Skipped untracked files outside the allowlist or blocked by policy:")
        for path in sorted(skipped_untracked):
            print(" -", path)

    staged = split_nul_paths(
        run(["git", "diff", "--cached", "--name-only", "-z"], root).stdout
    )
    if not staged:
        print("No changes to commit.")
        return 0

    validate_allowlisted(staged)
    validate_not_blocked(staged)
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
        verify_private_repository(root)
        run(["git", "push", "origin", EXPECTED_BRANCH], root)
        print("Push: OK")

    print(f"{args.patch_id.upper()}_GIT_FINALIZED")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"GIT FINALIZE FAILED: {type(exc).__name__}: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
