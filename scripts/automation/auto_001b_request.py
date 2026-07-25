from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from scripts.automation.auto_001a_foundation import (
    FoundationValidationError,
    append_github_outputs,
    load_json,
    validate_request,
)


def render_summary(result: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# AUTO-001B — Restricted development controller",
            "",
            "- Trusted GitHub validation: **PASSED**",
            "- VPS target: **development only**",
            "- Preview target: **forbidden / untouched**",
            f"- PR: `#{result['pr_number']}`",
            f"- Exact SHA: `{result['head_sha']}`",
            f"- Profile: `{result['deployment_profile']}`",
            "- Automatic merge: **absent**",
            "",
        ]
    )


def command_validate(args: argparse.Namespace) -> int:
    policy = load_json(Path(args.policy))
    request = load_json(Path(args.request))
    foundation_result = validate_request(request, policy)
    result = {
        "pr_number": foundation_result["pr_number"],
        "head_ref": foundation_result["head_ref"],
        "head_sha": foundation_result["head_sha"],
        "deployment_profile": foundation_result["deployment_profile"],
        "trusted_workflow_sha": foundation_result["trusted_workflow_sha"],
    }
    Path(args.summary).write_text(render_summary(result), encoding="utf-8")
    if args.outputs:
        append_github_outputs(
            Path(args.outputs),
            {key: str(value) for key, value in result.items()},
        )
    print(json.dumps(result, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AUTO-001B trusted request validation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--request", required=True)
    validate_parser.add_argument("--policy", required=True)
    validate_parser.add_argument("--summary", required=True)
    validate_parser.add_argument("--outputs")
    validate_parser.set_defaults(handler=command_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.handler(args))
    except FoundationValidationError as exc:
        print(f"AUTO-001B BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
