from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from eod_config.deployment import (  # noqa: E402
    DeploymentConfigurationError,
    PRODUCTION_CAPABLE_MODE,
    validate_deployment_environment,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Fail-closed EOD deployment preflight")
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate the environment contract without invoking Django deploy checks.",
    )
    args = parser.parse_args()

    try:
        contract = validate_deployment_environment(os.environ)
    except DeploymentConfigurationError as exc:
        print(f"DEPLOYMENT_PREFLIGHT=FAIL {exc}", file=sys.stderr)
        return 2

    if contract.mode != PRODUCTION_CAPABLE_MODE:
        print(
            "DEPLOYMENT_PREFLIGHT=FAIL active profile is not production-capable",
            file=sys.stderr,
        )
        return 2

    print("DEPLOYMENT_PREFLIGHT=CONFIG_OK mode=production database=postgresql tls=reverse-proxy")
    if args.validate_only:
        return 0

    result = subprocess.run(
        [
            sys.executable,
            "manage.py",
            "check",
            "--deploy",
            "--fail-level",
            "WARNING",
        ],
        cwd=ROOT,
        env=os.environ.copy(),
        check=False,
    )
    if result.returncode:
        print("DEPLOYMENT_PREFLIGHT=FAIL django_deploy_checks", file=sys.stderr)
        return result.returncode
    print("DEPLOYMENT_PREFLIGHT=PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
