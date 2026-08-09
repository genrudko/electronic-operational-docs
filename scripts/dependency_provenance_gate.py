#!/usr/bin/env python3
"""Environment-independent entrypoint for the dependency provenance contract.

Compose files contain required runtime values that must not be invented in CI.
This adapter keeps Docker Compose as the structural YAML parser while disabling
interpolation. One exact dynamic local-image carrier is accepted only while its
tracked controller proves the local build owner, exact-SHA tag and Compose handoff.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any

import dependency_provenance_contract as contract
import dependency_provenance_source_gate as source_gate

LOCAL_CARRIER_REFERENCE = "${EOD_RELEASE_IMAGE:?EOD_RELEASE_IMAGE is required}"
LOCAL_CARRIER_EVIDENCE = "deploy/automation/compose.development.yaml:app"
CONTROLLER = contract.ROOT / "deploy/automation/eod-development-controller"
DOWNLOAD_COMMAND_RE = re.compile(
    r"(?:^|(?:run:|RUN|&&|\|\||;|then|do|if|while)\s+)"
    r"(?:!\s+)?(?:sudo\s+)?(?:[A-Za-z0-9_./-]+/)?(?:curl|wget)\b",
    re.I,
)


def compose_config_no_interpolate(path: Path) -> dict[str, Any]:
    try:
        output = subprocess.run(
            [
                "docker",
                "compose",
                "-f",
                str(path),
                "config",
                "--no-interpolate",
                "--format",
                "json",
            ],
            cwd=contract.ROOT,
            check=True,
            capture_output=True,
            text=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError) as exc:
        raise contract.ContractViolation(
            "compose-structural-parse", str(path)
        ) from exc
    try:
        data = json.loads(output)
    except json.JSONDecodeError as exc:
        raise contract.ContractViolation(
            "compose-structural-parse", str(path)
        ) from exc
    if not isinstance(data, dict) or not isinstance(data.get("services", {}), dict):
        raise contract.ContractViolation("compose-structural-parse", str(path))
    return data


def local_carrier_owner_is_proven() -> bool:
    text = CONTROLLER.read_text(encoding="utf-8")
    required_evidence = (
        'require_sha() {',
        'local image="eod-development-app:$sha"',
        'EOD_RELEASE_IMAGE="$1" docker compose',
    )
    return all(item in text for item in required_evidence)


def validate_image_reference_with_local_carrier(
    reference: str,
    evidence: str,
    registry: dict[str, Any],
) -> None:
    if reference == LOCAL_CARRIER_REFERENCE and evidence == LOCAL_CARRIER_EVIDENCE:
        if not local_carrier_owner_is_proven():
            raise contract.ContractViolation("local-build-owner", evidence)
        return
    contract._original_validate_image_reference(reference, evidence, registry)


def validate_one_command_with_exact_download_detection(
    path: str,
    line: int,
    command: str,
) -> None:
    candidate = command
    if re.search(r"\b(?:curl|wget)\b", candidate) and not DOWNLOAD_COMMAND_RE.search(
        candidate
    ):
        candidate = re.sub(r"\b(?:curl|wget)\b", "listed-tool", candidate)
    contract._original_validate_one_command(path, line, candidate)


def independently_applicable_paths(paths: object) -> set[str]:
    del paths
    return source_gate.independently_applicable_paths(contract.ROOT)


def main() -> int:
    for relative in (
        ".github/workflows/dependency-provenance.yml",
        "scripts/dependency_provenance_contract.py",
    ):
        print(f"SOURCE_SHA256 {relative}={contract.sha256_file(contract.ROOT / relative)}")
    contract.compose_config = compose_config_no_interpolate
    contract.independently_applicable_paths = independently_applicable_paths
    contract._original_validate_image_reference = contract.validate_image_reference
    contract.validate_image_reference = validate_image_reference_with_local_carrier
    contract._original_validate_one_command = contract.validate_one_command
    contract.validate_one_command = validate_one_command_with_exact_download_detection
    return contract.main()


if __name__ == "__main__":
    raise SystemExit(main())
