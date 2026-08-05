from __future__ import annotations

import ast
import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path

from scripts.secret_hygiene import Finding
from scripts.secret_hygiene_scan import (
    is_named_test_fixture,
    is_safe_placeholder,
    is_sensitive_name,
)


def scan_python_keyword_literals(path: str, text: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []

    findings: list[Finding] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if (
                keyword.arg is None
                or not is_sensitive_name(keyword.arg)
                or not isinstance(keyword.value, ast.Constant)
                or not isinstance(keyword.value.value, str)
            ):
                continue
            value = keyword.value.value
            if is_safe_placeholder(value) or is_named_test_fixture(path, value):
                continue
            findings.append(
                Finding(
                    path=path,
                    line=keyword.value.lineno,
                    rule="sensitive-keyword-literal",
                    actual_class="committed-credential-keyword-literal",
                    value=value,
                )
            )
    return findings


def tracked_python_paths(root: Path) -> Iterable[Path]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z", "*.py"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    for raw in completed.stdout.split(b"\0"):
        if raw:
            yield root / raw.decode("utf-8")


def scan_repository(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for file_path in tracked_python_paths(root):
        relative = file_path.relative_to(root).as_posix()
        text = file_path.read_text(encoding="utf-8", errors="replace")
        findings.extend(scan_python_keyword_literals(relative, text))
    return sorted(findings, key=lambda item: (item.path, item.line, item.identifier))


def main() -> int:
    root = Path(".").resolve()
    findings = scan_repository(root)
    for finding in findings:
        print(finding.diagnostic())
    if findings:
        print(
            f"SECRET_KEYWORD_HYGIENE=FAIL findings={len(findings)}",
            file=sys.stderr,
        )
        return 1
    print("SECRET_KEYWORD_HYGIENE=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
