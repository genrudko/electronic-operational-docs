#!/usr/bin/env python3
"""Environment-independent entrypoint for the dependency provenance contract.

Compose files contain required runtime values that must not be invented in CI.
This adapter keeps Docker Compose as the structural YAML parser while disabling
interpolation. Dynamic image expressions therefore remain visible and are still
rejected by the canonical validator instead of disappearing during parsing.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from scripts import dependency_provenance_contract as contract


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


def main() -> int:
    contract.compose_config = compose_config_no_interpolate
    return contract.main()


if __name__ == "__main__":
    raise SystemExit(main())
