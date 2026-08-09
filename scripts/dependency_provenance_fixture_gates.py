#!/usr/bin/env python3
"""Small parser gates used by permanent positive/negative fixtures.

These checks cover evidence that is represented by workflow/component-set policy
rather than by one package/image parser in dependency_provenance_contract.py.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from scripts import dependency_provenance_contract as contract
from scripts.dependency_provenance_contract import ContractViolation

PROFILES = ("tooling", "build", "runtime", "dev", "browser")


def validate_clean_install_workflow(text: str) -> None:
    for profile in PROFILES:
        if profile not in text:
            raise ContractViolation("clean-hashed-install", f"missing-profile:{profile}")
    if "--require-hashes" not in text or "--without-pip" not in text:
        raise ContractViolation("clean-hashed-install", "untrusted-or-nonclean-install")
    if "pip --python" not in text:
        raise ContractViolation("clean-hashed-install", "accepted-installer-not-used")


def validate_build_workflow(text: str) -> None:
    build_commands = re.findall(r"python -m build[^\n]*", text)
    if not build_commands or any("--no-isolation" not in item for item in build_commands):
        raise ContractViolation("locked-build-environment", repr(build_commands))


def validate_runtime_install_workflow(text: str) -> None:
    if re.search(r"pip install[^\n]*(?:--editable|\s-e\b|--upgrade)", text):
        raise ContractViolation("locked-runtime-install", "editable-or-upgrade")
    wheel_installs = re.findall(r"pip install[^\n]*\.whl", text)
    if not wheel_installs or any("--no-deps" not in item for item in wheel_installs):
        raise ContractViolation("locked-runtime-install", repr(wheel_installs))


def validate_reusable_workflow_reference(reference: str) -> None:
    if "@" not in reference:
        raise ContractViolation("immutable-reusable-workflow", reference)
    _, revision = reference.rsplit("@", 1)
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ContractViolation("immutable-reusable-workflow", reference)


def validate_exact_head_workflow(text: str) -> None:
    required = (
        "github.event.pull_request.head.sha || github.sha",
        "git rev-parse HEAD",
        "SOURCE_COMMIT",
    )
    if not all(item in text for item in required):
        raise ContractViolation("single-final-exact-head-evidence", "exact-head-chain")


def validate_publication_order_workflow(text: str) -> None:
    secret = text.find("Verify wheel and evidence are credential-free before publication")
    manifest = text.find("Build and verify artifact-content manifest")
    upload_match = re.search(
        r"Upload verified (?:deterministic )?exact-head evidence",
        text,
    )
    upload = upload_match.start() if upload_match else -1
    if min(secret, manifest, upload) < 0 or not secret < manifest < upload:
        raise ContractViolation("secret-scan-before-publication", "workflow-order")


def validate_emergency_update_workflow(text: str) -> None:
    forbidden = ("continue-on-error: true", "|| true", "--no-verify")
    if any(item in text for item in forbidden):
        raise ContractViolation("emergency-update-controls", "bypass-token")
    required = ("verify-locks", "regenerate_dependency_locks.py", "verify-clean-tree")
    if not all(item in text for item in required):
        raise ContractViolation("emergency-update-controls", "mandatory-gate-missing")


def validate_javascript_contour(paths: list[str]) -> None:
    manifests = {
        path
        for path in paths
        if Path(path).name
        in {
            "package.json",
            "package-lock.json",
            "pnpm-lock.yaml",
            "yarn.lock",
            "npm-shrinkwrap.json",
        }
    }
    if manifests:
        raise ContractViolation("javascript-contour-owner", repr(sorted(manifests)))


def validate_service_boundary(component_set: dict[str, Any]) -> None:
    components = component_set.get("components", [])
    roles = [item.get("role") for item in components]
    if roles.count("production") != 1 or roles.count("browser-test") != 1:
        raise ContractViolation("sbom-service-boundary", repr(roles))
    services = [item for item in components if item.get("role") == "service-image"]
    if not services or any(not item.get("name") or not item.get("sha256") for item in services):
        raise ContractViolation("sbom-service-boundary", repr(services))


def validate_namespace_uniqueness(records: list[dict[str, str]]) -> None:
    owners: dict[str, tuple[str, str, str]] = {}
    for item in records:
        namespace = item.get("documentNamespace", "")
        identity = (
            item.get("imageDigest", ""),
            item.get("sourceCommit", ""),
            item.get("buildDefinitionDigest", ""),
        )
        previous = owners.setdefault(namespace, identity)
        if not namespace or previous != identity:
            raise ContractViolation(
                "spdx-document-namespace-unique-subject",
                f"namespace={namespace}",
            )


def validate_malformed_lock_fixture(path: Path) -> None:
    try:
        contract.parse_lock(path)
    except ContractViolation as exc:
        raise ContractViolation(
            "malformed-truncated-lock-fixture", exc.evidence
        ) from exc
    raise ContractViolation("malformed-truncated-lock-fixture", "fixture-was-accepted")


def validate_artifact_text(path: str, text: str) -> None:
    patterns = (
        r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----",
        r"gh[pousr]_[A-Za-z0-9]{20,}",
        r"postgres(?:ql)?://[^\s:@]+:[^\s@]+@",
    )
    if any(re.search(pattern, text) for pattern in patterns):
        raise ContractViolation("artifact-secret-free", path)
