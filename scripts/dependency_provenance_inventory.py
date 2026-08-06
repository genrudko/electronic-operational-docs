#!/usr/bin/env python3
"""Deterministic dependency/build-input inventory for DEPENDENCY-PROVENANCE-001."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
WORK_ITEM_DIR = Path("docs/work-items/active/DEPENDENCY-PROVENANCE-001")
INVENTORY_JSON = WORK_ITEM_DIR / "DEPENDENCY_BUILD_INVENTORY.json"
INVENTORY_MD = WORK_ITEM_DIR / "DEPENDENCY_BUILD_INVENTORY.md"
SCHEMA = 1

ACTION_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)(?:\s*#\s*(.*))?\s*$")
DOCKER_FROM_RE = re.compile(
    r"^\s*FROM\s+([^\s#]+)(?:\s+(?:AS\s+[^\s#]+))?(?:\s*#\s*(.*))?\s*$",
    re.IGNORECASE,
)
IMAGE_RE = re.compile(r"^\s*image:\s*([^\s#]+)(?:\s*#\s*(.*))?\s*$")
IMMUTABLE_ACTION_RE = re.compile(r"^[^@]+@[0-9a-fA-F]{40}$")
IMMUTABLE_IMAGE_RE = re.compile(r"@sha256:[0-9a-fA-F]{64}$")
REQUIREMENT_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)(.*)$")
URL_RE = re.compile(r"https?://[^\s\"'<>)}]+")
TEMP_WORKFLOW_RE = re.compile(
    r"(?:temp|temporary|post[-_]?merge|synchroni[sz]er|coordination)", re.I
)
LOCK_NAMES = {
    "Pipfile.lock",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pdm.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "uv.lock",
    "yarn.lock",
}
PACKAGE_NAMES = {
    "package.json",
    "package-lock.json",
    "npm-shrinkwrap.json",
    "pnpm-lock.yaml",
    "yarn.lock",
}
TEXT_SUFFIXES = {
    ".bash", ".cjs", ".css", ".html", ".htm", ".js", ".json", ".md",
    ".mjs", ".py", ".sh", ".toml", ".txt", ".yaml", ".yml",
}
COMMAND_PATTERNS = (
    (
        "python-install",
        re.compile(r"\b(?:python(?:3)?\s+-m\s+pip|pip(?:3)?)\s+install\b"),
    ),
    (
        "system-package-install",
        re.compile(
            r"\b(?:apt(?:-get)?\s+install|apk\s+add|dnf\s+install|yum\s+install)\b"
        ),
    ),
    ("external-download", re.compile(r"\b(?:curl|wget)\b")),
    (
        "javascript-install",
        re.compile(
            r"\b(?:npm\s+(?:ci|install)|pnpm\s+install|yarn\s+install|npx\b)"
        ),
    ),
    ("browser-binary-install", re.compile(r"\bplaywright\s+install\b")),
)


def tracked_files(root: Path = ROOT) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=root, check=True, capture_output=True
    )
    return sorted(
        item.decode("utf-8") for item in result.stdout.split(b"\0") if item
    )


def read_text(root: Path, relative: str) -> str:
    return (root / relative).read_text(encoding="utf-8", errors="replace")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def requirement_name(value: str) -> str:
    match = REQUIREMENT_RE.match(value)
    return (
        match.group(1).lower().replace("_", "-")
        if match
        else value.lower()
    )


def requirement_constraint(value: str) -> str:
    match = REQUIREMENT_RE.match(value)
    return match.group(2).strip() if match else ""


def make_entry(
    *,
    input_class: str,
    path: str,
    line: int | None,
    purpose: str,
    scope: str,
    canonicality: str,
    directness: str,
    declaration: str,
    constraint: str,
    immutable: bool,
    hash_coverage: str,
    reproducibility: str,
    risk: str,
    owner: str,
    evidence: str,
) -> dict[str, Any]:
    return {
        "class": input_class,
        "path": path,
        "line": line,
        "purpose": purpose,
        "dependency_scope": scope,
        "canonical_or_duplicate": canonicality,
        "direct_or_transitive": directness,
        "declaration": declaration,
        "version_constraint": constraint,
        "immutable": immutable,
        "hash_coverage": hash_coverage,
        "current_reproducibility": reproducibility,
        "risk": risk,
        "proposed_owner": owner,
        "evidence": evidence,
    }


def python_entry(
    requirement: str,
    *,
    input_class: str,
    purpose: str,
    scope: str,
    owner: str,
) -> dict[str, Any]:
    return make_entry(
        input_class=input_class,
        path="pyproject.toml",
        line=None,
        purpose=purpose,
        scope=scope,
        canonicality="canonical",
        directness="direct",
        declaration=requirement,
        constraint=requirement_constraint(requirement),
        immutable=False,
        hash_coverage="absent",
        reproducibility="floating-range",
        risk="HIGH",
        owner=owner,
        evidence="Direct intent exists; exact transitive graph is not locked.",
    )


def pyproject_entries(root: Path, files: set[str]) -> list[dict[str, Any]]:
    if "pyproject.toml" not in files:
        return []
    data = tomllib.loads(read_text(root, "pyproject.toml"))
    entries: list[dict[str, Any]] = []
    python_range = data.get("project", {}).get("requires-python")
    if python_range:
        entries.append(
            make_entry(
                input_class="python-runtime",
                path="pyproject.toml",
                line=None,
                purpose="Supported interpreter range",
                scope="runtime/build/test",
                canonicality="canonical",
                directness="direct",
                declaration="python",
                constraint=str(python_range),
                immutable=False,
                hash_coverage="not-applicable",
                reproducibility="partial-range-only",
                risk="MEDIUM",
                owner="pyproject.toml [project.requires-python]",
                evidence="Parsed from canonical project metadata.",
            )
        )
    for requirement in data.get("build-system", {}).get("requires", []):
        entries.append(
            python_entry(
                requirement,
                input_class="python-build",
                purpose="PEP 517 build backend dependency",
                scope="build",
                owner="pyproject.toml [build-system.requires]",
            )
        )
    for requirement in data.get("project", {}).get("dependencies", []):
        entries.append(
            python_entry(
                requirement,
                input_class="python-runtime",
                purpose="Application runtime dependency",
                scope="runtime",
                owner="pyproject.toml [project.dependencies]",
            )
        )
    optional = data.get("project", {}).get("optional-dependencies", {})
    for group, requirements in sorted(optional.items()):
        for requirement in requirements:
            entries.append(
                python_entry(
                    requirement,
                    input_class="python-optional",
                    purpose=f"Optional dependency group: {group}",
                    scope=group,
                    owner=(
                        "pyproject.toml "
                        f"[project.optional-dependencies.{group}]"
                    ),
                )
            )
    entries.append(
        make_entry(
            input_class="python-transitive",
            path="pyproject.toml",
            line=None,
            purpose="Resolved transitive dependency graph",
            scope="runtime/dev/browser/build",
            canonicality="missing-canonical-lock",
            directness="transitive",
            declaration="pip dynamic resolver output",
            constraint="derived from ranges and package-index state",
            immutable=False,
            hash_coverage="absent",
            reproducibility="not-reproducible",
            risk="CRITICAL",
            owner="proposed generated hashed lock profiles",
            evidence=(
                "No accepted transitive lock with integrity hashes is tracked."
            ),
        )
    )
    return entries


def is_dockerfile(path: str) -> bool:
    name = Path(path).name
    return name == "Dockerfile" or name.startswith("Dockerfile.")


def is_compose(path: str) -> bool:
    name = Path(path).name.lower()
    return name.startswith(("compose", "docker-compose")) and path.endswith(
        (".yaml", ".yml")
    )


def match_comment(match: re.Match[str]) -> str:
    return (match.group(2) or "Parsed tracked reference.").strip()


def scan_images(root: Path, files: list[str]) -> list[dict[str, Any]]:
    candidates = [
        path
        for path in files
        if is_dockerfile(path)
        or is_compose(path)
        or path.startswith(".github/workflows/")
    ]
    texts = {path: read_text(root, path) for path in candidates}
    entries: list[dict[str, Any]] = []
    for path in candidates:
        for line_number, raw in enumerate(texts[path].splitlines(), start=1):
            match = (
                DOCKER_FROM_RE.match(raw)
                if is_dockerfile(path)
                else IMAGE_RE.match(raw)
            )
            if not match:
                continue
            reference = match.group(1)
            immutable = reference == "scratch" or bool(
                IMMUTABLE_IMAGE_RE.search(reference)
            )
            occurrences = sum(reference in text for text in texts.values())
            entries.append(
                make_entry(
                    input_class="container-image",
                    path=path,
                    line=line_number,
                    purpose="Container base, service, test or local image input/output",
                    scope=(
                        "build"
                        if is_dockerfile(path)
                        else "ci"
                        if path.startswith(".github/")
                        else "runtime/test"
                    ),
                    canonicality=(
                        "duplicate-reference"
                        if occurrences > 1
                        else "canonical-reference"
                    ),
                    directness="direct",
                    declaration=reference,
                    constraint=reference.split("@", 1)[0],
                    immutable=immutable,
                    hash_coverage="sha256-digest" if immutable else "absent",
                    reproducibility="immutable" if immutable else "mutable-tag",
                    risk="LOW" if immutable else "HIGH",
                    owner="canonical container-image registry/reference contract",
                    evidence=match_comment(match),
                )
            )
    return entries


def scan_actions(root: Path, files: list[str]) -> list[dict[str, Any]]:
    workflows = [
        path
        for path in files
        if path.startswith(".github/workflows/")
        and path.endswith((".yaml", ".yml"))
    ]
    entries: list[dict[str, Any]] = []
    for path in workflows:
        for line_number, raw in enumerate(
            read_text(root, path).splitlines(), start=1
        ):
            match = ACTION_RE.match(raw)
            if not match:
                continue
            reference = match.group(1)
            local = reference.startswith("./")
            immutable = local or bool(IMMUTABLE_ACTION_RE.match(reference))
            entries.append(
                make_entry(
                    input_class="github-action",
                    path=path,
                    line=line_number,
                    purpose="GitHub Actions executable dependency",
                    scope="ci/deployment",
                    canonicality="reference",
                    directness="direct",
                    declaration=reference,
                    constraint=(
                        reference.rsplit("@", 1)[-1]
                        if "@" in reference
                        else "local"
                    ),
                    immutable=immutable,
                    hash_coverage=(
                        "repository-exact-head"
                        if local
                        else "commit-sha"
                        if immutable
                        else "absent"
                    ),
                    reproducibility=(
                        "exact-head-local"
                        if local
                        else "immutable"
                        if immutable
                        else "mutable-tag-or-branch"
                    ),
                    risk="LOW" if immutable else "HIGH",
                    owner="each validated .github/workflows uses reference",
                    evidence=(
                        match.group(2) or "No readable version comment."
                    ).strip(),
                )
            )
    return entries


def executable_source(path: str) -> bool:
    if path == "scripts/dependency_provenance_inventory.py":
        return False
    return (
        is_dockerfile(path)
        or is_compose(path)
        or path.startswith(".github/workflows/")
        or (
            path.startswith("scripts/")
            and Path(path).suffix in {".bash", ".py", ".sh"}
        )
    )


def scan_operations(root: Path, files: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in (item for item in files if executable_source(item)):
        for line_number, raw in enumerate(
            read_text(root, path).splitlines(), start=1
        ):
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for input_class, pattern in COMMAND_PATTERNS:
                if not pattern.search(stripped):
                    continue
                integrity = bool(
                    re.search(
                        r"(?:sha256|checksum|integrity|--require-hashes)",
                        stripped,
                        re.I,
                    )
                )
                high_risk = input_class in {
                    "browser-binary-install",
                    "external-download",
                    "system-package-install",
                }
                entries.append(
                    make_entry(
                        input_class=input_class,
                        path=path,
                        line=line_number,
                        purpose="Build, test or deployment input operation",
                        scope="ci/build/runtime tooling",
                        canonicality="operational-declaration",
                        directness="direct",
                        declaration=stripped,
                        constraint="embedded in command or absent",
                        immutable=integrity,
                        hash_coverage=(
                            "inline-or-associated-evidence"
                            if integrity
                            else "absent"
                        ),
                        reproducibility=(
                            "integrity-evidenced" if integrity else "not-proven"
                        ),
                        risk="HIGH" if high_risk and not integrity else "MEDIUM",
                        owner="canonical lock/download/image contract",
                        evidence="Parsed from tracked executable source.",
                    )
                )
                break
    return entries


def scan_external_assets(root: Path, files: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in files:
        normalized = path.replace("\\", "/")
        asset_source = (
            "/templates/" in f"/{normalized}"
            or "/static/" in f"/{normalized}"
            or normalized.startswith("static/")
        )
        if not asset_source or Path(path).suffix.lower() not in TEXT_SUFFIXES:
            continue
        for line_number, raw in enumerate(
            read_text(root, path).splitlines(), start=1
        ):
            for url in URL_RE.findall(raw):
                if url.startswith(
                    ("http://127.0.0.1", "http://localhost", "https://localhost")
                ):
                    continue
                integrity = "integrity=" in raw or "sha256" in raw.lower()
                entries.append(
                    make_entry(
                        input_class="external-asset",
                        path=path,
                        line=line_number,
                        purpose="External browser/static runtime input",
                        scope="browser/runtime",
                        canonicality="external-reference",
                        directness="direct",
                        declaration=url,
                        constraint="URL content state",
                        immutable=False,
                        hash_coverage="present" if integrity else "absent",
                        reproducibility=(
                            "integrity-evidenced"
                            if integrity
                            else "mutable-external-content"
                        ),
                        risk="MEDIUM" if integrity else "HIGH",
                        owner=(
                            "repository-managed asset or integrity-pinned registry"
                        ),
                        evidence="Parsed from tracked template/static source.",
                    )
                )
    return entries


def duplicate_owner_groups(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in entries:
        if (
            item["class"].startswith("python-")
            and item["direct_or_transitive"] == "direct"
        ):
            key = ("python", requirement_name(item["declaration"]))
        elif item["class"] == "container-image":
            key = ("image", item["declaration"].split("@", 1)[0])
        elif item["class"] == "github-action":
            key = ("action", item["declaration"].split("@", 1)[0])
        else:
            continue
        groups[key].append(item)
    result: list[dict[str, Any]] = []
    for (input_class, name), values in sorted(groups.items()):
        if len(values) < 2:
            continue
        result.append(
            {
                "class": input_class,
                "name": name,
                "occurrences": len(values),
                "paths": sorted({value["path"] for value in values}),
                "declarations": sorted(
                    {value["declaration"] for value in values}
                ),
            }
        )
    return result


def contour_summary(
    root: Path,
    files: list[str],
    entries: list[dict[str, Any]],
) -> dict[str, Any]:
    tracked = set(files)
    requirements = sorted(
        path
        for path in files
        if Path(path).name.lower().startswith("requirements")
        and Path(path).suffix in {".in", ".txt"}
    )
    locks = sorted(
        path
        for path in files
        if Path(path).name in LOCK_NAMES
        or Path(path).name.endswith((".lock", ".lock.json"))
    )
    packages = sorted(path for path in files if Path(path).name in PACKAGE_NAMES)
    workflows = sorted(
        path
        for path in files
        if path.startswith(".github/workflows/")
        and path.endswith((".yaml", ".yml"))
    )
    browser_operations = [
        item for item in entries if item["class"] == "browser-binary-install"
    ]
    static_files = [
        path
        for path in files
        if "/static/" in f"/{path}" or path.startswith("static/")
    ]
    return {
        "python": {
            "pyproject_present": "pyproject.toml" in tracked,
            "requirements_files": requirements,
            "lock_files": locks,
            "integrity_hashed_lock_present": any(
                "--hash=sha256:" in read_text(root, path)
                for path in requirements
            ),
        },
        "javascript": {
            "package_or_lock_files": packages,
            "separate_frontend_dependency_contour": bool(packages),
        },
        "browser": {
            "python_playwright_declared": any(
                item["dependency_scope"] == "browser" for item in entries
            ),
            "browser_binary_install_operations": [
                f"{item['path']}:{item['line']}" for item in browser_operations
            ],
            "binary_integrity_contract_present": any(
                item["immutable"] for item in browser_operations
            ),
        },
        "containers": {
            "dockerfiles": sorted(path for path in files if is_dockerfile(path)),
            "compose_files": sorted(path for path in files if is_compose(path)),
        },
        "github_actions": {
            "workflow_files": workflows,
            "temporary_workflow_files": [
                path
                for path in workflows
                if TEMP_WORKFLOW_RE.search(Path(path).name)
            ],
        },
        "assets": {
            "tracked_static_file_count": len(static_files),
            "external_asset_reference_count": sum(
                item["class"] == "external-asset" for item in entries
            ),
        },
    }


def build_inventory(root: Path = ROOT) -> dict[str, Any]:
    files = tracked_files(root)
    entries: list[dict[str, Any]] = []
    entries.extend(pyproject_entries(root, set(files)))
    entries.extend(scan_images(root, files))
    entries.extend(scan_actions(root, files))
    entries.extend(scan_operations(root, files))
    entries.extend(scan_external_assets(root, files))
    entries.sort(
        key=lambda item: (
            item["class"], item["path"], item["line"] or 0, item["declaration"]
        )
    )
    for ordinal, item in enumerate(entries, start=1):
        item["id"] = f"INP-{ordinal:04d}"
        item["ordinal"] = ordinal
    floating = [
        item["id"]
        for item in entries
        if not item["immutable"]
        and (
            item["hash_coverage"] == "absent"
            or item["class"]
            in {
                "container-image",
                "external-asset",
                "github-action",
                "python-transitive",
            }
        )
    ]
    immutable = [item["id"] for item in entries if item["immutable"]]
    duplicates = duplicate_owner_groups(entries)
    contours = contour_summary(root, files, entries)
    source_paths = sorted({item["path"] for item in entries})
    return {
        "schema": SCHEMA,
        "work_item": "DEPENDENCY-PROVENANCE-001",
        "generation": {
            "method": "repository tracked-file scan",
            "tool": "scripts/dependency_provenance_inventory.py",
            "deterministic": True,
            "volatile_fields_excluded": [
                "network-resolved latest versions", "runner", "timestamp"
            ],
        },
        "accepted_boundary": {
            "source": "exact repository commit",
            "python": "direct intent plus future resolved hashed transitive lock",
            "container": "final OCI image plus OS and Python packages",
            "assets": "tracked/generated static assets copied into final image",
            "ci_artifacts": "verified artifacts only after secret-hygiene gate",
            "deployment_carrier": "immutable artifact digest linked to exact head",
        },
        "totals": {
            "tracked_files": len(files),
            "inventory_entries": len(entries),
            "by_class": dict(
                sorted(Counter(item["class"] for item in entries).items())
            ),
            "floating_inputs": len(floating),
            "immutable_inputs": len(immutable),
            "duplicate_owner_groups": len(duplicates),
            "source_files": len(source_paths),
        },
        "contours": contours,
        "floating_input_ids": floating,
        "immutable_input_ids": immutable,
        "duplicate_owner_groups": duplicates,
        "source_digests": {
            path: sha256_text(read_text(root, path)) for path in source_paths
        },
        "entries": entries,
        "limitations": [
            "Network registries are not queried; future tag movement is outside repository evidence.",
            "No accepted transitive Python lock exists; clean resolution is not reproducible.",
            "Hosted-runner software and Docker/BuildKit versions remain external inputs.",
            "SBOM and provenance are specified but not emitted in this inventory-only stage.",
            "An SBOM is an inventory and does not prove absence of vulnerabilities.",
        ],
    }


def render_json(inventory: dict[str, Any]) -> str:
    return json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    contours = inventory["contours"]
    lines = [
        "# Dependency/build inventory",
        "",
        "> GENERATED VIEW из `scripts/dependency_provenance_inventory.py`. Ручное изменение отклоняется побайтной проверкой.",
        "",
        "## Итог",
        "",
        f"- tracked files: `{totals['tracked_files']}`;",
        f"- inventory entries: `{totals['inventory_entries']}`;",
        f"- floating inputs: `{totals['floating_inputs']}`;",
        f"- immutable inputs: `{totals['immutable_inputs']}`;",
        f"- duplicate owner groups: `{totals['duplicate_owner_groups']}`;",
        f"- source files with dependency/build evidence: `{totals['source_files']}`.",
        "",
        "## Контуры",
        "",
        f"- Python: pyproject=`{contours['python']['pyproject_present']}`, requirements={contours['python']['requirements_files'] or 'NONE'}, locks={contours['python']['lock_files'] or 'NONE'}, hashed lock=`{contours['python']['integrity_hashed_lock_present']}`.",
        f"- JavaScript: package/lock files={contours['javascript']['package_or_lock_files'] or 'NONE'}; separate frontend contour=`{contours['javascript']['separate_frontend_dependency_contour']}`.",
        f"- Browser: Playwright declared=`{contours['browser']['python_playwright_declared']}`; binary install operations={contours['browser']['browser_binary_install_operations'] or 'NONE'}; integrity contract=`{contours['browser']['binary_integrity_contract_present']}`.",
        f"- Containers: Dockerfiles={contours['containers']['dockerfiles']}; Compose={contours['containers']['compose_files']}.",
        f"- GitHub Actions: workflows=`{len(contours['github_actions']['workflow_files'])}`; temporary={contours['github_actions']['temporary_workflow_files'] or 'NONE'}.",
        f"- Static assets: tracked=`{contours['assets']['tracked_static_file_count']}`; external references=`{contours['assets']['external_asset_reference_count']}`.",
        "",
        "## Totals by class",
        "",
        "| Class | Count |",
        "|---|---:|",
    ]
    for input_class, count in totals["by_class"].items():
        lines.append(f"| `{input_class}` | {count} |")
    lines.extend(
        [
            "",
            "## Inputs",
            "",
            "| ID | Class | Path:line | Scope | Declaration | Immutable | Hash | Reproducibility | Risk | Proposed owner |",
            "|---|---|---|---|---|---:|---|---|---|---|",
        ]
    )
    for item in inventory["entries"]:
        location = item["path"] + (
            f":{item['line']}" if item["line"] else ""
        )
        cells = [
            f"`{md_cell(item['id'])}`",
            f"`{md_cell(item['class'])}`",
            f"`{md_cell(location)}`",
            md_cell(item["dependency_scope"]),
            f"`{md_cell(item['declaration'])}`",
            "yes" if item["immutable"] else "no",
            md_cell(item["hash_coverage"]),
            md_cell(item["current_reproducibility"]),
            md_cell(item["risk"]),
            md_cell(item["proposed_owner"]),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(["", "## Duplicate owner groups", ""])
    if inventory["duplicate_owner_groups"]:
        for group in inventory["duplicate_owner_groups"]:
            lines.append(
                f"- `{group['class']}:{group['name']}` — {group['occurrences']} references in {', '.join(group['paths'])}."
            )
    else:
        lines.append("- NONE.")
    lines.extend(["", "## Ограничения", ""])
    lines.extend(f"- {item}" for item in inventory["limitations"])
    return "\n".join(lines).rstrip() + "\n"


def validation_errors(root: Path = ROOT) -> list[str]:
    inventory = build_inventory(root)
    errors: list[str] = []
    temporary = inventory["contours"]["github_actions"][
        "temporary_workflow_files"
    ]
    if temporary:
        errors.append(
            ".github/workflows: rule=temporary-workflow-absent; "
            f"expected=[]; actual={temporary!r}"
        )
    expected = (
        (INVENTORY_JSON, render_json(inventory)),
        (INVENTORY_MD, render_markdown(inventory)),
    )
    for relative, expected_content in expected:
        path = root / relative
        if not path.is_file():
            errors.append(
                f"{relative}: rule=inventory-generated-view-present; "
                "expected='tracked exact view'; actual='missing'"
            )
            continue
        actual_content = path.read_text(encoding="utf-8")
        if actual_content != expected_content:
            errors.append(
                f"{relative}: rule=inventory-generated-view-exact; "
                f"expected_sha256='{sha256_text(expected_content)}'; "
                f"actual_sha256='{sha256_text(actual_content)}'"
            )
    return errors


def write_views(root: Path = ROOT) -> None:
    inventory = build_inventory(root)
    for relative, content in (
        (INVENTORY_JSON, render_json(inventory)),
        (INVENTORY_MD, render_markdown(inventory)),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("check", "summary", "write"),
        nargs="?",
        default="check",
    )
    args = parser.parse_args()
    if args.command == "write":
        write_views(ROOT)
        print(f"WROTE {INVENTORY_JSON} and {INVENTORY_MD}")
        return 0
    inventory = build_inventory(ROOT)
    if args.command == "summary":
        print(json.dumps(inventory["totals"], ensure_ascii=False, sort_keys=True))
        return 0
    errors = validation_errors(ROOT)
    if errors:
        print("Dependency provenance inventory: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print(
            "Run: python scripts/dependency_provenance_inventory.py write",
            file=sys.stderr,
        )
        return 1
    print("Dependency provenance inventory: OK")
    print(json.dumps(inventory["totals"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
