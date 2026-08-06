#!/usr/bin/env python3
"""Bootstrap and apply the accepted DEPENDENCY-PROVENANCE-001 contract.

The controller deliberately separates discovery from execution:

1. download exact bootstrap distributions and verify each file against the
   official PyPI JSON digest before importing/executing candidate tooling;
2. resolve OCI tags to immutable repository digests;
3. materialise the canonical registry and a hash-only bootstrap manifest;
4. install the generator from the verified local wheelhouse with
   --require-hashes and --no-index;
5. generate all five lock projections, verify semantic and byte exactness;
6. migrate repository installation and immutable-reference paths.

It is intended to run in the repository-owned dependency-provenance workflow.
"""

from __future__ import annotations

import argparse
import email
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "supply-chain/registry.json"
BOOTSTRAP_PATH = ROOT / "requirements/bootstrap.txt"
LOCK_DIR = ROOT / "requirements/locks"
SCHEMA_PATH = ROOT / "supply-chain/schema/spdx-2.3.schema.json"
FONT_PATH = ROOT / "src/static/system/fonts/Onest[wght].woff2"
TYPOGRAPHY_PATH = ROOT / "src/static/system/eod_typography.css"

PYTHON_MINOR = "3.13"
PLATFORM = "linux_x86_64"
PIP_VERSION = "25.3"
PIP_TOOLS_VERSION = "7.6.0"
JSONSCHEMA_VERSION = "4.26.0"
PLAYWRIGHT_VERSION = "1.58.0"
SYFT_VERSION = "1.44.0"

PYTHON_IMAGE = "python:3.13-slim-bookworm"
POSTGRES_IMAGE = "postgres:18.4-bookworm"
PLAYWRIGHT_IMAGE = f"mcr.microsoft.com/playwright/python:v{PLAYWRIGHT_VERSION}-noble"
SYFT_IMAGE = f"anchore/syft:v{SYFT_VERSION}"

ONEST_URL = (
    "https://cdn.jsdelivr.net/gh/simpals/onest@"
    "f18c06a14512e43a6191849278d6f07fdaf347d6/"
    "fonts/webfonts/Onest%5Bwght%5D.woff2"
)
SPDX_REF = "v2.3"
SPDX_REPOSITORY = "spdx/spdx-spec"
SPDX_SCHEMA_RELPATH = "schemas/spdx-schema.json"

ACTION_REVISIONS = {
    "actions/checkout": {
        "version": "v6",
        "sha": "d23441a48e516b6c34aea4fa41551a30e30af803",
    },
    "actions/setup-python": {
        "version": "v6",
        "sha": "ece7cb06caefa5fff74198d8649806c4678c61a1",
    },
    "actions/upload-artifact": {
        "version": "v7",
        "sha": "043fb46d1a93c77aae656e7c1c64a875d1fc6a0a",
    },
    "actions/github-script": {
        "version": "v8",
        "sha": "3a2844b7e9c422d3c10d287c895573f7108da1b3",
    },
}

# These are the exact versions observed on the accepted architecture head.
# They constrain initial lock generation so implementation does not perform an
# opportunistic application dependency upgrade.
ACCEPTED_RESOLUTION = {
    "asgiref": "3.12.1",
    "coverage": "7.15.4",
    "django": "5.2.17",
    "et-xmlfile": "2.0.0",
    "gunicorn": "26.0.0",
    "jsonschema": JSONSCHEMA_VERSION,
    "openpyxl": "3.1.5",
    "packaging": "26.3",
    "pip": PIP_VERSION,
    "playwright": PLAYWRIGHT_VERSION,
    "psycopg": "3.3.4",
    "psycopg-binary": "3.3.4",
    "ruff": "0.16.1",
    "setuptools": "83.0.0",
    "sqlparse": "0.5.5",
    "wheel": "0.47.0",
    "whitenoise": "6.12.0",
}

LOCK_PROFILES = ("tooling", "build", "runtime", "dev", "browser")


class ContractError(RuntimeError):
    """Fail-closed implementation error."""


@dataclass(frozen=True)
class Distribution:
    name: str
    version: str
    filename: str
    url: str
    sha256: str


def run(*args: str, cwd: Path = ROOT, capture: bool = False) -> str:
    result = subprocess.run(
        list(args),
        cwd=cwd,
        check=True,
        text=True,
        capture_output=capture,
    )
    return result.stdout.strip() if capture else ""


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def fetch_json(url: str, *, token: str | None = None) -> dict[str, Any]:
    headers = {"Accept": "application/json", "User-Agent": "eod-supply-chain/1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        headers["X-GitHub-Api-Version"] = "2022-11-28"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as response:
        return json.loads(response.read().decode("utf-8"))


def fetch_bytes(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "eod-supply-chain/1"})
    with urllib.request.urlopen(request) as response:
        return response.read()


def normalized_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def wheel_name_version(filename: str) -> tuple[str, str]:
    if not filename.endswith(".whl"):
        raise ContractError(f"bootstrap-source-distribution-forbidden: {filename}")
    parts = filename[:-4].split("-")
    if len(parts) < 5:
        raise ContractError(f"invalid-wheel-name: {filename}")
    return normalized_name(parts[0]), parts[1]


def metadata_requires(wheel: Path) -> list[str]:
    with zipfile.ZipFile(wheel) as archive:
        metadata_name = next(
            name for name in archive.namelist() if name.endswith(".dist-info/METADATA")
        )
        message = email.message_from_bytes(archive.read(metadata_name))
    return list(message.get_all("Requires-Dist", []))


def marker_applies(requirement: str) -> bool:
    # pip download already evaluates markers for the accepted interpreter and
    # platform. The subsequent no-index/require-hashes install is the
    # fail-closed wheelhouse-completeness proof.
    return False


def requirement_name(requirement: str) -> str:
    match = re.match(r"\s*([A-Za-z0-9_.-]+)", requirement)
    if not match:
        raise ContractError(f"opaque-bootstrap-requirement: {requirement}")
    return normalized_name(match.group(1))


def pypi_release(name: str, version: str) -> dict[str, Any]:
    return fetch_json(f"https://pypi.org/pypi/{name}/{version}/json")


def verified_bootstrap_wheelhouse(work: Path) -> list[Distribution]:
    wheelhouse = work / "wheelhouse"
    wheelhouse.mkdir(parents=True)
    run(
        sys.executable,
        "-m",
        "pip",
        "download",
        "--disable-pip-version-check",
        "--only-binary=:all:",
        "--dest",
        str(wheelhouse),
        f"pip=={PIP_VERSION}",
        f"pip-tools=={PIP_TOOLS_VERSION}",
    )

    distributions: list[Distribution] = []
    for wheel in sorted(wheelhouse.glob("*.whl")):
        name, version = wheel_name_version(wheel.name)
        metadata = pypi_release(name, version)
        candidate = next(
            (
                item
                for item in metadata["urls"]
                if item["filename"] == wheel.name
                and item["packagetype"] == "bdist_wheel"
            ),
            None,
        )
        if candidate is None:
            raise ContractError(f"pypi-wheel-evidence-missing: {wheel.name}")
        actual = sha256_file(wheel)
        expected = candidate["digests"]["sha256"]
        if actual != expected:
            raise ContractError(
                f"bootstrap-distribution-digest-mismatch: {wheel.name} "
                f"expected={expected} actual={actual}"
            )
        distributions.append(
            Distribution(name, version, wheel.name, candidate["url"], actual)
        )

    names = {item.name for item in distributions}
    required = {"pip", "pip-tools"}
    if not required.issubset(names):
        raise ContractError(f"bootstrap-wheelhouse-incomplete: {sorted(required - names)}")

    # Prove every non-extra metadata dependency has a downloaded owner. pip has
    # vendored dependencies and intentionally reports none.
    for wheel in sorted(wheelhouse.glob("*.whl")):
        for requirement in metadata_requires(wheel):
            if marker_applies(requirement):
                owner = requirement_name(requirement)
                if owner not in names:
                    raise ContractError(
                        f"bootstrap-transitive-distribution-missing: {wheel.name} -> {owner}"
                    )
    return distributions


def render_bootstrap(distributions: list[Distribution]) -> str:
    lines = [
        "# GENERATED BY scripts/dependency_provenance_implementation.py",
        f"# python={PYTHON_MINOR} platform={PLATFORM}",
        "# root=official-pypi-json-digest+downloaded-wheel-sha256",
        "# timestamps and machine paths are intentionally absent",
        "",
    ]
    for item in sorted(distributions, key=lambda value: value.name):
        lines.append(f"{item.name}=={item.version} --hash=sha256:{item.sha256}")
    return "\n".join(lines) + "\n"


def resolve_image(reference: str) -> dict[str, str]:
    run("docker", "pull", reference)
    repo_digest = run(
        "docker",
        "image",
        "inspect",
        reference,
        "--format={{index .RepoDigests 0}}",
        capture=True,
    )
    if "@sha256:" not in repo_digest:
        raise ContractError(f"image-repository-digest-missing: {reference}")
    repository, digest = repo_digest.rsplit("@", 1)
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
        raise ContractError(f"invalid-image-digest: {repo_digest}")
    return {"tag": reference, "repository": repository, "digest": digest}


def resolve_spdx_schema(token: str | None) -> tuple[bytes, dict[str, str]]:
    ref = fetch_json(
        f"https://api.github.com/repos/{SPDX_REPOSITORY}/git/ref/tags/{SPDX_REF}",
        token=token,
    )
    target = ref["object"]
    if target["type"] == "tag":
        target = fetch_json(target["url"], token=token)["object"]
    if target["type"] != "commit" or not re.fullmatch(r"[0-9a-f]{40}", target["sha"]):
        raise ContractError("spdx-schema-tag-resolution-failed")
    commit = target["sha"]
    url = (
        f"https://raw.githubusercontent.com/{SPDX_REPOSITORY}/{commit}/"
        f"{SPDX_SCHEMA_RELPATH}"
    )
    content = fetch_bytes(url)
    parsed = json.loads(content)
    if parsed.get("title") != "SPDX 2.3":
        raise ContractError("spdx-schema-title-mismatch")
    return content, {
        "version": "2.3",
        "repository": SPDX_REPOSITORY,
        "commit": commit,
        "path": SPDX_SCHEMA_RELPATH,
        "url": url,
        "sha256": sha256_bytes(content),
    }


def write_registry(
    distributions: list[Distribution],
    images: dict[str, dict[str, str]],
    schema: dict[str, str],
    font_sha256: str,
) -> dict[str, Any]:
    source_commit = run("git", "rev-parse", "HEAD", capture=True)
    registry: dict[str, Any] = {
        "schema": 1,
        "contract": "DEPENDENCY-PROVENANCE-001",
        "python": {"minor": PYTHON_MINOR, "platform": PLATFORM, "implementation": "CPython"},
        "generator": {
            "kind": "pip-tools",
            "version": PIP_TOOLS_VERSION,
            "oci": images["python"],
            "bootstrap_root": {
                "source": "official PyPI JSON distribution digest plus downloaded wheel SHA-256",
                "source_commit": source_commit,
                "pip": PIP_VERSION,
                "pip_tools": PIP_TOOLS_VERSION,
                "distributions": [item.__dict__ for item in sorted(distributions, key=lambda value: value.name)],
            },
        },
        "lock_profiles": [
            {"name": name, "path": f"requirements/locks/{name}.txt"}
            for name in LOCK_PROFILES
        ],
        "accepted_resolution": ACCEPTED_RESOLUTION,
        "external_images": images,
        "github_actions": ACTION_REVISIONS,
        "browser": {
            "package": {"name": "playwright", "version": PLAYWRIGHT_VERSION},
            "image": images["playwright"],
            "compatibility": "package and image release versions must be identical",
        },
        "spdx_schema": schema,
        "tooling": {
            "sbom": {"name": "anchore/syft", "version": SYFT_VERSION, "image": images["syft"]},
            "provenance": {"name": "repository-python-generator", "script": "scripts/dependency_provenance_contract.py"},
        },
        "external_assets": {
            "onest_variable_woff2": {
                "source_url": ONEST_URL,
                "upstream_commit": "f18c06a14512e43a6191849278d6f07fdaf347d6",
                "repository_path": "src/static/system/fonts/Onest[wght].woff2",
                "sha256": font_sha256,
            }
        },
        "policy": {
            "external_saas": False,
            "publication_requires_secret_hygiene": True,
            "byte_reproducibility_claimed": False,
        },
    }
    REGISTRY_PATH.parent.mkdir(parents=True, exist_ok=True)
    REGISTRY_PATH.write_text(canonical_json(registry), encoding="utf-8")
    return registry


def bootstrap_environment(work: Path) -> Path:
    venv = work / "generator-venv"
    run(sys.executable, "-m", "venv", str(venv))
    python = venv / "bin/python"
    wheelhouse = work / "wheelhouse"
    run(
        str(python),
        "-m",
        "pip",
        "install",
        "--disable-pip-version-check",
        "--no-index",
        "--find-links",
        str(wheelhouse),
        "--require-hashes",
        "-r",
        str(BOOTSTRAP_PATH),
    )
    return python


def write_lock_inputs(work: Path) -> dict[str, Path]:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]
    build_requires = data["build-system"]["requires"]
    optional = project.get("optional-dependencies", {})

    constraints = work / "accepted-constraints.txt"
    constraints.write_text(
        "".join(f"{name}=={version}\n" for name, version in sorted(ACCEPTED_RESOLUTION.items())),
        encoding="utf-8",
    )

    profiles: dict[str, list[str]] = {
        "tooling": [
            f"pip=={PIP_VERSION}",
            f"pip-tools=={PIP_TOOLS_VERSION}",
            f"jsonschema=={JSONSCHEMA_VERSION}",
        ],
        "build": [*build_requires, "build>=1.3,<2", "wheel>=0.47,<1"],
        "runtime": list(project.get("dependencies", [])),
        "dev": [*project.get("dependencies", []), *optional.get("dev", [])],
        "browser": [*project.get("dependencies", []), *optional.get("browser", [])],
    }
    result: dict[str, Path] = {}
    for name in LOCK_PROFILES:
        path = work / f"{name}.in"
        path.write_text(
            f"-c {constraints}\n" + "\n".join(profiles[name]) + "\n",
            encoding="utf-8",
        )
        result[name] = path
    return result


def generate_locks(generator_python: Path, work: Path) -> None:
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    inputs = write_lock_inputs(work)
    env = os.environ.copy()
    env["CUSTOM_COMPILE_COMMAND"] = (
        "python scripts/dependency_provenance_implementation.py verify-locks"
    )
    for name in LOCK_PROFILES:
        output = LOCK_DIR / f"{name}.txt"
        command = [
            str(generator_python),
            "-m",
            "piptools",
            "compile",
            "--generate-hashes",
            "--allow-unsafe",
            "--strip-extras",
            "--resolver=backtracking",
            "--no-emit-index-url",
            "--no-emit-trusted-host",
            "--newline=lf",
            "--output-file",
            str(output),
            str(inputs[name]),
        ]
        subprocess.run(command, cwd=ROOT, check=True, env=env)
        normalize_lock_header(output, name)


def normalize_lock_header(path: Path, profile: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    first_requirement = next(
        (index for index, line in enumerate(lines) if line and not line.startswith("#")),
        len(lines),
    )
    body = [
        re.sub(r"/tmp/eod-supply-[^/\s]+/", "<generator>/", line)
        for line in lines[first_requirement:]
    ]
    header = [
        "# GENERATED FILE - DO NOT EDIT",
        f"# profile={profile}",
        f"# python={PYTHON_MINOR}",
        f"# platform={PLATFORM}",
        "# source=pyproject.toml+supply-chain/registry.json",
        "# generator=pip-tools==" + PIP_TOOLS_VERSION,
        "# regeneration=python scripts/dependency_provenance_implementation.py verify-locks",
        "",
    ]
    path.write_text("\n".join(header + body).rstrip() + "\n", encoding="utf-8")


def parse_lock(path: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    current = ""
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        current = f"{current} {line}".strip() if current else line
        if current.endswith("\\"):
            current = current[:-1].rstrip()
            continue
        match = re.match(r"^([A-Za-z0-9_.-]+)==([^\s\\]+)(.*)$", current)
        if not match:
            raise ContractError(f"exact-lock-version: {path}:{current}")
        name = normalized_name(match.group(1))
        hashes = re.findall(r"--hash=sha256:([0-9a-f]{64})", match.group(3))
        if not hashes:
            raise ContractError(f"lock-integrity-hashes: {path}:{name}")
        if name in records:
            raise ContractError(f"duplicate-lock-record: {path}:{name}")
        records[name] = {"version": match.group(2), "hashes": sorted(set(hashes))}
        current = ""
    if current:
        raise ContractError(f"truncated-lock-record: {path}")
    return records


def verify_locks() -> None:
    if not REGISTRY_PATH.exists():
        raise ContractError("canonical-registry-missing")
    for profile in LOCK_PROFILES:
        path = LOCK_DIR / f"{profile}.txt"
        if not path.exists():
            raise ContractError(f"lock-profile-missing: {profile}")
        records = parse_lock(path)
        if not records:
            raise ContractError(f"lock-profile-empty: {profile}")
    runtime = parse_lock(LOCK_DIR / "runtime.txt")
    dev = parse_lock(LOCK_DIR / "dev.txt")
    browser = parse_lock(LOCK_DIR / "browser.txt")
    if not set(runtime).issubset(dev) or not set(runtime).issubset(browser):
        raise ContractError("profile-layering-drift")
    if browser.get("playwright", {}).get("version") != PLAYWRIGHT_VERSION:
        raise ContractError("browser-binary-provenance")


def replace_exact(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        return
    path.write_text(text.replace(old, new), encoding="utf-8")


def pin_references(registry: dict[str, Any]) -> None:
    for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for owner, evidence in ACTION_REVISIONS.items():
            text = re.sub(
                rf"{re.escape(owner)}@(?:v[^\s#]+|[0-9a-f]{{40}})(?:\s*#\s*[^\n]*)?",
                f"{owner}@{evidence['sha']} # {evidence['version']}",
                text,
            )
        workflow.write_text(text, encoding="utf-8")

    image_map = {
        PYTHON_IMAGE: (
            f"{registry['external_images']['python']['repository']}@"
            f"{registry['external_images']['python']['digest']}"
        ),
        POSTGRES_IMAGE: (
            f"{registry['external_images']['postgres']['repository']}@"
            f"{registry['external_images']['postgres']['digest']}"
        ),
    }
    candidates = [
        ROOT / "Dockerfile",
        ROOT / "deploy/automation/Dockerfile.development",
        ROOT / "compose.yaml",
        ROOT / "compose.preview.yaml",
        ROOT / "compose.development.yaml",
        ROOT / "deploy/automation/compose.development.yaml",
        *sorted((ROOT / ".github/workflows").glob("*.yml")),
    ]
    for path in candidates:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for old, immutable in image_map.items():
            text = text.replace(old, immutable)
        path.write_text(text, encoding="utf-8")


def rewrite_dockerfiles(registry: dict[str, Any]) -> None:
    python_ref = (
        f"{registry['external_images']['python']['repository']}@"
        f"{registry['external_images']['python']['digest']}"
    )
    production = f'''FROM {python_ref} AS build
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/build-venv/bin:$PATH"
WORKDIR /app
RUN python -m venv /opt/build-venv
COPY requirements/locks/build.txt requirements/locks/runtime.txt /app/requirements/locks/
RUN python -m pip install --disable-pip-version-check --require-hashes \\
    -r requirements/locks/build.txt
COPY pyproject.toml README.md manage.py /app/
COPY src /app/src
RUN python -m build --wheel --no-isolation --outdir /app/dist

FROM {python_ref} AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /app
RUN python -m venv /opt/venv
COPY requirements/locks/runtime.txt /app/requirements/locks/runtime.txt
RUN python -m pip install --disable-pip-version-check --require-hashes \\
    -r requirements/locks/runtime.txt
COPY --from=build /app/dist/*.whl /tmp/eod/
RUN python -m pip install --disable-pip-version-check --no-deps /tmp/eod/*.whl \\
    && rm -rf /tmp/eod
COPY manage.py /app/manage.py
COPY scripts/container-entrypoint.sh /app/scripts/container-entrypoint.sh
RUN chmod +x /app/scripts/container-entrypoint.sh \\
    && mkdir -p /app/data /app/media /app/staticfiles /app/logs \\
    && chown -R 10001:10001 /app
USER 10001:10001
EXPOSE 8765
ENTRYPOINT ["/app/scripts/container-entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8765", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
'''
    (ROOT / "Dockerfile").write_text(production, encoding="utf-8")

    development = f'''FROM {python_ref}
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PATH="/opt/venv/bin:$PATH"
WORKDIR /workspace
RUN python -m venv /opt/venv
COPY requirements/locks/build.txt requirements/locks/dev.txt /workspace/requirements/locks/
RUN python -m pip install --disable-pip-version-check --require-hashes \\
    -r requirements/locks/build.txt \\
    && python -m pip install --disable-pip-version-check --require-hashes \\
    -r requirements/locks/dev.txt
COPY pyproject.toml README.md /workspace/
COPY src /workspace/src
RUN python -m build --wheel --no-isolation --outdir /tmp/eod-wheel \\
    && python -m pip install --disable-pip-version-check --no-deps /tmp/eod-wheel/*.whl \\
    && rm -rf /tmp/eod-wheel
COPY deploy/automation/app-entrypoint.sh /usr/local/bin/eod-development-app-entrypoint
RUN chmod +x /usr/local/bin/eod-development-app-entrypoint
EXPOSE 8000
ENTRYPOINT ["/usr/local/bin/eod-development-app-entrypoint"]
CMD ["gunicorn", "config.wsgi:application", "--reload", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "--error-logfile", "-"]
'''
    (ROOT / "deploy/automation/Dockerfile.development").write_text(
        development, encoding="utf-8"
    )


def migrate_install_commands() -> None:
    replacements = {
        "python -m pip install --upgrade pip setuptools wheel": (
            "python -m pip install --disable-pip-version-check --require-hashes "
            "-r requirements/locks/tooling.txt"
        ),
        'python -m pip install --editable ".[dev]"': (
            "python -m pip install --disable-pip-version-check --require-hashes "
            "-r requirements/locks/build.txt\n"
            "          python -m pip install --disable-pip-version-check --require-hashes "
            "-r requirements/locks/dev.txt\n"
            "          python -m build --wheel --no-isolation --outdir dist\n"
            "          python -m pip install --disable-pip-version-check --no-deps dist/*.whl"
        ),
        "python -m pip install --editable .[dev]": (
            "python -m pip install --disable-pip-version-check --require-hashes "
            "-r requirements/locks/build.txt\n"
            "          python -m pip install --disable-pip-version-check --require-hashes "
            "-r requirements/locks/dev.txt\n"
            "          python -m build --wheel --no-isolation --outdir dist\n"
            "          python -m pip install --disable-pip-version-check --no-deps dist/*.whl"
        ),
    }
    for workflow in sorted((ROOT / ".github/workflows").glob("*.yml")):
        text = workflow.read_text(encoding="utf-8")
        for old, new in replacements.items():
            text = text.replace(old, new)
        text = text.replace("cache-dependency-path: pyproject.toml", "cache-dependency-path: requirements/locks/*.txt")
        workflow.write_text(text, encoding="utf-8")


def vendor_font(content: bytes) -> None:
    FONT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FONT_PATH.write_bytes(content)
    css = TYPOGRAPHY_PATH.read_text(encoding="utf-8")
    css = re.sub(
        r'https://cdn\.jsdelivr\.net/gh/simpals/onest@[^"\)]+/Onest%5Bwght%5D\.woff2',
        "fonts/Onest%5Bwght%5D.woff2",
        css,
    )
    css = css.replace(
        "The acceptance candidate loads the exact variable WOFF2\n * from an immutable upstream revision; production/offline packaging must host\n * the same licensed asset locally.",
        "The exact accepted variable WOFF2 is repository-managed and verified\n * by the canonical supply-chain registry before build/publication.",
    )
    TYPOGRAPHY_PATH.write_text(css, encoding="utf-8")


def regenerate_inventory_views() -> None:
    script = ROOT / "scripts/dependency_provenance_views.py"
    if script.exists():
        run(sys.executable, str(script), "write")


def apply() -> None:
    token = os.environ.get("GITHUB_TOKEN")
    with tempfile.TemporaryDirectory(prefix="eod-supply-") as directory:
        work = Path(directory)
        distributions = verified_bootstrap_wheelhouse(work)
        BOOTSTRAP_PATH.parent.mkdir(parents=True, exist_ok=True)
        BOOTSTRAP_PATH.write_text(render_bootstrap(distributions), encoding="utf-8")

        images = {
            "python": resolve_image(PYTHON_IMAGE),
            "postgres": resolve_image(POSTGRES_IMAGE),
            "playwright": resolve_image(PLAYWRIGHT_IMAGE),
            "syft": resolve_image(SYFT_IMAGE),
        }
        schema_content, schema = resolve_spdx_schema(token)
        SCHEMA_PATH.parent.mkdir(parents=True, exist_ok=True)
        SCHEMA_PATH.write_bytes(schema_content)

        font_content = fetch_bytes(ONEST_URL)
        font_sha256 = sha256_bytes(font_content)
        vendor_font(font_content)

        registry = write_registry(distributions, images, schema, font_sha256)
        generator_python = bootstrap_environment(work)
        generate_locks(generator_python, work)
        verify_locks()
        pin_references(registry)
        rewrite_dockerfiles(registry)
        migrate_install_commands()
        regenerate_inventory_views()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("apply", "verify-locks"))
    args = parser.parse_args()
    try:
        if args.command == "apply":
            apply()
        else:
            verify_locks()
    except (ContractError, subprocess.CalledProcessError, OSError, ValueError) as exc:
        print(f"DEPENDENCY_PROVENANCE_IMPLEMENTATION=FAIL error={exc}", file=sys.stderr)
        return 1
    print(f"DEPENDENCY_PROVENANCE_IMPLEMENTATION=PASS command={args.command}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
