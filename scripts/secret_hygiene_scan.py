from __future__ import annotations

import argparse
import ast
import collections
import re
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from scripts.secret_hygiene import (
    DEFAULT_ALLOWLIST,
    FIXTURE_PATH,
    Finding,
    apply_allowlist,
    load_allowlist,
)

MAX_TEXT_BYTES = 2 * 1024 * 1024
BINARY_SUFFIXES = {
    ".7z", ".avi", ".bmp", ".db", ".doc", ".docx", ".eot", ".gif", ".gz",
    ".ico", ".jpeg", ".jpg", ".m4a", ".mkv", ".mov", ".mp3", ".mp4",
    ".ogg", ".otf", ".pdf", ".png", ".sqlite", ".tar", ".ttf", ".wav",
    ".webm", ".webp", ".woff", ".woff2", ".xls", ".xlsx", ".zip",
}
ASSIGNMENT = re.compile(
    r"^\s*(?:-\s*)?[\"']?(?P<name>[A-Za-z_][A-Za-z0-9_.-]*)[\"']?"
    r"\s*(?::|=)\s*(?P<value>[^\n]+)$"
)
INLINE_ENV_ASSIGNMENT = re.compile(
    r"(?:^|\s)(?:--env|-e)\s+[\"']?"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_.-]*)=(?P<value>[^\s\"']+)"
)
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")
SECRET_DSN = re.compile(
    r"(?i)\b(?:postgres(?:ql)?|mysql|mariadb|redis|amqp|mongodb(?:\+srv)?)://"
    r"[^\s:/@]+:(?P<value>[^\s/@]+)@"
)
TOKEN_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("github-fine-grained-token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("aws-access-key", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("stripe-live-key", re.compile(r"\b(?:sk|rk)_live_[A-Za-z0-9]{16,}\b")),
)
SHELL_OUTPUT_CALL = re.compile(r"(?i)(?:^|[;&|]\s*|\s)(?:echo|printf)\b")
SHELL_SECRET_REFERENCE = re.compile(
    r"(?i)\$\{?[A-Z0-9_]*(?:PASSWORD|PASSWD|PWD|API[_-]?KEY|API[_-]?TOKEN|"
    r"ACCESS[_-]?TOKEN|AUTH[_-]?TOKEN|SECRET[_-]?KEY|PRIVATE[_-]?KEY|"
    r"WEBHOOK[_-]?SECRET|CLIENT[_-]?SECRET|DATABASE[_-]?URL|DSN)[A-Z0-9_]*\}?"
)
SHELL_TRACE = re.compile(
    r"(?:^|\s)set\s+(?:-x|-[A-Za-z]*x[A-Za-z]*|-o\s+xtrace)(?:\s|$)"
)
ARTIFACT_ACTION = re.compile(r"actions/upload-artifact@")
ARTIFACT_RISKY_PATH = re.compile(
    r"(?i)(?:\.env(?:\.|$)|secret|credential|private[_-]?key|"
    r"\.(?:pem|key|log|txt|json|xml|csv)(?:$|\s)|"
    r"(?:^|[/_-])(?:raw|diagnostic|result|output)(?:[/_.-]|$))"
)
PLACEHOLDER_TOKENS = (
    "${", "${{", "<required", "<secret", "<token", "<password", "<generated",
    "change-me", "changeme", "replace-me", "replace-this", "replace-with",
    "placeholder", "example.invalid", "redacted", "not-for-deployment",
    "fixture-only", "test-only", "validation-only", "isolated-test", "not-persistent",
    "dummy", "fake",
)
COMMON_TEST_PLACEHOLDERS = {
    "password", "passwd", "secret", "token", "test-password", "test-secret",
    "test-token", "wrong-password", "invalid-password", "incorrect-password",
}
HISTORY_GREP_PATTERN = (
    r"PRIVATE KEY|PASSWORD|PASSWD|PWD|API[_-]?KEY|API[_-]?TOKEN|ACCESS[_-]?TOKEN|"
    r"AUTH[_-]?TOKEN|SECRET[_-]?KEY|PRIVATE[_-]?KEY|WEBHOOK[_-]?SECRET|"
    r"CLIENT[_-]?SECRET|DATABASE[_-]?URL|DSN|github_pat_|gh[pousr]_|xox[baprs]-|"
    r"postgres(ql)?://|mysql://|mariadb://|redis://|amqp://|mongodb(\+srv)?://"
)


def is_sensitive_name(name: str) -> bool:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    if normalized in {"PASSWORD", "PASSWD", "PWD", "SECRET", "TOKEN", "DSN"}:
        return True
    return normalized.endswith(
        (
            "_PASSWORD", "_PASSWD", "_PWD", "_API_KEY", "_API_TOKEN",
            "_ACCESS_TOKEN", "_AUTH_TOKEN", "_SECRET_KEY", "_PRIVATE_KEY",
            "_WEBHOOK_SECRET", "_CLIENT_SECRET", "_DATABASE_URL", "_DSN",
        )
    )


def is_safe_placeholder(value: str) -> bool:
    lowered = value.casefold().strip()
    return (
        not lowered
        or any(token in lowered for token in PLACEHOLDER_TOKENS)
        or lowered in COMMON_TEST_PLACEHOLDERS
        or bool(re.fullmatch(r"\*{3,}|x{6,}", lowered))
    )


def is_named_test_fixture(path: str, value: str) -> bool:
    lowered_path = path.casefold()
    is_test = (
        lowered_path.startswith("tests/")
        or "/tests/" in lowered_path
        or lowered_path.endswith("_test.py")
        or lowered_path.endswith(".test.js")
    )
    lowered_value = value.casefold()
    return is_test and ("fixture" in lowered_value or "test" in lowered_value)


def finding(path: str, line: int, rule: str, actual: str, value: str) -> Finding:
    return Finding(path=path, line=line, rule=rule, actual_class=actual, value=value)


def target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for item in node.elts for name in target_names(item)]
    return []


def python_findings(path: str, text: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    results: list[Finding] = []
    test_fixture_assignments: set[int] = set()
    if "/tests/" in path.casefold() or path.casefold().startswith("tests/"):
        for class_node in (item for item in ast.walk(tree) if isinstance(item, ast.ClassDef)):
            if class_node.name.endswith(("Test", "Tests", "TestCase")):
                test_fixture_assignments.update(
                    id(item)
                    for item in ast.walk(class_node)
                    if isinstance(item, (ast.Assign, ast.AnnAssign))
                )
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        value_node: ast.AST | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value_node = node.value
        if (
            value_node is not None
            and isinstance(value_node, ast.Constant)
            and isinstance(value_node.value, str)
        ):
            value = value_node.value
            for name in [name for target in targets for name in target_names(target)]:
                if (
                    not is_sensitive_name(name)
                    or is_safe_placeholder(value)
                    or is_named_test_fixture(path, value)
                    or (
                        id(node) in test_fixture_assignments
                        and name.casefold() == "password"
                    )
                ):
                    continue
                upper = name.upper()
                rule = "explicit-credential-assignment"
                actual = "committed-credential-literal"
                if "DEMO" in upper and upper.endswith(("PASSWORD", "PASSWD", "PWD")):
                    rule = "reusable-demo-credential"
                    actual = "reusable-demo-password"
                results.append(finding(path, node.lineno, rule, actual, value))
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name):
            call_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            call_name = node.func.attr
        else:
            call_name = ""
        if call_name not in {
            "print", "write", "debug", "info", "warning", "error", "critical",
            "exception",
        }:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and is_sensitive_name(child.id):
                results.append(
                    finding(
                        path,
                        node.lineno,
                        "credential-output",
                        "credential-bearing-output",
                        child.id,
                    )
                )
            elif isinstance(child, ast.Attribute) and is_sensitive_name(child.attr):
                results.append(
                    finding(
                        path,
                        node.lineno,
                        "credential-output",
                        "credential-bearing-output",
                        child.attr,
                    )
                )
    return results


def literal_value(raw: str) -> str | None:
    value = raw.strip().rstrip(",")
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    if not value or value in {"None", "null", "NULL", "~", "''", '\"\"'}:
        return ""
    if any(marker in value for marker in ("${", "$(", "${{", "`")):
        return None
    if value[0:1] in {"'", '\"'}:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            return None
        return parsed if isinstance(parsed, str) else None
    if re.fullmatch(r"[-+]?\d+(?:\.\d+)?", value):
        return None
    if value.casefold() in {"true", "false", "yes", "no", "on", "off"}:
        return None
    if value.startswith(("$", "<")):
        return None
    if any(marker in value for marker in ("(", ")", "[", "]", "{", "}")):
        return None
    if re.search(r"\b(?:if|for|else|and|or)\b|\.get\(", value):
        return None
    return value


def step_block(lines: list[str], start: int) -> str:
    block = [lines[start]]
    base_indent = len(lines[start]) - len(lines[start].lstrip())
    for line in lines[start + 1 :]:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("- name:") and indent <= base_indent:
            break
        block.append(line)
    return "\n".join(block)


def redacted_outputs(workflow: str) -> set[str]:
    return {
        match.group("path")
        for match in re.finditer(
            r"secret_hygiene\.py\s+redact"
            r"(?:(?!\n\s{4,}-\s+name:).)*?"
            r"--output\s+[\"']?(?P<path>[^\s\"'\\]+)",
            workflow,
            re.IGNORECASE | re.DOTALL,
        )
    }


def artifact_paths(block: str) -> list[str]:
    paths: list[str] = []
    collecting = False
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("path:"):
            value = stripped.split(":", 1)[1].strip()
            collecting = value == "|"
            if value and value != "|":
                paths.append(value.strip("\"'"))
            continue
        if collecting:
            if stripped.startswith("- "):
                paths.append(stripped[2:].strip("\"'"))
            elif stripped and not line.startswith(" " * 10):
                collecting = False
    return paths


def scan_text(path: str, text: str) -> list[Finding]:
    if path == FIXTURE_PATH:
        return []
    results: list[Finding] = []
    lines = text.splitlines()
    is_python = path.casefold().endswith(".py")
    is_workflow = path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
    if is_python:
        results.extend(python_findings(path, text))
    for number, line in enumerate(lines, start=1):
        if PRIVATE_KEY.search(line):
            results.append(
                finding(path, number, "private-key-marker", "private-key-material", line)
            )
        for match in SECRET_DSN.finditer(line):
            value = match.group("value")
            if not is_safe_placeholder(value) and not is_named_test_fixture(path, value):
                results.append(
                    finding(path, number, "secret-bearing-dsn", "credential-in-url", value)
                )
        for token_class, pattern in TOKEN_PATTERNS:
            for match in pattern.finditer(line):
                value = match.group(0)
                if not is_named_test_fixture(path, value):
                    results.append(finding(path, number, "token-like-value", token_class, value))
        if not is_python:
            assignment = ASSIGNMENT.match(line)
            if assignment and is_sensitive_name(assignment.group("name")):
                name = assignment.group("name")
                value = literal_value(assignment.group("value"))
                if (
                    value is not None
                    and not is_safe_placeholder(value)
                    and not is_named_test_fixture(path, value)
                ):
                    upper = name.upper()
                    rule = "explicit-credential-assignment"
                    actual = "committed-credential-literal"
                    if "DEMO" in upper and upper.endswith(("PASSWORD", "PASSWD", "PWD")):
                        rule = "reusable-demo-credential"
                        actual = "reusable-demo-password"
                    results.append(finding(path, number, rule, actual, value))
            for match in INLINE_ENV_ASSIGNMENT.finditer(line):
                name = match.group("name")
                value = literal_value(match.group("value"))
                if is_sensitive_name(name) and value is not None and not is_safe_placeholder(value):
                    results.append(
                        finding(
                            path,
                            number,
                            "explicit-credential-assignment",
                            "committed-credential-literal",
                            value,
                        )
                    )
            if (
                SHELL_OUTPUT_CALL.search(line)
                and SHELL_SECRET_REFERENCE.search(line)
                and "::add-mask::" not in line
            ):
                results.append(
                    finding(path, number, "credential-output", "credential-bearing-output", line)
                )
            if SHELL_TRACE.search(line):
                nearby = "\n".join(lines[number - 1 : min(len(lines), number + 12)])
                if SHELL_SECRET_REFERENCE.search(nearby):
                    results.append(
                        finding(
                            path,
                            number,
                            "shell-xtrace-secret",
                            "xtrace-near-secret-command",
                            nearby,
                        )
                    )
        if re.search(
            r"(?i)(?:output of:|run:?)\s*(?:sudo\s+)?cat\s+"
            r"[^\s]*(?:key|secret|credential)",
            line,
        ):
            results.append(
                finding(
                    path,
                    number,
                    "credential-retrieval-instruction",
                    "operator-secret-print-command",
                    line,
                )
            )
    if is_workflow:
        sanitised = redacted_outputs(text)
        starts = [i for i, line in enumerate(lines) if line.lstrip().startswith("- name:")]
        for start in starts or ([0] if lines else []):
            block = step_block(lines, start)
            if "GITHUB_STEP_SUMMARY" in block:
                raw_names = [
                    name
                    for name in re.findall(
                        r"\$\{?([A-Za-z_][A-Za-z0-9_]*(?:_OUTPUT|_LOG|_RESPONSE|_RAW))\}?",
                        block,
                        re.IGNORECASE,
                    )
                    if name.upper() != "GITHUB_OUTPUT"
                ]
                unsafe_cat = any(
                    match.group("path") not in sanitised
                    for match in re.finditer(
                        r"(?im)^\s*(?:cat|tail|head)\s+[\"']?(?P<path>[^\s\"']+)",
                        block,
                    )
                )
                if raw_names or unsafe_cat:
                    results.append(
                        finding(
                            path,
                            start + 1,
                            "workflow-summary-leak",
                            "unbounded-output-in-summary",
                            block,
                        )
                    )
            if ARTIFACT_ACTION.search(block):
                for artifact_path in artifact_paths(block):
                    if (
                        ARTIFACT_RISKY_PATH.search(artifact_path)
                        and artifact_path not in sanitised
                    ):
                        results.append(
                            finding(
                                path,
                                start + 1,
                                "artifact-leak",
                                "raw-or-secret-bearing-artifact",
                                block,
                            )
                        )
                        break
    unique = {(item.path, item.line, item.rule, item.identifier): item for item in results}
    return list(unique.values())


def tracked_paths(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return [root / item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]


def read_text(path: Path) -> str | None:
    if path.suffix.casefold() in BINARY_SUFFIXES or path.stat().st_size > MAX_TEXT_BYTES:
        return None
    data = path.read_bytes()
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def scan_repository(root: Path) -> list[Finding]:
    results: list[Finding] = []
    for file_path in tracked_paths(root):
        relative = file_path.relative_to(root).as_posix()
        text = read_text(file_path)
        if text is not None:
            results.extend(scan_text(relative, text))
    return sorted(results, key=lambda item: (item.path, item.line, item.rule, item.identifier))


def history_inventory(root: Path, max_commits: int) -> dict[str, object]:
    revs = subprocess.run(
        ["git", "-C", str(root), "rev-list", f"--max-count={max_commits}", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    ).stdout.splitlines()
    completed = subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "grep",
            "-I",
            "-i",
            "-n",
            "-E",
            HISTORY_GREP_PATTERN,
            *revs,
        ],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        errors="replace",
    )
    unique: dict[tuple[str, int, str, str], Finding] = {}
    for raw in completed.stdout.splitlines():
        try:
            _, path, line_raw, line_text = raw.split(":", 3)
            line_number = int(line_raw)
        except (ValueError, IndexError):
            continue
        if path == FIXTURE_PATH:
            continue
        for item in scan_text(path, line_text):
            normalized = Finding(path, line_number, item.rule, item.actual_class, item.value)
            unique[(path, line_number, normalized.rule, normalized.value_hash)] = normalized
    counts = collections.Counter(item.rule for item in unique.values())
    return {
        "schema": 1,
        "commit_depth": len(revs),
        "unique_findings": len(unique),
        "counts_by_rule": dict(sorted(counts.items())),
        "identifiers": sorted(item.identifier for item in unique.values()),
    }


def command_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    allowlist_path = root / args.allowlist
    results = scan_repository(root)
    entries, errors = load_allowlist(allowlist_path)
    results, allow_errors = apply_allowlist(results, entries, allowlist_path)
    errors.extend(allow_errors)
    for item in results:
        print(item.diagnostic())
    for error in errors:
        print(error)
    if results or errors:
        print(
            f"SECRET_HYGIENE=FAIL findings={len(results)} contract_errors={len(errors)}",
            file=sys.stderr,
        )
        return 1
    print(
        f"SECRET_HYGIENE=PASS scanned_files={len(tracked_paths(root))} "
        f"allowlist_entries={len(entries)}"
    )
    return 0


def command_history(args: argparse.Namespace) -> int:
    report = history_inventory(Path(args.root).resolve(), args.max_commits)
    counts = ",".join(
        f"{key}:{value}" for key, value in report["counts_by_rule"].items()
    ) or "none"
    print(
        f"HISTORY_SECRET_INVENTORY commits={report['commit_depth']} "
        f"unique_findings={report['unique_findings']} counts={counts}"
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="AST-aware EOD tracked-content secret scanner"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    scan = subparsers.add_parser("scan")
    scan.add_argument("--root", default=".")
    scan.add_argument("--allowlist", default=DEFAULT_ALLOWLIST)
    scan.set_defaults(func=command_scan)
    history = subparsers.add_parser("history-inventory")
    history.add_argument("--root", default=".")
    history.add_argument("--max-commits", type=int, default=250)
    history.set_defaults(func=command_history)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
