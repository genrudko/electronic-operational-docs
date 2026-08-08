"""Repository-wide dependency/build-input discovery and classification."""

from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import tomllib
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA = 2
ACTION_RE = re.compile(r"^\s*-?\s*uses:\s*([^\s#]+)(?:\s*#\s*(.*))?\s*$")
FROM_RE = re.compile(
    r"^\s*FROM\s+([^\s#]+)(?:\s+(?:AS\s+[^\s#]+))?"
    r"(?:\s*#\s*(.*))?\s*$",
    re.I,
)
IMAGE_RE = re.compile(r"^\s*image:\s*([^\s#]+)(?:\s*#\s*(.*))?\s*$")
ACTION_SHA_RE = re.compile(r"^[^@]+@[0-9a-fA-F]{40}$")
IMAGE_DIGEST_RE = re.compile(r"@sha256:[0-9a-fA-F]{64}$")
ASSET_REV_RE = re.compile(r"@[0-9a-fA-F]{40}(?:/|$)")
REQ_RE = re.compile(r"^\s*([A-Za-z0-9_.-]+)(.*)$")
URL_RE = re.compile(r"https?://[^\s\"'<>)}]+")
TEMP_WORKFLOW_RE = re.compile(
    r"(?:temp|temporary|post[-_]?merge|synchroni[sz]er|coordination)", re.I
)
LOCAL_ENDPOINT_RE = re.compile(
    r"(?:127\.0\.0\.1|localhost|testserver|"
    r"\$\{(?:PREVIEW|DEVELOPMENT)_PORT\})",
    re.I,
)
OPERATOR_NAME_RE = re.compile(
    r"(?:bootstrap|build|deploy|install|operator|provision|release|setup|task)",
    re.I,
)
SHELL_SHEBANG_RE = re.compile(r"^#!.*\b(?:ba|da|k|z)?sh\b")
PYTHON_SHEBANG_RE = re.compile(r"^#!.*\bpython(?:3(?:\.\d+)?)?\b")
DOWNLOAD_COMMAND_RE = re.compile(
    r"(?:^|(?:run:|RUN|&&|\|\||;|then|do)\s+)"
    r"(?:sudo\s+)?(?:[A-Za-z0-9_./-]+/)?(?:curl|wget)\b",
    re.I,
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
TASK_NAMES = {
    "build.xml",
    "gnumakefile",
    "justfile",
    "makefile",
    "pom.xml",
    "taskfile.yaml",
    "taskfile.yml",
}
TASK_SUFFIXES = (".gradle", ".gradle.kts", ".make", ".mk")
SHELL_SUFFIXES = {".bash", ".sh"}
ASSET_SUFFIXES = {".cjs", ".css", ".html", ".htm", ".js", ".mjs"}
DIRECT_PYTHON_CLASSES = {"python-build", "python-optional", "python-runtime"}
PYTHON_EXECUTION_CALLS = {
    "os.popen",
    "os.system",
    "subprocess.Popen",
    "subprocess.call",
    "subprocess.check_call",
    "subprocess.check_output",
    "subprocess.run",
}
COMMAND_PATTERNS = (
    (
        "python-install",
        re.compile(r"\b(?:python(?:3)?\s+-m\s+pip|pip(?:3)?)\s+install\b"),
    ),
    (
        "system-package-install",
        re.compile(
            r"\b(?:apt(?:-get)?\s+install|apk\s+add|dnf\s+install|"
            r"yum\s+install)\b"
        ),
    ),
    ("external-download", DOWNLOAD_COMMAND_RE),
    (
        "javascript-install",
        re.compile(
            r"\b(?:npm\s+(?:ci|install)|pnpm\s+install|"
            r"yarn\s+install|npx\b)"
        ),
    ),
    ("browser-binary-install", re.compile(r"\bplaywright\s+install\b")),
)
# Registry entries require a separately reviewed canonical owner. It is empty
# during this architecture-repair stage; current local outputs are proven by build:.
CANONICAL_LOCAL_OUTPUT_REGISTRY: dict[str, str] = {}
# No directory-wide exemptions are permitted. Every future exception must name
# one exact path and explain why scanning that exact file is unsafe or meaningless.
EXACT_SOURCE_EXCLUSIONS: dict[str, str] = {}


@dataclass(frozen=True)
class TrackedFile:
    path: str
    mode: str = "100644"


@dataclass(frozen=True)
class ExecutableSource:
    path: str
    kind: str
    rationale: str


def read_text(root: Path, path: str) -> str:
    return (root / path).read_text(encoding="utf-8", errors="replace")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def tracked_file_records(root: Path) -> list[TrackedFile]:
    result = subprocess.run(
        ["git", "ls-files", "--stage", "-z"],
        cwd=root,
        check=True,
        capture_output=True,
    )
    records: list[TrackedFile] = []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        metadata, raw_path = raw.split(b"\t", 1)
        mode = metadata.split(b" ", 1)[0].decode("ascii")
        records.append(TrackedFile(raw_path.decode("utf-8"), mode))
    return sorted(records, key=lambda item: item.path)


def tracked_files(root: Path) -> list[str]:
    return [item.path for item in tracked_file_records(root)]


def first_line(root: Path, path: str) -> str:
    with (root / path).open(encoding="utf-8", errors="replace") as handle:
        return handle.readline().rstrip("\n")


def is_dockerfile(path: str) -> bool:
    name = Path(path).name
    return name == "Dockerfile" or name.startswith("Dockerfile.")


def is_compose(path: str) -> bool:
    name = Path(path).name.lower()
    return name.startswith(("compose", "docker-compose")) and path.endswith(
        (".yaml", ".yml")
    )


def is_workflow(path: str) -> bool:
    return path.startswith(".github/workflows/") and path.endswith(
        (".yaml", ".yml")
    )


def is_task_file(path: str) -> bool:
    name = Path(path).name.lower()
    lowered = path.lower()
    return (
        name in TASK_NAMES
        or name.startswith("taskfile.")
        or lowered.endswith(TASK_SUFFIXES)
    )


def call_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = call_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


def python_has_execution_call(text: str) -> bool:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return False
    return any(
        isinstance(node, ast.Call) and call_name(node.func) in PYTHON_EXECUTION_CALLS
        for node in ast.walk(tree)
    )


def discover_executable_sources(
    root: Path,
    records: Iterable[TrackedFile],
) -> list[ExecutableSource]:
    sources: list[ExecutableSource] = []
    for record in records:
        path = record.path
        if path in EXACT_SOURCE_EXCLUSIONS:
            continue
        suffix = Path(path).suffix.lower()
        normalized = path.replace("\\", "/")
        shebang = first_line(root, path) if not is_workflow(path) else ""
        source: ExecutableSource | None = None
        if is_workflow(path):
            source = ExecutableSource(path, "github-workflow", "tracked workflow")
        elif is_dockerfile(path):
            source = ExecutableSource(path, "dockerfile", "tracked Dockerfile")
        elif is_compose(path):
            source = ExecutableSource(path, "compose", "tracked Compose file")
        elif suffix in SHELL_SUFFIXES:
            source = ExecutableSource(
                path, "shell", "tracked **/*.sh or **/*.bash"
            )
        elif suffix == ".ps1":
            source = ExecutableSource(path, "powershell", "tracked PowerShell")
        elif is_task_file(path):
            source = ExecutableSource(path, "task-build", "tracked task/build file")
        elif not suffix and SHELL_SHEBANG_RE.search(shebang):
            source = ExecutableSource(
                path, "shell-shebang", "tracked extensionless shell entrypoint"
            )
        elif suffix == ".py":
            text = read_text(root, path)
            if normalized.startswith("deploy/"):
                reason = "tracked deploy/**/*.py operator source"
            elif PYTHON_SHEBANG_RE.search(shebang) or record.mode == "100755":
                reason = "tracked executable Python source"
            elif OPERATOR_NAME_RE.search(Path(path).name):
                reason = "tracked Python operator/build filename"
            elif python_has_execution_call(text):
                reason = "tracked Python source invokes an external process"
            else:
                reason = ""
            if reason:
                source = ExecutableSource(path, "python-operator", reason)
        if source:
            sources.append(source)
    return sorted(sources, key=lambda item: item.path)


def command_blocks(text: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    result: list[tuple[int, str]] = []
    index = 0
    while index < len(lines):
        start = index
        parts = [lines[index].strip()]
        while parts[-1].rstrip().endswith("\\") and index + 1 < len(lines):
            index += 1
            parts.append(lines[index].strip())
        result.append((start + 1, " ".join(parts)))
        index += 1
    return result


def literal_command(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, (ast.List, ast.Tuple)):
        values: list[str] = []
        for element in node.elts:
            if not isinstance(element, ast.Constant) or not isinstance(
                element.value, str
            ):
                return None
            values.append(element.value)
        return " ".join(values)
    return None


def python_commands(text: str) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    commands: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if call_name(node.func) not in PYTHON_EXECUTION_CALLS or not node.args:
            continue
        command = literal_command(node.args[0])
        if command:
            commands.append((node.lineno, command))
    return sorted(commands)


def source_commands(root: Path, source: ExecutableSource) -> list[tuple[int, str]]:
    text = read_text(root, source.path)
    if source.kind == "python-operator":
        return python_commands(text)
    return command_blocks(text)


def is_local_probe(command: str) -> bool:
    urls = URL_RE.findall(command)
    if urls:
        return all(LOCAL_ENDPOINT_RE.search(url) for url in urls)
    return bool(LOCAL_ENDPOINT_RE.search(command))


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


def requirement_constraint(value: str) -> str:
    match = REQ_RE.match(value)
    return match.group(2).strip() if match else ""


def requirement_name(value: str) -> str:
    match = REQ_RE.match(value)
    return match.group(1).lower().replace("_", "-") if match else value.lower()


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
                    owner=f"pyproject.toml [project.optional-dependencies.{group}]",
                )
            )
    entries.append(
        make_entry(
            input_class="python-transitive",
            path="pyproject.toml",
            line=None,
            purpose="Resolved transitive dependency graph",
            scope="tooling/build/runtime/dev/browser",
            canonicality="missing-canonical-lock",
            directness="transitive",
            declaration="pip dynamic resolver output",
            constraint="derived from ranges and package-index state",
            immutable=False,
            hash_coverage="absent",
            reproducibility="not-reproducible",
            risk="CRITICAL",
            owner="proposed generated hashed lock profiles",
            evidence="No accepted transitive lock with integrity hashes is tracked.",
        )
    )
    return entries


def compose_service_blocks(text: str) -> list[dict[str, Any]]:
    services: list[dict[str, Any]] = []
    in_services = False
    current: dict[str, Any] | None = None
    for line_number, raw in enumerate(text.splitlines(), start=1):
        if re.match(r"^services:\s*(?:#.*)?$", raw):
            in_services = True
            current = None
            continue
        if not in_services:
            continue
        if raw and not raw.startswith((" ", "\t")):
            break
        service = re.match(r"^  ([A-Za-z0-9_.-]+):\s*(?:#.*)?$", raw)
        if service:
            current = {
                "name": service.group(1),
                "has_build": False,
                "images": [],
            }
            services.append(current)
            continue
        if current is None:
            continue
        if re.match(r"^    build:\s*(?:.*)?$", raw):
            current["has_build"] = True
        image = re.match(r"^    image:\s*([^\s#]+)(?:\s*#\s*(.*))?\s*$", raw)
        if image:
            current["images"].append(
                (line_number, image.group(1), (image.group(2) or "").strip())
            )
    return services


def image_records(root: Path, files: list[str]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in files:
        if is_dockerfile(path):
            for line_number, raw in enumerate(
                read_text(root, path).splitlines(), start=1
            ):
                match = FROM_RE.match(raw)
                if match:
                    records.append(
                        {
                            "path": path,
                            "line": line_number,
                            "reference": match.group(1),
                            "comment": (match.group(2) or "").strip(),
                            "local": False,
                            "local_evidence": "Docker FROM is an external/base input",
                        }
                    )
        elif is_compose(path):
            for service in compose_service_blocks(read_text(root, path)):
                for line_number, reference, comment in service["images"]:
                    registry_owner = CANONICAL_LOCAL_OUTPUT_REGISTRY.get(reference)
                    local = bool(service["has_build"] or registry_owner)
                    if service["has_build"]:
                        evidence = f"service {service['name']} has tracked build: owner"
                    elif registry_owner:
                        evidence = f"canonical local-output registry: {registry_owner}"
                    else:
                        evidence = "no tracked build owner; external registry input"
                    records.append(
                        {
                            "path": path,
                            "line": line_number,
                            "reference": reference,
                            "comment": comment,
                            "local": local,
                            "local_evidence": evidence,
                        }
                    )
        elif is_workflow(path):
            for line_number, raw in enumerate(
                read_text(root, path).splitlines(), start=1
            ):
                match = IMAGE_RE.match(raw)
                if match:
                    records.append(
                        {
                            "path": path,
                            "line": line_number,
                            "reference": match.group(1),
                            "comment": (match.group(2) or "").strip(),
                            "local": False,
                            "local_evidence": "workflow image is an external input",
                        }
                    )
    return records


def scan_images(root: Path, files: list[str]) -> list[dict[str, Any]]:
    records = image_records(root, files)
    references = Counter(item["reference"] for item in records)
    entries: list[dict[str, Any]] = []
    for item in records:
        reference = item["reference"]
        local = item["local"]
        immutable = reference == "scratch" or bool(IMAGE_DIGEST_RE.search(reference))
        entries.append(
            make_entry(
                input_class="container-output" if local else "container-image",
                path=item["path"],
                line=item["line"],
                purpose=(
                    "Locally built application image output"
                    if local
                    else "External container base/service/test input"
                ),
                scope=(
                    "build-output"
                    if local
                    else "build"
                    if is_dockerfile(item["path"])
                    else "ci"
                    if is_workflow(item["path"])
                    else "runtime/test"
                ),
                canonicality=(
                    "generated-local-output"
                    if local
                    else "duplicate-reference"
                    if references[reference] > 1
                    else "canonical-reference"
                ),
                directness="direct",
                declaration=reference,
                constraint=reference.split("@", 1)[0],
                immutable=immutable,
                hash_coverage="sha256-digest" if immutable else "absent",
                reproducibility=(
                    "local-build-output"
                    if local
                    else "immutable"
                    if immutable
                    else "mutable-tag"
                ),
                risk="MEDIUM" if local else "LOW" if immutable else "HIGH",
                owner=(
                    "final application image digest/build provenance"
                    if local
                    else "canonical container-image registry/reference contract"
                ),
                evidence=item["comment"] or item["local_evidence"],
            )
        )
    return entries


def scan_actions(root: Path, files: list[str]) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for path in (item for item in files if is_workflow(item)):
        for line_number, raw in enumerate(
            read_text(root, path).splitlines(), start=1
        ):
            match = ACTION_RE.match(raw)
            if not match:
                continue
            reference = match.group(1)
            local = reference.startswith("./")
            immutable = local or bool(ACTION_SHA_RE.match(reference))
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
                        reference.rsplit("@", 1)[-1] if "@" in reference else "local"
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
                    evidence=(match.group(2) or "No readable version comment.").strip(),
                )
            )
    return entries


def scan_operations(
    root: Path,
    files: list[str],
    sources: list[ExecutableSource] | None = None,
) -> list[dict[str, Any]]:
    if sources is None:
        records = [TrackedFile(path) for path in files]
        sources = discover_executable_sources(root, records)
    entries: list[dict[str, Any]] = []
    for source in sources:
        for line_number, command in source_commands(root, source):
            stripped = command.strip()
            if not stripped or stripped.startswith("#"):
                continue
            for input_class, pattern in COMMAND_PATTERNS:
                if not pattern.search(stripped):
                    continue
                if input_class == "external-download" and is_local_probe(stripped):
                    break
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
                        path=source.path,
                        line=line_number,
                        purpose="Build, test or deployment input operation",
                        scope="ci/build/runtime tooling",
                        canonicality="operational-declaration",
                        directness="direct",
                        declaration=stripped,
                        constraint="embedded in command or absent",
                        immutable=integrity,
                        hash_coverage=(
                            "inline-or-associated-evidence" if integrity else "absent"
                        ),
                        reproducibility=(
                            "integrity-evidenced" if integrity else "not-proven"
                        ),
                        risk="HIGH" if high_risk and not integrity else "MEDIUM",
                        owner="canonical lock/download/image contract",
                        evidence=(
                            f"Parsed from {source.kind}; discovery={source.rationale}."
                        ),
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
        if not asset_source or Path(path).suffix.lower() not in ASSET_SUFFIXES:
            continue
        for line_number, raw in enumerate(
            read_text(root, path).splitlines(), start=1
        ):
            for url in URL_RE.findall(raw):
                if LOCAL_ENDPOINT_RE.search(url):
                    continue
                immutable_url = bool(ASSET_REV_RE.search(url))
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
                        constraint="immutable URL revision or mutable URL state",
                        immutable=immutable_url,
                        hash_coverage="present" if integrity else "absent",
                        reproducibility=(
                            "immutable-url-with-integrity"
                            if immutable_url and integrity
                            else "immutable-url-no-integrity"
                            if immutable_url
                            else "mutable-external-content"
                        ),
                        risk="MEDIUM" if immutable_url else "HIGH",
                        owner="repository-managed asset or integrity-pinned registry",
                        evidence="Parsed from tracked template/static source.",
                    )
                )
    return entries


def duplicate_owner_groups(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in entries:
        if item["class"] in DIRECT_PYTHON_CLASSES:
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
        declarations = sorted({value["declaration"] for value in values})
        result.append(
            {
                "class": input_class,
                "name": name,
                "occurrences": len(values),
                "paths": sorted({value["path"] for value in values}),
                "declarations": declarations,
                "conflicting_declarations": len(declarations) > 1,
            }
        )
    return result


def contour_summary(
    root: Path,
    files: list[str],
    entries: list[dict[str, Any]],
    sources: list[ExecutableSource],
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
    workflows = sorted(path for path in files if is_workflow(path))
    browser_operations = [
        item for item in entries if item["class"] == "browser-binary-install"
    ]
    static_files = [
        path
        for path in files
        if "/static/" in f"/{path}" or path.startswith("static/")
    ]
    source_kinds = Counter(source.kind for source in sources)
    exact_exclusions = [
        {"path": path, "rationale": rationale}
        for path, rationale in sorted(EXACT_SOURCE_EXCLUSIONS.items())
        if path in tracked
    ]
    return {
        "python": {
            "pyproject_present": "pyproject.toml" in tracked,
            "requirements_files": requirements,
            "lock_files": locks,
            "accepted_profiles": ["tooling", "build", "runtime", "dev", "browser"],
            "integrity_hashed_lock_present": any(
                "--hash=sha256:" in read_text(root, path) for path in requirements
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
                path for path in workflows if TEMP_WORKFLOW_RE.search(Path(path).name)
            ],
        },
        "executable_sources": {
            "applicable_count": len(sources),
            "applicable_paths": [source.path for source in sources],
            "source_kinds": dict(sorted(source_kinds.items())),
            "exact_exclusions": exact_exclusions,
            "uncovered_paths": [],
            "contract": (
                "all tracked applicable source classes are discovered independently "
                "of directory; every exact exclusion is named with rationale"
            ),
        },
        "assets": {
            "tracked_static_file_count": len(static_files),
            "external_asset_reference_count": sum(
                item["class"] == "external-asset" for item in entries
            ),
        },
        "external_downloads": {
            "download_operation_count": sum(
                item["class"] == "external-download" for item in entries
            ),
            "local_runtime_probes_excluded": True,
        },
    }


def build_inventory(root: Path) -> dict[str, Any]:
    records = tracked_file_records(root)
    files = [record.path for record in records]
    sources = discover_executable_sources(root, records)
    entries: list[dict[str, Any]] = []
    entries.extend(pyproject_entries(root, set(files)))
    entries.extend(scan_images(root, files))
    entries.extend(scan_actions(root, files))
    entries.extend(scan_operations(root, files, sources))
    entries.extend(scan_external_assets(root, files))
    entries.sort(
        key=lambda item: (
            item["class"],
            item["path"],
            item["line"] or 0,
            item["declaration"],
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
                "container-output",
                "external-asset",
                "external-download",
                "github-action",
                "python-transitive",
            }
        )
    ]
    immutable = [item["id"] for item in entries if item["immutable"]]
    duplicates = duplicate_owner_groups(entries)
    contours = contour_summary(root, files, entries, sources)
    evidence_paths = {item["path"] for item in entries}
    completeness_paths = {source.path for source in sources}
    exclusion_paths = {
        item["path"] for item in contours["executable_sources"]["exact_exclusions"]
    }
    source_paths = sorted(evidence_paths | completeness_paths | exclusion_paths)
    return {
        "schema": SCHEMA,
        "work_item": "DEPENDENCY-PROVENANCE-001",
        "generation": {
            "method": "repository tracked-file executable/config discovery",
            "tool": "scripts/dependency_provenance_inventory.py",
            "deterministic": True,
            "volatile_fields_excluded": [
                "network-resolved latest versions",
                "runner",
                "wall-clock timestamp",
            ],
        },
        "accepted_boundary": {
            "source": "exact repository commit",
            "python": "direct intent plus future resolved hashed transitive locks",
            "container": "final OCI image plus OS and Python packages",
            "assets": "tracked/generated static assets copied into final image",
            "ci_artifacts": "verified artifacts only after secret-hygiene gate",
            "deployment_carrier": "immutable artifact digest linked to exact head",
        },
        "totals": {
            "tracked_files": len(files),
            "inventory_entries": len(entries),
            "by_class": dict(sorted(Counter(item["class"] for item in entries).items())),
            "floating_inputs": len(floating),
            "immutable_inputs": len(immutable),
            "duplicate_owner_groups": len(duplicates),
            "conflicting_owner_groups": sum(
                item["conflicting_declarations"] for item in duplicates
            ),
            "source_files": len(evidence_paths),
            "applicable_executable_sources": len(completeness_paths),
            "source_completeness_digests": len(source_paths),
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
            (
                "Network registries are not queried; future tag movement is "
                "outside repository evidence."
            ),
            (
                "No accepted transitive Python lock exists; clean resolution "
                "is not reproducible."
            ),
            (
                "Hosted-runner software and Docker/BuildKit versions remain "
                "external inputs."
            ),
            (
                "SBOM and provenance are specified but not emitted in this "
                "inventory-only stage."
            ),
            "An SBOM is an inventory and does not prove absence of vulnerabilities.",
        ],
    }
