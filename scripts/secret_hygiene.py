from __future__ import annotations

import argparse
import ast
import collections
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ALLOWLIST = ".github/secret-hygiene-allowlist.json"
MAX_TEXT_BYTES = 2 * 1024 * 1024
BINARY_SUFFIXES = {
    ".7z", ".avi", ".bmp", ".db", ".doc", ".docx", ".eot", ".gif", ".gz",
    ".ico", ".jpeg", ".jpg", ".m4a", ".mkv", ".mov", ".mp3", ".mp4",
    ".ogg", ".otf", ".pdf", ".png", ".sqlite", ".tar", ".ttf", ".wav",
    ".webm", ".webp", ".woff", ".woff2", ".xls", ".xlsx", ".zip",
}
SENSITIVE_NAME = re.compile(
    r"(?i)(?:password|passwd|pwd|api[_-]?key|api[_-]?token|access[_-]?token|"
    r"auth[_-]?token|secret(?:[_-]?key)?|private[_-]?key|webhook[_-]?secret|"
    r"client[_-]?secret|database[_-]?url|dsn)"
)
ASSIGNMENT = re.compile(
    r"^\s*(?:-\s*)?[\"']?(?P<name>[A-Za-z_][A-Za-z0-9_.-]*)[\"']?"
    r"\s*(?P<separator>:|=)\s*(?P<value>[^\n]+)$"
)
JSON_PAIR = re.compile(
    r"^\s*(?:[,{[]\s*)?[\"'](?P<name>[A-Za-z_][A-Za-z0-9_.-]*)[\"']"
    r"\s*:\s*[\"'](?P<value>[^\"']+)[\"']\s*[,}]?\s*$"
)
INLINE_ENV_ASSIGNMENT = re.compile(
    r"(?:^|\s)(?:--env|-e)\s+[\"']?"
    r"(?P<name>[A-Za-z_][A-Za-z0-9_.-]*)=(?P<value>[^\s\"']+)"
)
PRIVATE_KEY_MARKER = re.compile(
    r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----"
)
PRIVATE_KEY_BLOCK = re.compile(
    r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----.*?"
    r"-----END (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----",
    re.DOTALL,
)
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
OUTPUT_CALL = re.compile(
    r"(?i)(?:\becho\b|\bprintf\b|\bprint\s*\(|stdout\.write|stderr\.write|"
    r"logger\.|logging\.|console\.log)"
)
SHELL_SECRET_REFERENCE = re.compile(
    r"(?i)\$\{?[A-Z0-9_]*(?:PASSWORD|PASSWD|PWD|API[_-]?KEY|API[_-]?TOKEN|"
    r"ACCESS[_-]?TOKEN|AUTH[_-]?TOKEN|SECRET(?:[_-]?KEY)?|PRIVATE[_-]?KEY|"
    r"WEBHOOK[_-]?SECRET|CLIENT[_-]?SECRET|DATABASE[_-]?URL|DSN)[A-Z0-9_]*\}?"
)
BRACED_SECRET_REFERENCE = re.compile(
    r"(?i)\{[^}\n]*(?:password|passwd|pwd|api[_-]?key|api[_-]?token|"
    r"access[_-]?token|auth[_-]?token|secret(?:[_-]?key)?|private[_-]?key|"
    r"webhook[_-]?secret|client[_-]?secret|database[_-]?url|dsn)[^}\n]*\}"
)
SHELL_TRACE = re.compile(
    r"(?:^|\s)set\s+(?:-x|-[A-Za-z]*x[A-Za-z]*|-o\s+xtrace)(?:\s|$)"
)
ARTIFACT_ACTION = re.compile(r"actions/upload-artifact@")
TEXT_OUTPUT_PATH = re.compile(
    r"(?i)(?:\.env(?:\.|$)|secret|credential|private[_-]?key|"
    r"\.(?:pem|key|log|txt|json|xml|csv|md)(?:$|\s)|"
    r"(?:^|[/_.-])(?:raw|saniti[sz]ed|diagnostic|result|output)(?:[/_.-]|$))"
)
APPROVED_PLACEHOLDER_VALUES = {
    "[redacted]",
    "change-me",
    "changeme",
    "example.invalid",
    "not-for-deployment",
    "redacted",
    "replace-me",
    "replace-this-in-real-deployment",
    "replace-with-a-long-random-secret",
}
APPROVED_ANGLE_PLACEHOLDER = re.compile(
    r"(?i)^<(?:required|generated|secret|token|password)(?:[-_ :][^<>]+)?>$"
)
MASKED_PLACEHOLDER = re.compile(r"^(?:\*{3,}|x{6,})$", re.IGNORECASE)
HISTORY_GREP_PATTERN = (
    r"PRIVATE KEY|PASSWORD|PASSWD|PWD|API[_-]?KEY|API[_-]?TOKEN|ACCESS[_-]?TOKEN|"
    r"AUTH[_-]?TOKEN|SECRET[_-]?KEY|PRIVATE[_-]?KEY|WEBHOOK[_-]?SECRET|"
    r"CLIENT[_-]?SECRET|DATABASE[_-]?URL|DSN|github_pat_|gh[pousr]_|xox[baprs]-|"
    r"postgres(ql)?://|mysql://|mariadb://|redis://|amqp://|mongodb(\+srv)?://"
)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    rule: str
    actual_class: str
    value: str

    @property
    def value_hash(self) -> str:
        return hashlib.sha256(self.value.encode("utf-8", errors="replace")).hexdigest()

    @property
    def identifier(self) -> str:
        material = (
            f"secret-hygiene-v2\0{self.path}\0{self.line}\0{self.rule}\0{self.value_hash}"
        )
        return "finding-" + hashlib.sha256(material.encode()).hexdigest()[:16]

    def diagnostic(self) -> str:
        return (
            f"file={self.path} line={self.line} identifier={self.identifier} "
            f"rule={self.rule} expected=non-secret-or-runtime-injection "
            f"actual={self.actual_class}"
        )


@dataclass(frozen=True)
class AllowEntry:
    path: str
    rule: str
    identifier: str
    rationale: str
    owner: str
    expires: str

    @property
    def key(self) -> tuple[str, str, str]:
        return self.path, self.rule, self.identifier


def is_sensitive_name(name: str) -> bool:
    normalized = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").upper()
    if normalized in {"PASSWORD", "PASSWD", "PWD", "SECRET", "TOKEN", "DSN"}:
        return True
    return normalized.endswith(
        (
            "_PASSWORD",
            "_PASSWD",
            "_PWD",
            "_API_KEY",
            "_API_TOKEN",
            "_ACCESS_TOKEN",
            "_AUTH_TOKEN",
            "_SECRET",
            "_SECRET_KEY",
            "_PRIVATE_KEY",
            "_WEBHOOK_SECRET",
            "_CLIENT_SECRET",
            "_DATABASE_URL",
            "_DSN",
        )
    )


def _strip_rhs(raw: str) -> str:
    value = raw.strip()
    if value.endswith(","):
        value = value[:-1].rstrip()
    if " #" in value:
        value = value.split(" #", 1)[0].rstrip()
    return value.strip()


def _literal_string(raw: str, path: str = "") -> str | None:
    value = _strip_rhs(raw)
    if not value or value in {"None", "null", "NULL", "~", "''", '\"\"'}:
        return ""
    if any(marker in value for marker in ("${", "$(", "${{", "`")):
        return None
    if re.match(r"(?i)^(?:f|rf|fr|r|b)[\"']", value):
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
    if path.casefold().endswith(".py"):
        return None
    if any(marker in value for marker in ("(", ")", "[", "]", "{", "}")):
        return None
    if re.search(r"\b(?:if|for|else|and|or)\b|\.get\(", value):
        return None
    return value


def is_safe_placeholder(raw_value: str, path: str = "") -> bool:
    literal = _literal_string(raw_value, path)
    if literal is None or literal == "":
        return True
    lowered = literal.casefold().strip()
    return (
        lowered in APPROVED_PLACEHOLDER_VALUES
        or bool(APPROVED_ANGLE_PLACEHOLDER.fullmatch(literal.strip()))
        or bool(MASKED_PLACEHOLDER.fullmatch(literal.strip()))
    )


def _finding(path: str, line: int, rule: str, actual: str, value: str) -> Finding:
    return Finding(path=path, line=line, rule=rule, actual_class=actual, value=value)


def _target_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Name):
        return [node.id]
    if isinstance(node, ast.Attribute):
        return [node.attr]
    if isinstance(node, (ast.Tuple, ast.List)):
        return [name for item in node.elts for name in _target_names(item)]
    return []


def _call_name(node: ast.Call) -> str:
    if isinstance(node.func, ast.Name):
        return node.func.id
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return ""


def _literal_rule(name: str) -> tuple[str, str]:
    upper = re.sub(r"[^A-Za-z0-9]+", "_", name).upper()
    if "DEMO" in upper and upper.endswith(("PASSWORD", "PASSWD", "PWD")):
        return "reusable-demo-credential", "reusable-demo-password"
    return "explicit-credential-assignment", "committed-credential-literal"


def scan_python(path: str, text: str) -> list[Finding]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    findings: list[Finding] = []
    for node in ast.walk(tree):
        targets: list[ast.AST] = []
        value_node: ast.AST | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value_node = node.value
        if isinstance(value_node, ast.Constant) and isinstance(value_node.value, str):
            for name in [name for target in targets for name in _target_names(target)]:
                if not is_sensitive_name(name):
                    continue
                value = value_node.value
                if is_safe_placeholder(repr(value), path):
                    continue
                rule, actual = _literal_rule(name)
                findings.append(_finding(path, node.lineno, rule, actual, value))

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
            if is_safe_placeholder(repr(value), path):
                continue
            findings.append(
                _finding(
                    path,
                    keyword.value.lineno,
                    "sensitive-keyword-literal",
                    "committed-credential-keyword-literal",
                    value,
                )
            )

        if _call_name(node) not in {
            "print",
            "write",
            "debug",
            "info",
            "warning",
            "error",
            "critical",
            "exception",
        }:
            continue
        for child in ast.walk(node):
            if isinstance(child, ast.Name) and is_sensitive_name(child.id):
                findings.append(
                    _finding(
                        path,
                        node.lineno,
                        "credential-output",
                        "credential-bearing-output",
                        child.id,
                    )
                )
            elif isinstance(child, ast.Attribute) and is_sensitive_name(child.attr):
                findings.append(
                    _finding(
                        path,
                        node.lineno,
                        "credential-output",
                        "credential-bearing-output",
                        child.attr,
                    )
                )
    return findings


def scan_python_keyword_literals(path: str, text: str) -> list[Finding]:
    return [item for item in scan_python(path, text) if item.rule == "sensitive-keyword-literal"]


def _output_references_secret_value(line: str) -> bool:
    if SHELL_SECRET_REFERENCE.search(line) or BRACED_SECRET_REFERENCE.search(line):
        return True
    without_strings = re.sub(r'''([\"'])(?:\\.|(?!\1).)*\1''', "", line)
    return bool(
        re.search(
            r"(?i)(?:print|write|log|debug|info|warning|error)\s*\([^)]*"
            r"\b(?:password|passwd|pwd|api[_-]?key|api[_-]?token|access[_-]?token|"
            r"auth[_-]?token|secret(?:[_-]?key)?|private[_-]?key|webhook[_-]?secret|"
            r"client[_-]?secret|database[_-]?url|dsn)\b",
            without_strings,
        )
    )


def _workflow_step_block(lines: list[str], start_index: int) -> str:
    block = [lines[start_index]]
    base_indent = len(lines[start_index]) - len(lines[start_index].lstrip())
    for line in lines[start_index + 1 :]:
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("- name:") and indent <= base_indent:
            break
        block.append(line)
    return "\n".join(block)


def _normalize_workflow_path(raw: str) -> str:
    value = raw.strip().strip("\"'").rstrip("\\")
    value = value.replace("${{ runner.temp }}", "<runner-temp>")
    value = value.replace("${RUNNER_TEMP}", "<runner-temp>")
    value = value.replace("$RUNNER_TEMP", "<runner-temp>")
    value = re.sub(r"/+", "/", value)
    return value


def _command_paths(workflow_text: str, command: str, option: str) -> set[str]:
    pattern = re.compile(
        rf"secret_hygiene\.py\s+{re.escape(command)}"
        rf"(?:(?!\n\s{{4,}}-\s+name:).)*?"
        rf"{re.escape(option)}\s+[\"']?(?P<path>[^\s\"'\\]+)",
        re.IGNORECASE | re.DOTALL,
    )
    return {_normalize_workflow_path(match.group("path")) for match in pattern.finditer(workflow_text)}


def _artifact_paths(block: str) -> list[str]:
    paths: list[str] = []
    collecting = False
    path_indent = 0
    for line in block.splitlines():
        stripped = line.strip()
        if stripped.startswith("path:"):
            value = stripped.split(":", 1)[1].strip()
            collecting = value == "|"
            path_indent = len(line) - len(line.lstrip())
            if value and value != "|":
                paths.append(_normalize_workflow_path(value))
            continue
        if collecting:
            indent = len(line) - len(line.lstrip())
            if stripped and indent <= path_indent:
                collecting = False
                continue
            if stripped:
                paths.append(_normalize_workflow_path(stripped.removeprefix("- ")))
    return paths


def _published_paths(block: str) -> list[tuple[str, str]]:
    published: list[tuple[str, str]] = []
    for match in re.finditer(
        r"(?im)^\s*(?:run:\s*)?(?:cat|tail|head)\s+[\"']?(?P<path>[^\s\"']+)", block
    ):
        path = _normalize_workflow_path(match.group("path"))
        if TEXT_OUTPUT_PATH.search(path):
            published.append(("workflow-log-or-summary", path))
    if ARTIFACT_ACTION.search(block):
        published.extend(("artifact", path) for path in _artifact_paths(block))
    return published


def _workflow_contract_findings(path: str, text: str) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    redacted = _command_paths(text, "redact", "--output")
    verified = _command_paths(text, "verify-sanitized", "--input")
    starts = [index for index, line in enumerate(lines) if line.lstrip().startswith("- name:")]
    for start in starts or ([0] if lines else []):
        block = _workflow_step_block(lines, start)
        for publication_class, output_path in _published_paths(block):
            if not TEXT_OUTPUT_PATH.search(output_path):
                continue
            if output_path in verified:
                continue
            rule = "post-redaction-verification-missing" if output_path in redacted else "artifact-leak"
            if publication_class == "workflow-log-or-summary" and output_path not in redacted:
                rule = "workflow-summary-leak" if "GITHUB_STEP_SUMMARY" in block else "credential-output"
            findings.append(
                _finding(
                    path,
                    start + 1,
                    rule,
                    "unverified-sanitized-output" if output_path in redacted else "raw-or-unverified-output",
                    block,
                )
            )
    return findings


def scan_text(path: str, text: str, *, enforce_workflow_contract: bool = True) -> list[Finding]:
    findings: list[Finding] = []
    lines = text.splitlines()
    is_python = path.casefold().endswith(".py")
    is_workflow = path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
    if is_python:
        findings.extend(scan_python(path, text))

    for index, line in enumerate(lines, start=1):
        if PRIVATE_KEY_MARKER.search(line):
            findings.append(_finding(path, index, "private-key-marker", "private-key-material", line))

        for match in SECRET_DSN.finditer(line):
            value = match.group("value")
            if not is_safe_placeholder(repr(value), path):
                findings.append(_finding(path, index, "secret-bearing-dsn", "credential-in-url", value))

        for token_class, pattern in TOKEN_PATTERNS:
            for match in pattern.finditer(line):
                findings.append(
                    _finding(path, index, "token-like-value", token_class, match.group(0))
                )

        if not is_python:
            assignment = ASSIGNMENT.match(line)
            json_pair = JSON_PAIR.match(line)
            for assignment_match in (assignment, json_pair):
                if assignment_match is None or not is_sensitive_name(assignment_match.group("name")):
                    continue
                name = assignment_match.group("name")
                raw_value = assignment_match.group("value")
                literal = _literal_string(raw_value, path)
                if literal is not None and not is_safe_placeholder(raw_value, path):
                    rule, actual = _literal_rule(name)
                    findings.append(_finding(path, index, rule, actual, literal))

            for inline_match in INLINE_ENV_ASSIGNMENT.finditer(line):
                name = inline_match.group("name")
                raw_value = inline_match.group("value")
                if not is_sensitive_name(name):
                    continue
                literal = _literal_string(raw_value, path)
                if literal is not None and not is_safe_placeholder(raw_value, path):
                    rule, actual = _literal_rule(name)
                    findings.append(_finding(path, index, rule, actual, literal))

            if (
                OUTPUT_CALL.search(line)
                and _output_references_secret_value(line)
                and "::add-mask::" not in line
                and "GITHUB_ENV" not in line
            ):
                findings.append(
                    _finding(path, index, "credential-output", "credential-bearing-output", line)
                )

            if SHELL_TRACE.search(line):
                nearby = "\n".join(lines[index - 1 : min(len(lines), index + 12)])
                if SHELL_SECRET_REFERENCE.search(nearby):
                    findings.append(
                        _finding(
                            path,
                            index,
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
            findings.append(
                _finding(
                    path,
                    index,
                    "credential-retrieval-instruction",
                    "operator-secret-print-command",
                    line,
                )
            )

    if is_workflow and enforce_workflow_contract:
        findings.extend(_workflow_contract_findings(path, text))

    unique = {(item.path, item.line, item.rule, item.identifier): item for item in findings}
    return sorted(unique.values(), key=lambda item: (item.path, item.line, item.rule, item.identifier))


def _tracked_paths(root: Path) -> list[Path]:
    completed = subprocess.run(
        ["git", "-C", str(root), "ls-files", "-z"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    return [root / item.decode("utf-8") for item in completed.stdout.split(b"\0") if item]


def _read_text(path: Path) -> str | None:
    if path.suffix.casefold() in BINARY_SUFFIXES:
        return None
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data:
        return None
    return data.decode("utf-8", errors="replace")


def scan_repository(root: Path) -> list[Finding]:
    findings: list[Finding] = []
    for file_path in _tracked_paths(root):
        relative = file_path.relative_to(root).as_posix()
        text = _read_text(file_path)
        if text is not None:
            findings.extend(scan_text(relative, text))
    return sorted(findings, key=lambda item: (item.path, item.line, item.rule, item.identifier))


def load_allowlist(
    path: Path,
    *,
    today: dt.date | None = None,
) -> tuple[list[AllowEntry], list[str]]:
    if not path.exists():
        return [], [
            f"file={path.as_posix()} identifier=allowlist-missing rule=allowlist-contract "
            "expected=versioned-minimal-allowlist actual=missing"
        ]
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return [], [
            f"file={path.as_posix()} identifier=allowlist-invalid-json rule=allowlist-contract "
            "expected=valid-json actual=invalid"
        ]
    errors: list[str] = []
    if payload.get("schema") != 1 or not isinstance(payload.get("entries"), list):
        errors.append(
            f"file={path.as_posix()} identifier=allowlist-schema rule=allowlist-contract "
            "expected=schema-1-with-entries actual=invalid-structure"
        )
        return [], errors
    current = today or dt.date.today()
    entries: list[AllowEntry] = []
    seen: set[tuple[str, str, str]] = set()
    required = {"path", "rule", "identifier", "rationale", "owner", "expires"}
    for position, raw in enumerate(payload["entries"], start=1):
        identifier = f"allowlist-entry-{position}"
        if not isinstance(raw, dict) or set(raw) != required:
            errors.append(
                f"file={path.as_posix()} identifier={identifier} rule=allowlist-contract "
                "expected=exact-required-fields actual=invalid-fields"
            )
            continue
        entry = AllowEntry(**raw)
        if (
            not entry.path
            or entry.path.startswith("/")
            or ".." in Path(entry.path).parts
            or any(char in entry.path for char in "*?[]{}")
            or entry.rule in {"", "*"}
            or any(char in entry.rule for char in "*?[]{}")
        ):
            errors.append(
                f"file={path.as_posix()} identifier={identifier} rule=overly-broad-allowlist "
                "expected=exact-path-and-rule actual=wildcard-or-noncanonical"
            )
        if not re.fullmatch(r"finding-[0-9a-f]{16}", entry.identifier):
            errors.append(
                f"file={path.as_posix()} identifier={identifier} rule=allowlist-contract "
                "expected=safe-finding-identifier actual=invalid-identifier"
            )
        if len(entry.rationale.strip()) < 12 or not entry.owner.strip():
            errors.append(
                f"file={path.as_posix()} identifier={identifier} rule=allowlist-rationale "
                "expected=named-owner-and-rationale actual=missing-or-empty"
            )
        try:
            expiry = dt.date.fromisoformat(entry.expires)
        except ValueError:
            errors.append(
                f"file={path.as_posix()} identifier={identifier} rule=allowlist-expiry "
                "expected=iso-date actual=invalid-date"
            )
        else:
            if expiry < current:
                errors.append(
                    f"file={path.as_posix()} identifier={identifier} rule=allowlist-expiry "
                    "expected=not-expired actual=expired"
                )
        if entry.key in seen:
            errors.append(
                f"file={path.as_posix()} identifier={identifier} rule=allowlist-contract "
                "expected=unique-entry actual=duplicate"
            )
        seen.add(entry.key)
        entries.append(entry)
    return entries, errors


def apply_allowlist(
    findings: Sequence[Finding],
    entries: Sequence[AllowEntry],
    allowlist_path: Path,
) -> tuple[list[Finding], list[str]]:
    allowed = {entry.key for entry in entries}
    matched: set[tuple[str, str, str]] = set()
    remaining: list[Finding] = []
    for finding in findings:
        key = (finding.path, finding.rule, finding.identifier)
        if key in allowed:
            matched.add(key)
        else:
            remaining.append(finding)
    errors = [
        f"file={allowlist_path.as_posix()} identifier={identifier} "
        "rule=stale-allowlist-entry expected=matching-current-finding actual=unmatched"
        for _, _, identifier in sorted(allowed - matched)
    ]
    return remaining, errors


def validate_demo_bootstrap_sources(sources: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    required_by_file = {
        "policy": (
            "EOD_DEMO_USER_PASSWORD",
            "COMPROMISED_DEMO_PASSWORD_SHA256",
            "set_unusable_password",
            "set_password",
        ),
        "command": ("CommandError", "reconcile_demo_access"),
        "signals": ("post_migrate", "reconcile_demo_access"),
    }
    for role, markers in required_by_file.items():
        text = sources.get(role, "")
        for marker in markers:
            if marker not in text:
                safe_id = hashlib.sha256((role + marker).encode()).hexdigest()[:12]
                errors.append(
                    f"file={role} identifier=bootstrap-{safe_id} rule=missing-mandatory-injection "
                    f"expected=marker-present actual=missing-{marker.lower()}"
                )
    combined = "\n".join(sources.values())
    if re.search(r"(?m)^\s*DEMO_PASSWORD\s*=\s*[\"'][^\"']+[\"']", combined):
        errors.append(
            "file=demo-bootstrap identifier=bootstrap-static-password "
            "rule=reusable-demo-credential expected=runtime-only-injection "
            "actual=tracked-password-constant"
        )
    if re.search(r"stdout\.write\([^\n]*(?:PASSWORD|password)", combined):
        errors.append(
            "file=demo-bootstrap identifier=bootstrap-password-output rule=credential-output "
            "expected=no-secret-output actual=password-written-to-command-output"
        )
    return errors


def redact_text(text: str, explicit_values: Iterable[str] = ()) -> str:
    redacted = text
    values = sorted(
        {value for value in explicit_values if len(value) >= 4},
        key=len,
        reverse=True,
    )
    for value in values:
        redacted = redacted.replace(value, "[REDACTED]")
    redacted = PRIVATE_KEY_BLOCK.sub("[REDACTED PRIVATE KEY BLOCK]", redacted)
    redacted = PRIVATE_KEY_MARKER.sub("[REDACTED PRIVATE KEY MARKER]", redacted)
    redacted = SECRET_DSN.sub(
        lambda match: match.group(0).replace(match.group("value"), "[REDACTED]"),
        redacted,
    )
    for _, pattern in TOKEN_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    output_lines: list[str] = []
    for line in redacted.splitlines(keepends=True):
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        assignment = ASSIGNMENT.match(body)
        if assignment and is_sensitive_name(assignment.group("name")):
            literal = _literal_string(assignment.group("value"))
            if literal and not is_safe_placeholder(assignment.group("value")):
                body = body[: assignment.start("value")] + "[REDACTED]"
        output_lines.append(body + ending)
    return "".join(output_lines)


def verify_sanitized_text(
    path: str,
    text: str,
    explicit_values: Iterable[str] = (),
) -> list[Finding]:
    findings = scan_text(path, text, enforce_workflow_contract=False)
    for value in {item for item in explicit_values if len(item) >= 4}:
        if value in text:
            findings.append(
                _finding(
                    path,
                    0,
                    "known-injected-secret",
                    "dynamic-secret-remains-after-redaction",
                    value,
                )
            )
    unique = {(item.path, item.line, item.rule, item.identifier): item for item in findings}
    return sorted(unique.values(), key=lambda item: (item.path, item.line, item.rule, item.identifier))


def _history_lines(root: Path, max_commits: int) -> tuple[int, list[tuple[str, int, str]]]:
    revs = subprocess.run(
        ["git", "-C", str(root), "rev-list", f"--max-count={max_commits}", "HEAD"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
    ).stdout.splitlines()
    if not revs:
        return 0, []
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
    rows: list[tuple[str, int, str]] = []
    for raw in completed.stdout.splitlines():
        try:
            _, path, line_raw, line_text = raw.split(":", 3)
            line_number = int(line_raw)
        except (ValueError, IndexError):
            continue
        rows.append((path, line_number, line_text))
    return len(revs), rows


def classify_history_fragment(path: str, line_number: int, text: str) -> list[Finding]:
    return [
        Finding(path, line_number, item.rule, item.actual_class, item.value)
        for item in scan_text(path, text, enforce_workflow_contract=False)
    ]


def history_inventory(root: Path, max_commits: int) -> dict[str, object]:
    commit_count, rows = _history_lines(root, max_commits)
    unique: dict[tuple[str, int, str, str], Finding] = {}
    for path, line_number, line_text in rows:
        for item in classify_history_fragment(path, line_number, line_text):
            unique[(path, line_number, item.rule, item.value_hash)] = item
    counts = collections.Counter(item.rule for item in unique.values())
    return {
        "schema": 2,
        "commit_depth": commit_count,
        "unique_findings": len(unique),
        "counts_by_rule": dict(sorted(counts.items())),
        "identifiers": sorted(item.identifier for item in unique.values()),
    }


def clean_tree_residue(root: Path) -> list[tuple[str, str]]:
    completed = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain=v1", "-z", "--untracked-files=all"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    residue: list[tuple[str, str]] = []
    for raw in completed.stdout.split(b"\0"):
        if not raw:
            continue
        decoded = raw.decode("utf-8", errors="replace")
        status = decoded[:2]
        path = decoded[3:] if len(decoded) >= 4 else "unknown"
        residue.append((status, path))
    return residue


def _command_scan(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    allowlist_path = root / args.allowlist
    findings = scan_repository(root)
    entries, errors = load_allowlist(allowlist_path)
    findings, allow_errors = apply_allowlist(findings, entries, allowlist_path)
    errors.extend(allow_errors)
    for finding in findings:
        print(finding.diagnostic())
    for error in errors:
        print(error)
    if findings or errors:
        print(
            f"SECRET_HYGIENE=FAIL findings={len(findings)} contract_errors={len(errors)}",
            file=sys.stderr,
        )
        return 1
    print(
        f"SECRET_HYGIENE=PASS scanned_files={len(_tracked_paths(root))} "
        f"allowlist_entries={len(entries)}"
    )
    return 0


def _command_scan_python_keywords(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    findings: list[Finding] = []
    for file_path in _tracked_paths(root):
        if file_path.suffix.casefold() != ".py":
            continue
        relative = file_path.relative_to(root).as_posix()
        text = _read_text(file_path)
        if text is not None:
            findings.extend(scan_python_keyword_literals(relative, text))
    for finding in findings:
        print(finding.diagnostic())
    if findings:
        print(f"SECRET_KEYWORD_HYGIENE=FAIL findings={len(findings)}", file=sys.stderr)
        return 1
    print("SECRET_KEYWORD_HYGIENE=PASS")
    return 0


def _command_validate_bootstrap(args: argparse.Namespace) -> int:
    sources = {
        "policy": Path(args.policy).read_text(encoding="utf-8"),
        "command": Path(args.command).read_text(encoding="utf-8"),
        "signals": Path(args.signals).read_text(encoding="utf-8"),
    }
    errors = validate_demo_bootstrap_sources(sources)
    for error in errors:
        print(error)
    return 1 if errors else 0


def _command_history(args: argparse.Namespace) -> int:
    report = history_inventory(Path(args.root).resolve(), args.max_commits)
    output = json.dumps(report, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if args.output:
        Path(args.output).write_text(output + "\n", encoding="utf-8")
    counts = ",".join(
        f"{key}:{value}" for key, value in report["counts_by_rule"].items()
    ) or "none"
    print(
        f"HISTORY_SECRET_INVENTORY commits={report['commit_depth']} "
        f"unique_findings={report['unique_findings']} counts={counts}"
    )
    return 0


def _command_redact(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    output_path = Path(args.output)
    explicit_values = [os.environ.get(name, "") for name in args.env]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        redact_text(
            input_path.read_text(encoding="utf-8", errors="replace"),
            explicit_values,
        ),
        encoding="utf-8",
    )
    return 0


def _command_verify_sanitized(args: argparse.Namespace) -> int:
    input_path = Path(args.input)
    explicit_values = [os.environ.get(name, "") for name in args.env]
    findings = verify_sanitized_text(
        input_path.name,
        input_path.read_text(encoding="utf-8", errors="replace"),
        explicit_values,
    )
    for finding in findings:
        print(finding.diagnostic())
    if findings:
        print(f"SANITIZED_OUTPUT=FAIL findings={len(findings)}", file=sys.stderr)
        return 1
    print(f"SANITIZED_OUTPUT=PASS file={input_path.name}")
    return 0


def _command_verify_clean_tree(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    diff_check = subprocess.run(
        ["git", "-C", str(root), "diff", "--check"],
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        errors="replace",
    )
    residue = clean_tree_residue(root)
    if diff_check.returncode != 0:
        print(
            "file=. identifier=clean-tree-diff-check rule=clean-tree-residue "
            "expected=no-whitespace-errors actual=git-diff-check-failed"
        )
    for status, path in residue:
        safe_id = hashlib.sha256(f"{status}\0{path}".encode()).hexdigest()[:16]
        print(
            f"file={path} identifier=residue-{safe_id} rule=clean-tree-residue "
            f"expected=empty-git-status actual=status-{status.strip() or 'unknown'}"
        )
    if diff_check.returncode != 0 or residue:
        print(
            f"CLEAN_TREE=FAIL residue={len(residue)} diff_check={diff_check.returncode}",
            file=sys.stderr,
        )
        return 1
    print("CLEAN_TREE=PASS porcelain_entries=0")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Canonical fail-closed EOD secret-hygiene engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan")
    scan.add_argument("--root", default=".")
    scan.add_argument("--allowlist", default=DEFAULT_ALLOWLIST)
    scan.set_defaults(func=_command_scan)

    keyword_scan = subparsers.add_parser("scan-python-keywords")
    keyword_scan.add_argument("--root", default=".")
    keyword_scan.set_defaults(func=_command_scan_python_keywords)

    validate = subparsers.add_parser("validate-demo-bootstrap")
    validate.add_argument("--policy", required=True)
    validate.add_argument("--command", required=True)
    validate.add_argument("--signals", required=True)
    validate.set_defaults(func=_command_validate_bootstrap)

    history = subparsers.add_parser("history-inventory")
    history.add_argument("--root", default=".")
    history.add_argument("--max-commits", type=int, default=250)
    history.add_argument("--output")
    history.set_defaults(func=_command_history)

    redact = subparsers.add_parser("redact")
    redact.add_argument("--input", required=True)
    redact.add_argument("--output", required=True)
    redact.add_argument("--env", action="append", default=[])
    redact.set_defaults(func=_command_redact)

    verify = subparsers.add_parser("verify-sanitized")
    verify.add_argument("--input", required=True)
    verify.add_argument("--env", action="append", default=[])
    verify.set_defaults(func=_command_verify_sanitized)

    clean = subparsers.add_parser("verify-clean-tree")
    clean.add_argument("--root", default=".")
    clean.set_defaults(func=_command_verify_clean_tree)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
