#!/usr/bin/env python3
"""Fail-closed dependency, SBOM, and provenance contract for EOD.

This module is intentionally self-contained. It validates the canonical registry,
all five lock projections, repository installation/reference paths, deterministic
static evidence, SPDX 2.3 payloads, and in-toto/SLSA provenance. It also provides
artifact generators used by the exact-head evidence workflow.
"""

from __future__ import annotations

import argparse
import ast
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "supply-chain/registry.json"
INVENTORY_PATH = (
    ROOT
    / "docs/work-items/active/DEPENDENCY-PROVENANCE-001/"
    "DEPENDENCY_BUILD_INVENTORY.json"
)
LOCK_DIR = ROOT / "requirements/locks"
LOCK_PROFILES = ("tooling", "build", "runtime", "dev", "browser")
ACTION_RE = re.compile(
    r"^\s*(?:-\s*)?uses:\s*([^\s#]+)(?:\s*#\s*([^\n]+))?\s*$"
)
FROM_RE = re.compile(
    r"^\s*FROM\s+([^\s#]+)(?:\s+AS\s+[^\s#]+)?(?:\s*#\s*(.*))?\s*$",
    re.I,
)
IMAGE_LINE_RE = re.compile(r"^\s*image:\s*([^\s#]+)(?:\s*#\s*(.*))?\s*$")
DIGEST_RE = re.compile(r"@sha256:([0-9a-f]{64})$")
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
URL_RE = re.compile(r"https?://[^\s\"'<>)}]+")
LOCAL_URL_RE = re.compile(r"https?://(?:127\.0\.0\.1|localhost|testserver)(?::\d+)?", re.I)
SHELL_SUFFIXES = {".sh", ".bash"}
TASK_NAMES = {
    "makefile",
    "gnumakefile",
    "justfile",
    "taskfile.yml",
    "taskfile.yaml",
    "pom.xml",
    "build.xml",
}
PROCESS_CALLS = {
    "subprocess.run",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.Popen",
    "os.system",
    "os.popen",
}


class ContractViolation(RuntimeError):
    """One deterministic fail-closed rule violation."""

    def __init__(self, rule: str, evidence: str) -> None:
        super().__init__(f"rule={rule} evidence={evidence}")
        self.rule = rule
        self.evidence = evidence


@dataclass(frozen=True)
class LockRecord:
    name: str
    version: str
    hashes: tuple[str, ...]


@dataclass(frozen=True)
class ProcessCommand:
    path: str
    line: int
    command: str | None
    call: str


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContractViolation("machine-readable-evidence", f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ContractViolation("machine-readable-evidence", f"{path}: root-not-object")
    return value


def normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def requirement_name(value: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", value)
    if not match:
        raise ContractViolation("python-canonical-declaration", value)
    return normalized_name(match.group(1))


def parse_lock(path: Path) -> dict[str, LockRecord]:
    if not path.exists():
        raise ContractViolation("lock-profile-present", str(path))
    text = path.read_text(encoding="utf-8")
    if re.search(r"(?:generated|created|timestamp).{0,16}\d{4}-\d{2}-\d{2}", text, re.I):
        raise ContractViolation("deterministic-lock-header", str(path))
    if str(ROOT) in text or "\\Users\\" in text or "/home/runner/" in text:
        raise ContractViolation("deterministic-lock-header", f"machine-path:{path}")

    records: dict[str, LockRecord] = {}
    current = ""
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        current = f"{current} {stripped}".strip() if current else stripped
        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)(.*)$", current)
        if not match:
            raise ContractViolation("exact-lock-version", f"{path}:{current}")
        name = normalized_name(match.group(1))
        hashes = tuple(sorted(set(re.findall(r"--hash=sha256:([0-9a-f]{64})", match.group(3)))))
        if not hashes:
            raise ContractViolation("lock-integrity-hashes", f"{path}:{name}")
        if name in records:
            raise ContractViolation("exact-generated-lock", f"duplicate:{path}:{name}")
        records[name] = LockRecord(name, match.group(2), hashes)
        current = ""
    if current:
        raise ContractViolation("exact-generated-lock", f"truncated:{path}")
    if not records:
        raise ContractViolation("lock-profile-present", f"empty:{path}")
    return records


def load_locks() -> dict[str, dict[str, LockRecord]]:
    return {profile: parse_lock(LOCK_DIR / f"{profile}.txt") for profile in LOCK_PROFILES}


def direct_intent() -> dict[str, set[str]]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    runtime = {requirement_name(item) for item in project.get("dependencies", [])}
    optional = project.get("optional-dependencies", {})
    build = {requirement_name(item) for item in data["build-system"]["requires"]}
    return {
        "build": build,
        "runtime": runtime,
        "dev": runtime | {requirement_name(item) for item in optional.get("dev", [])},
        "browser": runtime | {
            requirement_name(item) for item in optional.get("browser", [])
        },
    }


def validate_registry(registry: dict[str, Any]) -> None:
    if registry.get("schema") != 1 or registry.get("contract") != "DEPENDENCY-PROVENANCE-001":
        raise ContractViolation("canonical-registry-schema", "schema-or-contract")
    python = registry.get("python", {})
    if python.get("minor") != "3.13" or python.get("platform") != "linux_x86_64":
        raise ContractViolation("platform-profile-coherence", canonical_json(python).strip())
    profiles = [item.get("name") for item in registry.get("lock_profiles", [])]
    if profiles != list(LOCK_PROFILES):
        raise ContractViolation("five-lock-profiles", repr(profiles))
    root = registry.get("generator", {}).get("bootstrap_root", {})
    distributions = root.get("distributions", [])
    invalid_distribution_digests = any(
        not re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", ""))
        for item in distributions
    )
    if not distributions or invalid_distribution_digests:
        raise ContractViolation("tooling-bootstrap-root", "distribution-digests")
    generator_image = registry.get("generator", {}).get("oci", {})
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", generator_image.get("digest", "")):
        raise ContractViolation("tooling-bootstrap-root", "generator-image-digest")
    for key, image in registry.get("external_images", {}).items():
        if not image.get("tag") or not re.fullmatch(r"sha256:[0-9a-f]{64}", image.get("digest", "")):
            raise ContractViolation("image-digest-metadata-coherence", key)
    for owner, action in registry.get("github_actions", {}).items():
        if not FULL_SHA_RE.fullmatch(action.get("sha", "")) or not action.get("version"):
            raise ContractViolation("action-version-metadata", owner)
    browser = registry.get("browser", {})
    if browser.get("package", {}).get("version") not in browser.get("image", {}).get("tag", ""):
        raise ContractViolation("browser-binary-provenance", "package-image-version")
    schema = registry.get("spdx_schema", {})
    if schema.get("version") != "2.3" or not re.fullmatch(r"[0-9a-f]{64}", schema.get("sha256", "")):
        raise ContractViolation("spdx-schema-valid", "registry-schema-identity")
    schema_path = ROOT / "supply-chain/schema/spdx-2.3.schema.json"
    if not schema_path.exists() or sha256_file(schema_path) != schema["sha256"]:
        raise ContractViolation("spdx-schema-valid", "checked-in-schema-digest")
    font = registry.get("external_assets", {}).get("onest_variable_woff2", {})
    font_path = ROOT / font.get("repository_path", "missing")
    if not font_path.exists() or sha256_file(font_path) != font.get("sha256"):
        raise ContractViolation("external-asset-integrity", "Onest")


def validate_buildx_workflow(text: str, registry: dict[str, Any]) -> None:
    create_commands = re.findall(r"docker buildx create(?:\\\n|[^\n])*", text)
    if len(create_commands) != 1:
        raise ContractViolation("buildx-oci-exporter", "builder-count")
    command = create_commands[0]
    buildkit = registry.get("external_images", {}).get("buildkit", {})
    reference = f"{buildkit.get('repository', '')}@{buildkit.get('digest', '')}"
    required = (
        "--driver docker-container",
        f"--driver-opt image={reference}",
        "--use",
        "--bootstrap",
    )
    if not all(item in command for item in required):
        raise ContractViolation("buildx-oci-exporter", "builder-contract")
    builder_match = re.search(r"--name\s+([^\s\\]+)", command)
    if builder_match is None:
        raise ContractViolation("buildx-oci-exporter", "builder-name")
    builder = builder_match.group(1)
    builds = re.findall(r"docker buildx build(?:\\\n|[^\n])*", text)
    oci_builds = [item for item in builds if "type=oci" in item]
    if len(oci_builds) != 2 or any(
        f"--builder {builder}" not in item for item in oci_builds
    ):
        raise ContractViolation("buildx-oci-exporter", "explicit-builder")
    if text.find("docker buildx create") > min(text.find(item) for item in oci_builds):
        raise ContractViolation("buildx-oci-exporter", "builder-order")


def validate_lock_intent(registry: dict[str, Any], locks: dict[str, dict[str, LockRecord]]) -> None:
    intent = direct_intent()
    for profile, names in intent.items():
        missing = sorted(names - set(locks[profile]))
        if missing:
            raise ContractViolation("declaration-lock-drift", f"{profile}:{missing}")
    if not set(locks["runtime"]).issubset(locks["dev"]):
        raise ContractViolation("profile-layering", "runtime-not-subset-dev")
    if not set(locks["runtime"]).issubset(locks["browser"]):
        raise ContractViolation("profile-layering", "runtime-not-subset-browser")
    accepted = registry.get("accepted_resolution", {})
    for profile, records in locks.items():
        for name, expected in accepted.items():
            normalized = normalized_name(name)
            if normalized in records and records[normalized].version != expected:
                raise ContractViolation(
                    "version-lock-hash-coherence",
                    f"{profile}:{normalized}:{records[normalized].version}!={expected}",
                )
    playwright = locks["browser"].get("playwright")
    expected_playwright = registry["browser"]["package"]["version"]
    if playwright is None or playwright.version != expected_playwright:
        raise ContractViolation("browser-binary-provenance", "browser-lock")


def tracked_paths() -> list[str]:
    output = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    ).stdout
    return sorted(item.decode("utf-8") for item in output.split(b"\0") if item)


def is_workflow(path: str) -> bool:
    return path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))


def is_compose(path: str) -> bool:
    name = Path(path).name.lower()
    return name.startswith(("compose", "docker-compose")) and name.endswith((".yml", ".yaml"))


def is_dockerfile(path: str) -> bool:
    name = Path(path).name
    return name == "Dockerfile" or name.startswith("Dockerfile.")


def call_name(node: ast.AST, aliases: dict[str, str]) -> str:
    if isinstance(node, ast.Name):
        return aliases.get(node.id, node.id)
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value, aliases)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def python_aliases(tree: ast.AST) -> dict[str, str]:
    aliases: dict[str, str] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for item in node.names:
                if item.name in {"os", "subprocess"}:
                    aliases[item.asname or item.name] = item.name
        elif isinstance(node, ast.ImportFrom) and node.module in {"os", "subprocess"}:
            for item in node.names:
                aliases[item.asname or item.name] = f"{node.module}.{item.name}"
    return aliases


def literal_command(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        values: list[str] = []
        for item in node.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                return None
            values.append(item.value)
        return " ".join(values)
    return None


def python_process_commands(path: Path) -> list[ProcessCommand]:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except SyntaxError as exc:
        raise ContractViolation("python-process-parser", f"{path}:{exc.lineno}") from exc
    aliases = python_aliases(tree)
    commands: list[ProcessCommand] = []
    relative = path.relative_to(ROOT).as_posix()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = call_name(node.func, aliases)
        if name not in PROCESS_CALLS:
            continue
        command = literal_command(node.args[0]) if node.args else None
        commands.append(ProcessCommand(relative, node.lineno, command, name))
    return sorted(commands, key=lambda item: (item.line, item.call))


def independently_applicable_paths(paths: Iterable[str]) -> set[str]:
    result: set[str] = set()
    operator_name = re.compile(
        r"(?:bootstrap|build|deploy|install|operator|provision|release|setup|task)",
        re.I,
    )
    for path in paths:
        suffix = Path(path).suffix.lower()
        name = Path(path).name.lower()
        if (
            is_workflow(path)
            or is_compose(path)
            or is_dockerfile(path)
            or suffix in SHELL_SUFFIXES | {".ps1"}
            or name in TASK_NAMES
            or suffix in {".mk", ".make", ".gradle", ".gradle.kts"}
        ):
            result.add(path)
            continue
        if suffix == ".py":
            file_path = ROOT / path
            if path.startswith("deploy/") or operator_name.search(name):
                result.add(path)
                continue
            if python_process_commands(file_path):
                result.add(path)
                continue
        if not suffix:
            first = (ROOT / path).read_text(encoding="utf-8", errors="replace").splitlines()[:1]
            if first and first[0].startswith("#!") and re.search(r"\b(?:ba|da|k|z)?sh\b", first[0]):
                result.add(path)
    return result


def validate_completeness() -> None:
    inventory = read_json(INVENTORY_PATH)
    actual = independently_applicable_paths(tracked_paths())
    recorded = set(
        inventory.get("contours", {})
        .get("executable_sources", {})
        .get("applicable_paths", [])
    )
    missing = sorted(actual - recorded)
    stale = sorted(recorded - actual)
    if missing or stale:
        raise ContractViolation(
            "inventory-source-completeness",
            f"missing={missing} stale={stale}",
        )
    source_digests = inventory.get("source_digests", {})
    undigested = sorted(actual - set(source_digests))
    if undigested:
        raise ContractViolation("inventory-source-completeness", f"undigested={undigested}")
    mismatched = [
        path
        for path in sorted(actual)
        if sha256_file(ROOT / path) != source_digests.get(path)
    ]
    if mismatched:
        raise ContractViolation("inventory-generated-view-exact", f"digests={mismatched}")


def command_blocks(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        start = index + 1
        parts = [lines[index].strip()]
        while parts[-1].endswith("\\") and index + 1 < len(lines):
            parts[-1] = parts[-1][:-1].rstrip()
            index += 1
            parts.append(lines[index].strip())
        blocks.append((start, " ".join(parts)))
        index += 1
    return blocks


def allowlisted_opaque(registry: dict[str, Any], command: ProcessCommand) -> bool:
    for item in registry.get("opaque_process_allowlist", []):
        if (
            item.get("path") == command.path
            and item.get("line") == command.line
            and item.get("call") == command.call
            and item.get("rationale")
        ):
            return True
    return False


def validate_one_command(path: str, line: int, command: str) -> None:
    lowered = command.lower()
    evidence = f"{path}:{line}:{command}"
    if re.search(r"\bpip(?:3)?\s+install\b|\bpython(?:3)?\s+-m\s+pip\s+install\b", lowered):
        if "--upgrade" in lowered or re.search(r"\s-u(?:\s|$)", lowered):
            raise ContractViolation("locked-runtime-install", evidence)
        if "--editable" in lowered or re.search(r"\s-e(?:\s|$)", lowered):
            raise ContractViolation("install-bypass", evidence)
        no_deps_wheel = "--no-deps" in lowered and re.search(r"\.whl(?:\s|$|\*)", lowered)
        locked = "--require-hashes" in lowered and re.search(r"requirements/locks/[a-z]+\.txt", lowered)
        if not (no_deps_wheel or locked):
            raise ContractViolation("locked-runtime-install", evidence)
        if "${{" in command or re.search(r"\$[A-Za-z_{]", command):
            raise ContractViolation("dynamic-install-expression", evidence)
    if re.search(r"\bpython(?:3)?\s+-m\s+build\b", lowered) and "--no-isolation" not in lowered:
        raise ContractViolation("locked-build-environment", evidence)
    if re.search(r"\b(?:curl|wget)\b", lowered):
        urls = URL_RE.findall(command)
        if urls and all(LOCAL_URL_RE.match(url) for url in urls):
            return
        if re.search(r"\|\s*(?:sh|bash|python|python3)\b", lowered):
            raise ContractViolation("no-pipe-to-interpreter", evidence)
        if not re.search(r"sha256|checksum|integrity", lowered):
            raise ContractViolation("external-download-integrity", evidence)


def validate_install_paths(registry: dict[str, Any]) -> None:
    applicable = independently_applicable_paths(tracked_paths())
    for path in sorted(applicable):
        file_path = ROOT / path
        if file_path.suffix.lower() == ".py":
            for item in python_process_commands(file_path):
                if item.command is None:
                    if not allowlisted_opaque(registry, item):
                        raise ContractViolation(
                            "opaque-external-process-command",
                            f"{item.path}:{item.line}:{item.call}",
                        )
                    continue
                validate_one_command(item.path, item.line, item.command)
        else:
            text = file_path.read_text(encoding="utf-8", errors="replace")
            for line, command in command_blocks(text):
                if command.strip().startswith("#"):
                    continue
                validate_one_command(path, line, command)


def registry_image_by_digest(registry: dict[str, Any]) -> dict[str, tuple[str, dict[str, str]]]:
    result: dict[str, tuple[str, dict[str, str]]] = {}
    for key, item in registry.get("external_images", {}).items():
        result[item["digest"]] = (key, item)
    return result


def validate_image_reference(reference: str, evidence: str, registry: dict[str, Any]) -> None:
    if "${{" in reference or "$" in reference:
        raise ContractViolation("dynamic-image-expression", evidence)
    match = DIGEST_RE.search(reference)
    if not match:
        raise ContractViolation("immutable-image-digest", evidence)
    digest = f"sha256:{match.group(1)}"
    owner = registry_image_by_digest(registry).get(digest)
    if owner is None:
        raise ContractViolation("single-image-owner", evidence)
    _, metadata = owner
    if not metadata.get("tag") or metadata.get("repository") not in reference:
        raise ContractViolation("image-digest-metadata-coherence", evidence)


def compose_config(path: Path) -> dict[str, Any]:
    try:
        output = subprocess.run(
            ["docker", "compose", "-f", str(path), "config", "--format", "json"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise ContractViolation("compose-structural-parse", str(path)) from exc
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise ContractViolation("compose-structural-parse", str(path)) from exc
    if not isinstance(data, dict) or not isinstance(data.get("services", {}), dict):
        raise ContractViolation("compose-structural-parse", str(path))
    return data


def validate_images(registry: dict[str, Any]) -> None:
    for path in tracked_paths():
        file_path = ROOT / path
        if is_dockerfile(path):
            for line, raw in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
                match = FROM_RE.match(raw)
                if match and match.group(1) != "scratch":
                    validate_image_reference(match.group(1), f"{path}:{line}", registry)
        elif is_compose(path):
            data = compose_config(file_path)
            for service, config in data["services"].items():
                image = config.get("image")
                has_build = bool(config.get("build"))
                if image and not has_build:
                    validate_image_reference(str(image), f"{path}:{service}", registry)
                if image and has_build and DIGEST_RE.search(str(image)):
                    raise ContractViolation("local-build-owner", f"{path}:{service}:digest-local")
        elif is_workflow(path):
            for line, raw in enumerate(file_path.read_text(encoding="utf-8").splitlines(), 1):
                match = IMAGE_LINE_RE.match(raw)
                if match:
                    validate_image_reference(match.group(1), f"{path}:{line}", registry)


def validate_actions(registry: dict[str, Any]) -> None:
    owners = registry.get("github_actions", {})
    for path in (item for item in tracked_paths() if is_workflow(item)):
        for line, raw in enumerate((ROOT / path).read_text(encoding="utf-8").splitlines(), 1):
            match = ACTION_RE.match(raw)
            if not match:
                continue
            reference, comment = match.group(1), (match.group(2) or "").strip()
            if reference.startswith("./"):
                continue
            if "${{" in reference:
                raise ContractViolation("dynamic-action-expression", f"{path}:{line}")
            if "@" not in reference:
                raise ContractViolation("immutable-action-sha", f"{path}:{line}")
            owner, revision = reference.rsplit("@", 1)
            expected = owners.get(owner)
            if expected is None:
                raise ContractViolation("single-action-owner", f"{path}:{line}:{owner}")
            if not FULL_SHA_RE.fullmatch(revision) or revision != expected["sha"]:
                raise ContractViolation("immutable-action-sha", f"{path}:{line}:{revision}")
            if comment != expected["version"]:
                raise ContractViolation("action-version-metadata", f"{path}:{line}:{comment}")


def validate_repository(root: Path = ROOT) -> dict[str, Any]:
    del root
    registry = read_json(REGISTRY_PATH)
    validate_registry(registry)
    locks = load_locks()
    validate_lock_intent(registry, locks)
    validate_actions(registry)
    validate_images(registry)
    validate_install_paths(registry)
    validate_completeness()
    return {
        "registry_sha256": sha256_file(REGISTRY_PATH),
        "lock_digests": {
            profile: sha256_file(LOCK_DIR / f"{profile}.txt")
            for profile in LOCK_PROFILES
        },
        "profiles": {
            profile: len(records) for profile, records in locks.items()
        },
        "applicable_sources": len(independently_applicable_paths(tracked_paths())),
    }


def static_category(relative: str) -> str:
    if relative.startswith("admin/"):
        return "framework-admin"
    if relative.startswith("system/fonts/"):
        return "repository-font"
    if relative.startswith("system/"):
        return "repository-system"
    return "repository-application"


def generate_static_manifest(static_root: Path, output: Path) -> dict[str, Any]:
    if not static_root.is_dir():
        raise ContractViolation("static-manifest-exact", f"missing:{static_root}")
    entries = []
    for path in sorted(item for item in static_root.rglob("*") if item.is_file()):
        relative = path.relative_to(static_root).as_posix()
        entries.append(
            {
                "path": relative,
                "size": path.stat().st_size,
                "sha256": sha256_file(path),
                "source_category": static_category(relative),
            }
        )
    payload = {
        "schema": 1,
        "root": "staticfiles",
        "entry_count": len(entries),
        "entries": entries,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(payload), encoding="utf-8")
    return payload


def verify_static_manifest(static_root: Path, manifest_path: Path) -> None:
    expected_path = manifest_path.with_suffix(manifest_path.suffix + ".expected")
    generate_static_manifest(static_root, expected_path)
    try:
        if expected_path.read_bytes() != manifest_path.read_bytes():
            raise ContractViolation("static-manifest-exact", str(manifest_path))
    finally:
        expected_path.unlink(missing_ok=True)


def epoch_timestamp(epoch: str) -> str:
    if not re.fullmatch(r"\d+", epoch):
        raise ContractViolation("spdx-created-build-epoch", epoch)
    value = dt.datetime.fromtimestamp(int(epoch), tz=dt.UTC)
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def canonical_namespace(
    image_digest: str,
    source_commit: str,
    build_definition_digest: str,
) -> str:
    identity = "\n".join(
        ["eod-spdx-namespace-v1", image_digest, source_commit, build_definition_digest]
    )
    return f"https://eod.invalid/spdx/{sha256_bytes(identity.encode('utf-8'))}"


def normalize_spdx(
    source: Path,
    output: Path,
    image_digest: str,
    source_commit: str,
    build_definition_digest: str,
    source_date_epoch: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", image_digest):
        raise ContractViolation("sbom-subject-digest", image_digest)
    if not FULL_SHA_RE.fullmatch(source_commit):
        raise ContractViolation("sbom-exact-head-chain", source_commit)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", build_definition_digest):
        raise ContractViolation("spdx-document-namespace-deterministic", build_definition_digest)
    payload = read_json(source)
    payload["spdxVersion"] = "SPDX-2.3"
    payload["dataLicense"] = "CC0-1.0"
    payload["SPDXID"] = "SPDXRef-DOCUMENT"
    payload["name"] = "electronic-operational-docs-final-image"
    payload["documentNamespace"] = canonical_namespace(
        image_digest, source_commit, build_definition_digest
    )
    creation = payload.setdefault("creationInfo", {})
    creation["created"] = epoch_timestamp(source_date_epoch)
    creators = creation.setdefault("creators", [])
    creator = "Tool: anchore/syft"
    if creator not in creators:
        creators.append(creator)
    creators.sort()

    packages = payload.setdefault("packages", [])
    packages = [item for item in packages if item.get("SPDXID") != "SPDXRef-FinalImage"]
    image_package = {
        "SPDXID": "SPDXRef-FinalImage",
        "name": "electronic-operational-docs-final-image",
        "downloadLocation": "NOASSERTION",
        "filesAnalyzed": False,
        "checksums": [
            {"algorithm": "SHA256", "checksumValue": image_digest.split(":", 1)[1]}
        ],
        "versionInfo": image_digest,
    }
    packages.append(image_package)
    packages.sort(key=lambda item: (item.get("SPDXID", ""), item.get("name", "")))
    payload["packages"] = packages
    payload["documentDescribes"] = ["SPDXRef-FinalImage"]
    relationships = payload.setdefault("relationships", [])
    known = {
        (item.get("spdxElementId"), item.get("relationshipType"), item.get("relatedSpdxElement"))
        for item in relationships
    }
    for package in packages:
        package_id = package.get("SPDXID")
        if package_id and package_id != "SPDXRef-FinalImage":
            relationship = ("SPDXRef-FinalImage", "CONTAINS", package_id)
            if relationship not in known:
                relationships.append(
                    {
                        "spdxElementId": relationship[0],
                        "relationshipType": relationship[1],
                        "relatedSpdxElement": relationship[2],
                    }
                )
    relationships.sort(
        key=lambda item: (
            item.get("spdxElementId", ""),
            item.get("relationshipType", ""),
            item.get("relatedSpdxElement", ""),
        )
    )
    payload["relationships"] = relationships
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(canonical_json(payload), encoding="utf-8")
    return payload


def validate_spdx_schema(payload: dict[str, Any]) -> None:
    try:
        import jsonschema
    except ImportError as exc:
        raise ContractViolation("spdx-schema-valid", "jsonschema-tooling-missing") from exc
    schema = read_json(ROOT / "supply-chain/schema/spdx-2.3.schema.json")
    try:
        jsonschema.validate(payload, schema)
    except jsonschema.ValidationError as exc:
        raise ContractViolation("spdx-schema-valid", exc.json_path) from exc


def pypi_components(payload: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for package in payload.get("packages", []):
        for reference in package.get("externalRefs", []):
            locator = reference.get("referenceLocator", "")
            match = re.match(r"pkg:pypi/([^@?]+)", locator)
            if match:
                result.add(normalized_name(match.group(1)))
    return result


def validate_spdx(
    payload: dict[str, Any],
    image_digest: str,
    source_commit: str,
    build_definition_digest: str,
    source_date_epoch: str,
    scope: str,
) -> None:
    creation = payload.get("creationInfo", {})
    created = creation.get("created")
    if not created:
        raise ContractViolation("spdx-creation-info-created-required", "missing")
    if not TIMESTAMP_RE.fullmatch(created):
        raise ContractViolation("spdx-created-rfc3339-utc", created)
    expected_created = epoch_timestamp(source_date_epoch)
    if created != expected_created:
        raise ContractViolation("spdx-created-build-epoch", f"{created}!={expected_created}")
    expected_namespace = canonical_namespace(image_digest, source_commit, build_definition_digest)
    if payload.get("documentNamespace") != expected_namespace:
        raise ContractViolation("spdx-document-namespace-deterministic", "namespace")
    packages = payload.get("packages", [])
    image_package = next(
        (item for item in packages if item.get("SPDXID") == "SPDXRef-FinalImage"),
        None,
    )
    if image_package is None or image_package.get("versionInfo") != image_digest:
        raise ContractViolation("sbom-subject-digest", image_digest)
    validate_spdx_schema(payload)

    components = pypi_components(payload)
    locks = load_locks()
    expected = set(locks[scope])
    missing = sorted(expected - components)
    if missing:
        raise ContractViolation("sbom-runtime-completeness", f"{scope}:{missing}")
    if scope == "runtime":
        forbidden = (set(locks["dev"]) | set(locks["browser"])) - expected
        leaked = sorted(components & forbidden)
        if leaked:
            raise ContractViolation("sbom-scope-separation", repr(leaked))
        allowed_extra = {
            "electronic-operational-docs",
            *read_json(REGISTRY_PATH).get("runtime_component_allowlist", []),
        }
        unexpected = sorted(components - expected - allowed_extra)
        if unexpected:
            raise ContractViolation("sbom-unexpected-component", repr(unexpected))


def generate_component_set(
    output: Path,
    production_sbom: Path,
    browser_sbom: Path,
    service_sboms: list[tuple[str, Path]],
) -> dict[str, Any]:
    components = [
        {
            "role": "production",
            "path": production_sbom.name,
            "sha256": sha256_file(production_sbom),
        },
        {
            "role": "browser-test",
            "path": browser_sbom.name,
            "sha256": sha256_file(browser_sbom),
        },
    ]
    for name, path in sorted(service_sboms):
        components.append(
            {
                "role": "service-image",
                "name": name,
                "path": path.name,
                "sha256": sha256_file(path),
            }
        )
    payload = {"schema": 1, "components": components}
    output.write_text(canonical_json(payload), encoding="utf-8")
    return payload


def digest_material(path: Path, uri: str | None = None) -> dict[str, Any]:
    return {
        "uri": uri or path.relative_to(ROOT).as_posix(),
        "digest": {"sha256": sha256_file(path)},
    }


def generate_provenance(
    output: Path,
    subject_name: str,
    subject_digest: str,
    wheel: Path,
    static_manifest: Path,
    spdx: Path,
    source_commit: str,
    workflow: Path,
    source_date_epoch: str,
) -> dict[str, Any]:
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", subject_digest):
        raise ContractViolation("provenance-subject-digest", subject_digest)
    if not FULL_SHA_RE.fullmatch(source_commit):
        raise ContractViolation("provenance-exact-head", source_commit)
    materials = [
        {
            "uri": f"git+https://github.com/genrudko/electronic-operational-docs@{source_commit}",
            "digest": {"sha1": source_commit},
        },
        digest_material(REGISTRY_PATH),
        digest_material(workflow),
        digest_material(ROOT / "Dockerfile"),
        digest_material(wheel, "wheel:" + wheel.name),
        digest_material(static_manifest),
        digest_material(spdx),
    ]
    for profile in LOCK_PROFILES:
        materials.append(digest_material(LOCK_DIR / f"{profile}.txt"))
    registry = read_json(REGISTRY_PATH)
    for key, image in sorted(registry.get("external_images", {}).items()):
        materials.append(
            {
                "uri": f"oci:{image['repository']}#{key}",
                "digest": {"sha256": image["digest"].split(":", 1)[1]},
            }
        )
    for owner, action in sorted(registry.get("github_actions", {}).items()):
        materials.append(
            {
                "uri": f"github-action:{owner}",
                "digest": {"gitCommit": action["sha"]},
            }
        )
    materials.sort(key=lambda item: item["uri"])
    created = epoch_timestamp(source_date_epoch)
    payload = {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": [
            {"name": subject_name, "digest": {"sha256": subject_digest.split(":", 1)[1]}}
        ],
        "predicateType": "https://slsa.dev/provenance/v1",
        "predicate": {
            "buildDefinition": {
                "buildType": "https://eod.invalid/build-types/oci-wheel/v1",
                "externalParameters": {
                    "sourceCommit": source_commit,
                    "python": registry["python"],
                    "lockProfiles": list(LOCK_PROFILES),
                },
                "internalParameters": {},
                "resolvedDependencies": materials,
            },
            "runDetails": {
                "builder": {"id": "https://github.com/genrudko/electronic-operational-docs/actions"},
                "metadata": {"startedOn": created, "finishedOn": created},
            },
        },
    }
    output.write_text(canonical_json(payload), encoding="utf-8")
    return payload


def validate_provenance(
    payload: dict[str, Any],
    subject_digest: str,
    source_commit: str,
) -> None:
    if payload.get("_type") != "https://in-toto.io/Statement/v1":
        raise ContractViolation("attestation-verification", "statement-type")
    if payload.get("predicateType") != "https://slsa.dev/provenance/v1":
        raise ContractViolation("attestation-verification", "predicate-type")
    subject = payload.get("subject", [])
    expected = subject_digest.split(":", 1)[1]
    if len(subject) != 1 or subject[0].get("digest", {}).get("sha256") != expected:
        raise ContractViolation("provenance-subject-digest", subject_digest)
    materials = payload.get("predicate", {}).get("buildDefinition", {}).get("resolvedDependencies", [])
    uris = {item.get("uri") for item in materials}
    required = {
        "supply-chain/registry.json",
        ".github/workflows/dependency-provenance.yml",
        "Dockerfile",
        *{f"requirements/locks/{profile}.txt" for profile in LOCK_PROFILES},
    }
    missing = sorted(required - uris)
    if missing:
        raise ContractViolation("provenance-material-completeness", repr(missing))
    source_uri = f"git+https://github.com/genrudko/electronic-operational-docs@{source_commit}"
    if source_uri not in uris:
        raise ContractViolation("provenance-exact-head", source_commit)


def verify_artifact_directory(directory: Path) -> dict[str, Any]:
    required = {
        "static-manifest.json",
        "production.spdx.json",
        "browser.spdx.json",
        "postgres.spdx.json",
        "component-set.json",
        "provenance.intoto.json",
        "publication-order.json",
    }
    present = {item.name for item in directory.iterdir() if item.is_file()}
    missing = sorted(required - present)
    if missing:
        raise ContractViolation("provenance-material-completeness", repr(missing))
    order = read_json(directory / "publication-order.json")
    steps = order.get("completed", [])
    try:
        secret_index = steps.index("secret-hygiene")
        publish_index = steps.index("publication-ready")
    except ValueError as exc:
        raise ContractViolation("secret-scan-before-publication", repr(steps)) from exc
    if secret_index >= publish_index:
        raise ContractViolation("secret-scan-before-publication", repr(steps))
    manifest = {
        item.name: sha256_file(item)
        for item in sorted(directory.iterdir())
        if item.is_file() and item.name != "artifact-manifest.json"
    }
    expected_path = directory / "artifact-manifest.json"
    if expected_path.exists():
        expected = read_json(expected_path).get("files", {})
        if expected != manifest:
            raise ContractViolation("verified-sanitized-artifact-only", "artifact-manifest")
    return {"files": manifest}


def build_artifact_manifest(directory: Path) -> dict[str, Any]:
    payload = verify_artifact_directory(directory)
    (directory / "artifact-manifest.json").write_text(
        canonical_json(payload), encoding="utf-8"
    )
    return payload


def parse_service(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("service must be NAME=PATH")
    name, path = value.split("=", 1)
    return name, Path(path)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("validate-repository")

    static = subparsers.add_parser("static-manifest")
    static.add_argument("--root", type=Path, required=True)
    static.add_argument("--output", type=Path, required=True)

    verify_static = subparsers.add_parser("verify-static-manifest")
    verify_static.add_argument("--root", type=Path, required=True)
    verify_static.add_argument("--manifest", type=Path, required=True)

    normalize = subparsers.add_parser("normalize-spdx")
    normalize.add_argument("--input", type=Path, required=True)
    normalize.add_argument("--output", type=Path, required=True)
    normalize.add_argument("--image-digest", required=True)
    normalize.add_argument("--source-commit", required=True)
    normalize.add_argument("--build-definition-digest", required=True)
    normalize.add_argument("--source-date-epoch", required=True)

    validate = subparsers.add_parser("validate-spdx")
    validate.add_argument("--input", type=Path, required=True)
    validate.add_argument("--image-digest", required=True)
    validate.add_argument("--source-commit", required=True)
    validate.add_argument("--build-definition-digest", required=True)
    validate.add_argument("--source-date-epoch", required=True)
    validate.add_argument("--scope", choices=("runtime", "browser"), required=True)

    component = subparsers.add_parser("component-set")
    component.add_argument("--output", type=Path, required=True)
    component.add_argument("--production", type=Path, required=True)
    component.add_argument("--browser", type=Path, required=True)
    component.add_argument("--service", action="append", type=parse_service, default=[])

    provenance = subparsers.add_parser("provenance")
    provenance.add_argument("--output", type=Path, required=True)
    provenance.add_argument("--subject-name", required=True)
    provenance.add_argument("--subject-digest", required=True)
    provenance.add_argument("--wheel", type=Path, required=True)
    provenance.add_argument("--static-manifest", type=Path, required=True)
    provenance.add_argument("--spdx", type=Path, required=True)
    provenance.add_argument("--source-commit", required=True)
    provenance.add_argument("--workflow", type=Path, required=True)
    provenance.add_argument("--source-date-epoch", required=True)

    verify_provenance = subparsers.add_parser("validate-provenance")
    verify_provenance.add_argument("--input", type=Path, required=True)
    verify_provenance.add_argument("--subject-digest", required=True)
    verify_provenance.add_argument("--source-commit", required=True)

    artifact = subparsers.add_parser("artifact-manifest")
    artifact.add_argument("--directory", type=Path, required=True)

    verify_artifact = subparsers.add_parser("verify-artifact")
    verify_artifact.add_argument("--directory", type=Path, required=True)

    args = parser.parse_args()
    try:
        if args.command == "validate-repository":
            result = validate_repository()
        elif args.command == "static-manifest":
            result = generate_static_manifest(args.root, args.output)
        elif args.command == "verify-static-manifest":
            verify_static_manifest(args.root, args.manifest)
            result = {"verified": True}
        elif args.command == "normalize-spdx":
            result = normalize_spdx(
                args.input,
                args.output,
                args.image_digest,
                args.source_commit,
                args.build_definition_digest,
                args.source_date_epoch,
            )
        elif args.command == "validate-spdx":
            payload = read_json(args.input)
            validate_spdx(
                payload,
                args.image_digest,
                args.source_commit,
                args.build_definition_digest,
                args.source_date_epoch,
                args.scope,
            )
            result = {"verified": True}
        elif args.command == "component-set":
            result = generate_component_set(
                args.output, args.production, args.browser, args.service
            )
        elif args.command == "provenance":
            result = generate_provenance(
                args.output,
                args.subject_name,
                args.subject_digest,
                args.wheel,
                args.static_manifest,
                args.spdx,
                args.source_commit,
                args.workflow,
                args.source_date_epoch,
            )
        elif args.command == "validate-provenance":
            validate_provenance(
                read_json(args.input), args.subject_digest, args.source_commit
            )
            result = {"verified": True}
        elif args.command == "artifact-manifest":
            result = build_artifact_manifest(args.directory)
        else:
            result = verify_artifact_directory(args.directory)
    except (ContractViolation, OSError, subprocess.CalledProcessError, ValueError) as exc:
        print(f"DEPENDENCY_PROVENANCE_CONTRACT=FAIL {exc}", file=sys.stderr)
        return 1
    print(
        "DEPENDENCY_PROVENANCE_CONTRACT=PASS "
        + json.dumps(result, ensure_ascii=False, sort_keys=True)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
