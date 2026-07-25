from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")
EXPECTED_READ_PERMISSIONS = {
    "contents": "read",
    "pull-requests": "read",
    "actions": "read",
    "checks": "read",
    "statuses": "read",
}
FORBIDDEN_TRUSTED_WORKFLOW_FRAGMENTS = (
    "secrets.",
    "contents: write",
    "workflows: write",
    "pull-requests: write",
    "issues: write",
    "checks: write",
    "actions: write",
    "statuses: write",
    "deployments: write",
    "id-token: write",
    "actions/download-artifact",
    "workflow_run:",
    "repository_dispatch:",
    "environment:",
    "ssh ",
    "scp ",
    "rsync ",
)


class FoundationValidationError(ValueError):
    """Raised when a trusted controller invariant is not satisfied."""


def load_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise FoundationValidationError(f"Expected JSON object in {path}.")
    return data


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    ).encode("utf-8")


def sha256_hex(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def require_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FoundationValidationError(f"{field} must be a non-empty string.")
    return value.strip()


def require_sha(value: Any, field: str) -> str:
    text = require_string(value, field)
    if not SHA_PATTERN.fullmatch(text):
        raise FoundationValidationError(f"{field} must be a lowercase 40-hex SHA.")
    return text


def require_positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool):
        raise FoundationValidationError(f"{field} must be a positive integer.")
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise FoundationValidationError(f"{field} must be a positive integer.") from exc
    if parsed <= 0:
        raise FoundationValidationError(f"{field} must be a positive integer.")
    return parsed


def validate_policy(policy: dict[str, Any]) -> None:
    if policy.get("schema_version") != 1:
        raise FoundationValidationError("Unsupported foundation policy schema_version.")
    require_string(policy.get("repository"), "policy.repository")
    if require_string(policy.get("base_ref"), "policy.base_ref") != "main":
        raise FoundationValidationError("policy.base_ref must be main.")

    labels = policy.get("allowed_labels")
    if not isinstance(labels, dict) or set(labels.values()) != {"refresh", "rebuild"}:
        raise FoundationValidationError("Policy must map exactly two labels to refresh/rebuild.")
    for label, profile in labels.items():
        require_string(label, "policy.allowed_labels label")
        require_string(profile, f"policy.allowed_labels[{label!r}]")

    permissions = policy.get("allowed_actor_permissions")
    if permissions != ["admin", "maintain", "write"]:
        raise FoundationValidationError(
            "allowed_actor_permissions must be admin, maintain, write in descending order."
        )

    workflows = policy.get("required_workflows")
    if not isinstance(workflows, list) or not workflows:
        raise FoundationValidationError("required_workflows must be a non-empty list.")
    if len(workflows) != len(set(workflows)):
        raise FoundationValidationError("required_workflows must not contain duplicates.")
    for workflow in workflows:
        require_string(workflow, "policy.required_workflows item")

    for key in ("blocked_path_prefixes", "blocked_exact_paths"):
        values = policy.get(key)
        if not isinstance(values, list) or not values:
            raise FoundationValidationError(f"{key} must be a non-empty list.")
        if len(values) != len(set(values)):
            raise FoundationValidationError(f"{key} must not contain duplicates.")
        for item in values:
            require_string(item, f"policy.{key} item")

    if policy.get("manifest_schema_version") != 1:
        raise FoundationValidationError("Unsupported manifest_schema_version.")
    retention = require_positive_int(
        policy.get("artifact_retention_days"), "policy.artifact_retention_days"
    )
    if retention != 14:
        raise FoundationValidationError("AUTO-001A manifest retention must be 14 days.")


def path_is_blocked(path: str, policy: dict[str, Any]) -> bool:
    normalized = path.strip().lstrip("./")
    if normalized in policy["blocked_exact_paths"]:
        return True
    return any(normalized.startswith(prefix) for prefix in policy["blocked_path_prefixes"])


def select_latest_required_run(
    runs: list[dict[str, Any]], workflow_name: str, head_sha: str
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    for run in runs:
        if not isinstance(run, dict):
            continue
        if run.get("name") != workflow_name:
            continue
        if run.get("head_sha") != head_sha:
            continue
        if run.get("event") != "pull_request":
            continue
        candidates.append(run)

    if not candidates:
        raise FoundationValidationError(
            f"Required workflow {workflow_name!r} has no pull_request run for exact head SHA."
        )

    def sort_key(run: dict[str, Any]) -> tuple[int, int]:
        return (
            int(run.get("run_attempt") or 0),
            int(run.get("id") or 0),
        )

    latest = max(candidates, key=sort_key)
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        raise FoundationValidationError(
            f"Latest exact-SHA run for {workflow_name!r} is not completed/success."
        )
    require_positive_int(latest.get("id"), f"workflow run id for {workflow_name}")
    return latest


def validate_request(request: dict[str, Any], policy: dict[str, Any]) -> dict[str, Any]:
    validate_policy(policy)

    event = request.get("event")
    live_pr = request.get("live_pr")
    if not isinstance(event, dict) or not isinstance(live_pr, dict):
        raise FoundationValidationError("request.event and request.live_pr must be objects.")

    repository = require_string(event.get("repository"), "event.repository")
    expected_repository = policy["repository"]
    if repository != expected_repository:
        raise FoundationValidationError("Repository does not match the allowlisted repository.")
    if event.get("action") != "labeled":
        raise FoundationValidationError("Only pull_request_target:labeled is accepted.")

    label = require_string(event.get("label"), "event.label")
    allowed_labels = policy["allowed_labels"]
    if label not in allowed_labels:
        raise FoundationValidationError("Label is not allowlisted for AUTO-001A.")
    profile = allowed_labels[label]

    event_pr_number = require_positive_int(event.get("pr_number"), "event.pr_number")
    live_pr_number = require_positive_int(live_pr.get("number"), "live_pr.number")
    if event_pr_number != live_pr_number:
        raise FoundationValidationError("Event PR number does not match live PR number.")
    if live_pr.get("state") != "open":
        raise FoundationValidationError("Pull request must still be open.")
    if live_pr.get("base_ref") != policy["base_ref"]:
        raise FoundationValidationError("Pull request base must be main.")
    if live_pr.get("head_repo_full_name") != expected_repository:
        raise FoundationValidationError("Fork or cross-repository pull requests are forbidden.")

    event_base_ref = require_string(event.get("base_ref"), "event.base_ref")
    if event_base_ref != live_pr.get("base_ref"):
        raise FoundationValidationError("Event base ref is stale or inconsistent.")
    event_head_repository = require_string(
        event.get("head_repo_full_name"), "event.head_repo_full_name"
    )
    if event_head_repository != live_pr.get("head_repo_full_name"):
        raise FoundationValidationError("Event head repository is stale or inconsistent.")

    event_head_sha = require_sha(event.get("head_sha"), "event.head_sha")
    live_head_sha = require_sha(live_pr.get("head_sha"), "live_pr.head_sha")
    if event_head_sha != live_head_sha:
        raise FoundationValidationError("PR head changed after the label event; request is superseded.")

    head_ref = require_string(live_pr.get("head_ref"), "live_pr.head_ref")
    actor = require_string(event.get("actor"), "event.actor")
    actor_permission = require_string(request.get("actor_permission"), "actor_permission")
    if actor_permission not in policy["allowed_actor_permissions"]:
        raise FoundationValidationError("Actor lacks allowlisted repository write authority.")

    changed_files = request.get("changed_files")
    if not isinstance(changed_files, list):
        raise FoundationValidationError("changed_files must be a list.")
    normalized_files: list[str] = []
    for item in changed_files:
        path = require_string(item, "changed_files item").lstrip("./")
        normalized_files.append(path)
        if path_is_blocked(path, policy):
            raise FoundationValidationError(
                f"PR changes blocked automation/security path: {path}"
            )
    normalized_files = sorted(set(normalized_files))

    workflow_runs = request.get("workflow_runs")
    if not isinstance(workflow_runs, list):
        raise FoundationValidationError("workflow_runs must be a list.")
    verified_workflows: list[dict[str, Any]] = []
    for workflow_name in policy["required_workflows"]:
        run = select_latest_required_run(workflow_runs, workflow_name, live_head_sha)
        verified_workflows.append(
            {
                "name": workflow_name,
                "run_id": require_positive_int(run.get("id"), f"run id for {workflow_name}"),
                "run_attempt": int(run.get("run_attempt") or 1),
                "conclusion": "success",
                "head_sha": live_head_sha,
                "event": "pull_request",
            }
        )

    observed_at = require_string(request.get("observed_at"), "observed_at")
    workflow_run_id = require_positive_int(
        event.get("workflow_run_id"), "event.workflow_run_id"
    )
    workflow_run_attempt = require_positive_int(
        event.get("workflow_run_attempt"), "event.workflow_run_attempt"
    )
    trusted_workflow_sha = require_sha(
        event.get("trusted_workflow_sha"), "event.trusted_workflow_sha"
    )

    files_digest = sha256_hex(("\n".join(normalized_files) + "\n").encode("utf-8"))
    return {
        "schema_version": policy["manifest_schema_version"],
        "state": "VALIDATED_STAGE_A",
        "vps_phase": "BLOCKED",
        "repository": expected_repository,
        "pr_number": live_pr_number,
        "base_ref": policy["base_ref"],
        "head_ref": head_ref,
        "head_sha": live_head_sha,
        "deployment_profile": profile,
        "request_label": label,
        "requested_by": actor,
        "actor_permission": actor_permission,
        "workflow_run_id": workflow_run_id,
        "workflow_run_attempt": workflow_run_attempt,
        "trusted_workflow_sha": trusted_workflow_sha,
        "observed_at": observed_at,
        "changed_files_count": len(normalized_files),
        "changed_files_sha256": files_digest,
        "required_workflows": verified_workflows,
        "vps_side_effects": "NONE_STAGE_A",
    }


def extract_top_level_permissions(workflow_text: str) -> dict[str, str]:
    lines = workflow_text.splitlines()
    start: int | None = None
    for index, line in enumerate(lines):
        if line == "permissions:":
            start = index + 1
            break
    if start is None:
        raise FoundationValidationError("Trusted workflow has no top-level permissions block.")

    permissions: dict[str, str] = {}
    for line in lines[start:]:
        if not line.strip():
            continue
        if not line.startswith("  "):
            break
        match = re.fullmatch(r"  ([a-z-]+): (read|write|none)", line)
        if not match:
            raise FoundationValidationError(
                f"Unexpected top-level permission declaration: {line!r}"
            )
        permissions[match.group(1)] = match.group(2)
    return permissions


def validate_trusted_workflow_text(workflow_text: str, policy: dict[str, Any]) -> None:
    validate_policy(policy)
    if "pull_request_target:" not in workflow_text or "types: [labeled]" not in workflow_text:
        raise FoundationValidationError(
            "Trusted workflow must use pull_request_target with labeled only."
        )
    if "group: eod-vps-development" not in workflow_text:
        raise FoundationValidationError("Trusted workflow concurrency group is missing.")
    if "cancel-in-progress: false" not in workflow_text:
        raise FoundationValidationError("Trusted workflow must queue rather than cancel runs.")
    if "ref: ${{ github.sha }}" not in workflow_text:
        raise FoundationValidationError("Trusted checkout must pin the default-branch event SHA.")
    if "persist-credentials: false" not in workflow_text:
        raise FoundationValidationError("Trusted checkout credentials must not persist.")
    if "vps-stage-a-blocked" not in workflow_text or "BLOCKED" not in workflow_text:
        raise FoundationValidationError("Stage A VPS phase must be deterministically BLOCKED.")

    lowered = workflow_text.lower()
    for fragment in FORBIDDEN_TRUSTED_WORKFLOW_FRAGMENTS:
        if fragment.lower() in lowered:
            raise FoundationValidationError(
                f"Forbidden trusted workflow fragment detected: {fragment}"
            )

    permissions = extract_top_level_permissions(workflow_text)
    if permissions != EXPECTED_READ_PERMISSIONS:
        raise FoundationValidationError(
            f"Effective workflow permissions differ from read-only contract: {permissions}"
        )

    for label in policy["allowed_labels"]:
        if label not in workflow_text:
            raise FoundationValidationError(f"Allowlisted label is missing from workflow: {label}")


def validate_foundation_ci_workflow_text(workflow_text: str) -> None:
    if "pull_request:" not in workflow_text:
        raise FoundationValidationError("Foundation CI must run on pull_request.")
    if "contents: read" not in workflow_text:
        raise FoundationValidationError("Foundation CI must declare contents: read.")
    if re.search(r"^[ ]+[a-z-]+: write$", workflow_text, flags=re.MULTILINE):
        raise FoundationValidationError("Foundation CI must not request write permissions.")
    for fragment in ("secrets.", "ssh ", "scp ", "rsync ", "environment:"):
        if fragment.lower() in workflow_text.lower():
            raise FoundationValidationError(
                f"Foundation CI contains forbidden fragment: {fragment}"
            )


def run_policy_check(root: Path, policy: dict[str, Any]) -> None:
    trusted_path = root / policy["trusted_workflow"]
    ci_path = root / policy["foundation_ci_workflow"]
    validate_trusted_workflow_text(trusted_path.read_text(encoding="utf-8"), policy)
    validate_foundation_ci_workflow_text(ci_path.read_text(encoding="utf-8"))


def render_summary(manifest: dict[str, Any], manifest_sha256: str) -> str:
    workflow_lines = "\n".join(
        f"- `{item['name']}`: success, run `{item['run_id']}`, exact SHA"
        for item in manifest["required_workflows"]
    )
    return f"""# AUTO-001A — Trusted Controller Foundation

## Result

- GitHub request validation: **PASSED**
- VPS phase: **BLOCKED** — Stage B is not authorised
- VPS side effects: **NONE**
- Repository write/approval/merge capability: **ABSENT**

## Exact request

- Repository: `{manifest['repository']}`
- PR: `#{manifest['pr_number']}`
- Branch: `{manifest['head_ref']}`
- Exact current SHA: `{manifest['head_sha']}`
- Profile: `{manifest['deployment_profile']}`
- Actor: `{manifest['requested_by']}` (`{manifest['actor_permission']}`)
- Trusted workflow SHA: `{manifest['trusted_workflow_sha']}`

## Required exact-SHA workflows

{workflow_lines}

## Immutable manifest

- SHA-256: `{manifest_sha256}`
- Changed-file count: `{manifest['changed_files_count']}`
- Changed-file-list SHA-256: `{manifest['changed_files_sha256']}`
- Retention: 14 days

## Effective permissions

```yaml
contents: read
pull-requests: read
actions: read
checks: read
statuses: read
```

No VPS secret, SSH connection, deploy account, forced command, PR artifact, PR checkout or PR code execution is present in Stage A.
"""


def append_github_outputs(path: Path, values: dict[str, str]) -> None:
    with path.open("a", encoding="utf-8") as handle:
        for key, value in values.items():
            if "\n" in value or "\r" in value:
                raise FoundationValidationError(f"Output {key} contains a newline.")
            handle.write(f"{key}={value}\n")


def command_validate(args: argparse.Namespace) -> int:
    policy = load_json(Path(args.policy))
    request = load_json(Path(args.request))
    manifest = validate_request(request, policy)
    manifest_bytes = canonical_json_bytes(manifest)
    manifest_sha256 = sha256_hex(manifest_bytes)

    manifest_path = Path(args.manifest)
    summary_path = Path(args.summary)
    manifest_path.write_bytes(manifest_bytes)
    summary_path.write_text(render_summary(manifest, manifest_sha256), encoding="utf-8")

    if args.outputs:
        append_github_outputs(
            Path(args.outputs),
            {
                "pr_number": str(manifest["pr_number"]),
                "head_ref": manifest["head_ref"],
                "head_sha": manifest["head_sha"],
                "deployment_profile": manifest["deployment_profile"],
                "manifest_sha256": manifest_sha256,
                "vps_state": "BLOCKED",
            },
        )

    print(
        "AUTO-001A request validated: "
        f"PR #{manifest['pr_number']} {manifest['head_sha']} "
        f"profile={manifest['deployment_profile']} vps=BLOCKED"
    )
    return 0


def command_policy_check(args: argparse.Namespace) -> int:
    root = Path(args.root).resolve()
    policy = load_json(root / args.policy)
    run_policy_check(root, policy)
    print("AUTO-001A trusted workflow policy: OK")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AUTO-001A trusted controller foundation")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate", help="Validate a trusted PR request")
    validate_parser.add_argument("--request", required=True)
    validate_parser.add_argument("--policy", required=True)
    validate_parser.add_argument("--manifest", required=True)
    validate_parser.add_argument("--summary", required=True)
    validate_parser.add_argument("--outputs")
    validate_parser.set_defaults(handler=command_validate)

    policy_parser = subparsers.add_parser("policy-check", help="Validate workflow policy")
    policy_parser.add_argument("--root", default=".")
    policy_parser.add_argument("--policy", default=".github/auto001a-foundation.json")
    policy_parser.set_defaults(handler=command_policy_check)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        return int(args.handler(args))
    except FoundationValidationError as exc:
        print(f"AUTO-001A BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
