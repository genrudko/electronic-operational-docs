from __future__ import annotations

import argparse
import json
import re
from pathlib import Path, PurePosixPath
from typing import Any

COMMAND_PATTERN = re.compile(r"/eod-hot-refresh ([0-9a-f]{40})")
ALLOWED_REPOSITORY = "genrudko/electronic-operational-docs"
ALLOWED_PERMISSIONS = {"write", "admin"}
ALLOWED_STATUSES = {"added", "modified"}
ALLOWED_PREFIXES = ("src/templates/", "src/static/")
SAFE_PATH_PATTERN = re.compile(r"^[A-Za-z0-9._/-]+$")


class HotRefreshValidationError(ValueError):
    """Raised when a DEV-FAST-001 request violates the trusted V1 contract."""


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise HotRefreshValidationError(f"{field} must be a non-empty string.")
    return value


def require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise HotRefreshValidationError(f"{field} must be a positive integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise HotRefreshValidationError(f"{field} must be a positive integer.") from exc
    if parsed <= 0:
        raise HotRefreshValidationError(f"{field} must be a positive integer.")
    return parsed


def parse_command(body: Any) -> str:
    text = require_string(body, "event.comment_body")
    match = COMMAND_PATTERN.fullmatch(text)
    if match is None:
        raise HotRefreshValidationError(
            "Comment must exactly match '/eod-hot-refresh <lowercase-40-hex-sha>'."
        )
    return match.group(1)


def normalize_allowed_path(value: Any, field: str = "changed file path") -> str:
    path = require_string(value, field)
    if not SAFE_PATH_PATTERN.fullmatch(path):
        raise HotRefreshValidationError(f"{field} contains unsupported characters.")
    if path.startswith("/") or "\\" in path or "\x00" in path:
        raise HotRefreshValidationError(f"{field} is not a safe repository path.")
    pure = PurePosixPath(path)
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise HotRefreshValidationError(f"{field} is not canonical.")
    normalized = pure.as_posix()
    if normalized != path:
        raise HotRefreshValidationError(f"{field} is not canonical.")
    if not path.startswith(ALLOWED_PREFIXES):
        raise HotRefreshValidationError(f"Path is outside the V1 presentation allowlist: {path}")
    if path in {"src/templates/", "src/static/"}:
        raise HotRefreshValidationError(f"Path must identify a file: {path}")
    return path


def validate_request(request: dict[str, Any]) -> dict[str, Any]:
    event = request.get("event")
    live_pr = request.get("live_pr")
    if not isinstance(event, dict) or not isinstance(live_pr, dict):
        raise HotRefreshValidationError("request.event and request.live_pr must be objects.")

    repository = require_string(event.get("repository"), "event.repository")
    if repository != ALLOWED_REPOSITORY:
        raise HotRefreshValidationError("Repository does not match the trusted repository.")
    if event.get("action") != "created":
        raise HotRefreshValidationError("Only issue_comment:created is accepted.")
    if event.get("is_pull_request") is not True:
        raise HotRefreshValidationError("The comment must belong to a pull request.")

    command_sha = parse_command(event.get("comment_body"))
    event_number = require_positive_int(event.get("pr_number"), "event.pr_number")
    live_number = require_positive_int(live_pr.get("number"), "live_pr.number")
    if event_number != live_number:
        raise HotRefreshValidationError("Event PR number does not match live PR number.")
    if live_pr.get("state") != "open":
        raise HotRefreshValidationError("Pull request must still be open.")
    if live_pr.get("base_ref") != "main":
        raise HotRefreshValidationError("Pull request base must be main.")
    if live_pr.get("head_repo_full_name") != ALLOWED_REPOSITORY:
        raise HotRefreshValidationError("Fork or cross-repository pull requests are forbidden.")

    live_sha = require_string(live_pr.get("head_sha"), "live_pr.head_sha")
    if not re.fullmatch(r"[0-9a-f]{40}", live_sha):
        raise HotRefreshValidationError("live_pr.head_sha must be a lowercase 40-hex SHA.")
    if command_sha != live_sha:
        raise HotRefreshValidationError("Command SHA does not match the live PR head.")

    actor = require_string(event.get("actor"), "event.actor")
    permission = require_string(request.get("actor_permission"), "actor_permission")
    if permission not in ALLOWED_PERMISSIONS:
        raise HotRefreshValidationError("Actor lacks write/admin repository permission.")

    changed_files = request.get("changed_files")
    if not isinstance(changed_files, list) or not changed_files:
        raise HotRefreshValidationError("changed_files must be a non-empty list.")

    normalized_paths: list[str] = []
    for item in changed_files:
        if not isinstance(item, dict):
            raise HotRefreshValidationError("Each changed_files item must be an object.")
        status = require_string(item.get("status"), "changed_files item.status")
        if status not in ALLOWED_STATUSES:
            raise HotRefreshValidationError(
                f"Only added/modified files are allowed in V1; got {status}."
            )
        if item.get("previous_filename") is not None:
            raise HotRefreshValidationError("Renames and copies are forbidden in V1.")
        normalized_paths.append(normalize_allowed_path(item.get("filename")))

    unique_paths = sorted(set(normalized_paths))
    if len(unique_paths) != len(normalized_paths):
        raise HotRefreshValidationError("Changed file list contains duplicate paths.")

    return {
        "pr_number": live_number,
        "head_sha": live_sha,
        "requested_by": actor,
        "actor_permission": permission,
        "changed_files_count": len(unique_paths),
        "changed_files": unique_paths,
    }


def append_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise HotRefreshValidationError(f"Output {key} contains a newline.")
            handle.write(f"{key}={value}\n")


def render_summary(result: dict[str, Any]) -> str:
    paths = "\n".join(f"- `{path}`" for path in result["changed_files"])
    return "\n".join(
        [
            "# DEV-FAST-001 — Trusted hot refresh request",
            "",
            "- Trusted GitHub validation: **PASSED**",
            f"- PR: `#{result['pr_number']}`",
            f"- Exact live head: `{result['head_sha']}`",
            f"- Actor: `{result['requested_by']}` (`{result['actor_permission']}`)",
            "- Scope: **presentation-only / added or modified regular files**",
            "- Database operations: **forbidden**",
            "- Preview: **untouched**",
            "- Automatic merge: **absent**",
            "",
            "## Requested files",
            "",
            paths,
            "",
        ]
    )


def command_validate(args: argparse.Namespace) -> int:
    request = json.loads(Path(args.request).read_text(encoding="utf-8"))
    if not isinstance(request, dict):
        raise HotRefreshValidationError("Request JSON must be an object.")
    result = validate_request(request)
    Path(args.summary).write_text(render_summary(result), encoding="utf-8")
    if args.outputs:
        append_outputs(
            Path(args.outputs),
            {
                "pr_number": str(result["pr_number"]),
                "head_sha": result["head_sha"],
                "requested_by": result["requested_by"],
                "changed_files_count": str(result["changed_files_count"]),
            },
        )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DEV-FAST-001 trusted hot refresh validation")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--request", required=True)
    validate_parser.add_argument("--summary", required=True)
    validate_parser.add_argument("--outputs")
    validate_parser.set_defaults(handler=command_validate)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.handler(args))
    except (HotRefreshValidationError, json.JSONDecodeError) as exc:
        print(f"DEV-FAST-001 BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
