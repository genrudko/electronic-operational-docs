from __future__ import annotations

import argparse
import fnmatch
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path, PurePosixPath
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RISK_ORDER = {
    "DOCS": 0,
    "PRESENTATION": 1,
    "APP_LOGIC": 2,
    "SCHEMA_DATA": 3,
    "SECURITY_INFRA": 4,
}
STATUSES = {"added", "modified", "removed", "renamed"}
HOT_PREFIXES = ("src/templates/", "src/static/")
INFRA_PREFIXES = (".github/", "deploy/", "scripts/automation/", "infra/")
INFRA_FILES = {
    "Dockerfile",
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
}
SCHEMA_MARKERS = ("/migrations/", "/fixtures/", "/seed/", "/imports/")
FINAL_TRUSTED_PREFIXES = ("requirements/", ".github/", "deploy/", "infra/")
FINAL_TRUSTED_FILES = {
    "Dockerfile",
    "compose.yaml",
    "compose.yml",
    "docker-compose.yaml",
    "docker-compose.yml",
    "compose.development.yaml",
    "compose.preview.yaml",
    "compose.production.yaml",
    "pyproject.toml",
}
LOCAL_RUNTIME_FILES = {"manage.py"}


class PreflightError(ValueError):
    pass


@dataclass(frozen=True)
class Change:
    path: str
    status: str


def text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PreflightError(f"{field} must be a non-empty string")
    return value.strip()


def sha(value: Any, field: str, optional: bool = False) -> str | None:
    if value is None and optional:
        return None
    result = text(value, field)
    if not SHA_RE.fullmatch(result):
        raise PreflightError(f"{field} must be lowercase 40-hex")
    return result


def path(value: Any, field: str) -> str:
    result = text(value, field)
    if result.startswith("/") or "\\" in result or "\x00" in result:
        raise PreflightError(f"unsafe path: {result}")
    pure = PurePosixPath(result)
    if any(part in {"", ".", ".."} for part in pure.parts):
        raise PreflightError(f"non-canonical path: {result}")
    return pure.as_posix()


def changes(value: Any) -> tuple[Change, ...]:
    if not isinstance(value, list) or not value:
        raise PreflightError("changed_files must be a non-empty list")
    result: list[Change] = []
    seen: set[str] = set()
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise PreflightError(f"changed_files[{index}] must be an object")
        item_path = path(item.get("path"), f"changed_files[{index}].path")
        status = text(item.get("status"), f"changed_files[{index}].status")
        if status not in STATUSES:
            raise PreflightError(f"unsupported status: {status}")
        if item_path in seen:
            raise PreflightError(f"duplicate path: {item_path}")
        seen.add(item_path)
        result.append(Change(item_path, status))
    return tuple(sorted(result, key=lambda item: item.path))


def profile(item_path: str) -> str:
    if item_path.startswith(("tests/process/", "tests/automation/")):
        return "SECURITY_INFRA"
    if item_path.startswith(("tests/browser_", "tests/presentation/", "tests/ux/")):
        return "PRESENTATION"
    if item_path.startswith(INFRA_PREFIXES) or item_path in INFRA_FILES:
        return "SECURITY_INFRA"
    wrapped = f"/{item_path}"
    if any(marker in wrapped for marker in SCHEMA_MARKERS):
        return "SCHEMA_DATA"
    if item_path.endswith("/models.py") or item_path == "src/models.py":
        return "SCHEMA_DATA"
    if item_path.startswith(HOT_PREFIXES):
        return "PRESENTATION"
    if item_path.startswith(("src/", "tests/")):
        return "APP_LOGIC"
    if item_path.startswith("docs/") or item_path in {"README.md", "AGENTS.md"}:
        return "DOCS"
    return "SECURITY_INFRA"


def match_any(item_path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatchcase(item_path, pattern) for pattern in patterns)


def validate_scope(items: tuple[Change, ...], manifest: dict[str, Any]) -> None:
    allowed = manifest.get("allowed_paths", [])
    forbidden = manifest.get("forbidden_paths", [])
    if not isinstance(allowed, list) or not isinstance(forbidden, list):
        raise PreflightError("allowed_paths and forbidden_paths must be lists")
    for item in items:
        if allowed and not match_any(item.path, allowed):
            raise PreflightError(f"outside allowed_paths: {item.path}")
        if forbidden and match_any(item.path, forbidden):
            raise PreflightError(f"matches forbidden_paths: {item.path}")


def direct_main_exception(
    items: tuple[Change, ...], manifest: dict[str, Any], mode: str
) -> str | None:
    if mode != "direct_main":
        return None
    non_docs = [
        item.path
        for item in items
        if not (item.path.startswith("docs/") or item.path in {"README.md", "AGENTS.md"})
    ]
    if not non_docs:
        return None
    exception = manifest.get("direct_main_exception")
    if not isinstance(exception, dict):
        raise PreflightError("non-doc direct_main requires direct_main_exception")
    exception_id = text(exception.get("id"), "direct_main_exception.id")
    prefixes = exception.get("allowed_prefixes")
    if not isinstance(prefixes, list) or not prefixes:
        raise PreflightError("direct_main_exception.allowed_prefixes is required")
    normalized: list[str] = []
    for value in prefixes:
        prefix = text(value, "direct_main_exception.allowed_prefix")
        if not prefix.endswith("/"):
            raise PreflightError("direct_main exception prefixes must end with '/'")
        path(prefix[:-1], "direct_main_exception.allowed_prefix")
        normalized.append(prefix)
    for item_path in non_docs:
        if not item_path.startswith(tuple(normalized)):
            raise PreflightError(f"direct_main exception does not cover {item_path}")
    return exception_id


def checks(risk: str, change_class: str, final: bool) -> dict[str, list[str]]:
    fast = ["git diff --check", "path/protected-boundary validation"]
    candidate: list[str] = []
    final_checks = [
        "final gate now"
        if final
        else "defer exact-head GitHub gate until accepted ready push"
    ]
    if risk == "DOCS":
        fast += ["documentation contract", "links/format/consistency"]
        final_checks += ["documentation gate"]
    elif risk == "PRESENTATION":
        fast += ["CSS/JS/template syntax", "focused source-contract tests"]
        candidate += ["targeted browser states on the VPS-local candidate"]
        final_checks += [
            "one full exact-head GitHub gate after ready push",
            "trusted development verification on the ready pushed head",
            "desktop/mobile user acceptance",
        ]
    elif risk == "APP_LOGIC":
        fast += ["Ruff/compile", "Django check", "focused tests", "migration check"]
        candidate += ["application smoke on the VPS-local candidate"]
        final_checks += [
            "full PostgreSQL suite on VPS before ready push",
            "required exact-head GitHub workflows once after ready push",
            "trusted development verification on the ready pushed head",
        ]
    elif risk == "SCHEMA_DATA":
        fast += ["migration consistency", "rollback plan"]
        candidate += ["SQLite migration and application smoke on the VPS-local candidate"]
        final_checks += [
            "PostgreSQL migration/data verification before ready push",
            "backup/rollback evidence",
            "required exact-head GitHub workflows once after ready push",
            "trusted development verification on the ready pushed head",
        ]
    else:
        fast += ["syntax", "dedicated self-tests", "security/protected-path guard"]
        final_checks += [
            "container/build verification",
            "profile-specific exact-head GitHub gate after ready push",
            "trusted runtime verification on the ready pushed head",
        ]
    if change_class == "MICRO":
        candidate.insert(0, "no full suite before user feedback")
    if change_class == "SYSTEM":
        fast.append("rollback/failure-mode review")
    return {"fast": fast, "candidate": candidate, "final": final_checks}


def is_source_test_path(item_path: str) -> bool:
    pure = PurePosixPath(item_path)
    return (
        "/tests/" in f"/{item_path}/"
        or pure.name.startswith("test_")
        or pure.name == "tests.py"
    )


def candidate_delivery(items: tuple[Change, ...], mode: str, risk: str) -> str:
    if mode == "direct_main" or risk == "DOCS":
        return "NONE"
    paths = [item.path for item in items]
    if any(
        item_path in FINAL_TRUSTED_FILES
        or item_path.startswith(FINAL_TRUSTED_PREFIXES)
        for item_path in paths
    ):
        return "FINAL_TRUSTED_ONLY"
    if any(
        item_path in LOCAL_RUNTIME_FILES
        or (item_path.startswith("src/") and not is_source_test_path(item_path))
        for item_path in paths
    ):
        return "VPS_LOCAL_CANDIDATE"
    return "NONE"


def build_plan(manifest: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(manifest, dict):
        raise PreflightError("manifest must be an object")
    repository = text(manifest.get("repository"), "repository")
    if repository.count("/") != 1:
        raise PreflightError("repository must be owner/name")
    base_sha = sha(manifest.get("base_sha"), "base_sha")
    head_sha = sha(manifest.get("head_sha"), "head_sha", optional=True)
    purpose = text(manifest.get("purpose"), "purpose")
    mode = manifest.get("mode", "pull_request")
    if mode not in {"pull_request", "direct_main"}:
        raise PreflightError("mode must be pull_request or direct_main")
    items = changes(manifest.get("changed_files"))
    validate_scope(items, manifest)
    exception_id = direct_main_exception(items, manifest, mode)

    risks = sorted({profile(item.path) for item in items}, key=RISK_ORDER.get)
    risk = max(risks, key=RISK_ORDER.get)
    statuses = {item.status for item in items}
    final_candidate = bool(manifest.get("final_candidate", False))
    if (
        risk in {"SCHEMA_DATA", "SECURITY_INFRA"}
        or statuses & {"removed", "renamed"}
        or len(items) > 12
        or len(risks) > 2
    ):
        change_class = "SYSTEM"
    elif (
        len(items) <= 3
        and statuses <= {"added", "modified"}
        and len(risks) == 1
        and risk in {"DOCS", "PRESENTATION"}
        and not final_candidate
    ):
        change_class = "MICRO"
    else:
        change_class = "STANDARD"

    deployment = candidate_delivery(items, mode, risk)
    selected_checks = checks(risk, change_class, final_candidate)
    if deployment == "VPS_LOCAL_CANDIDATE":
        selected_checks["candidate"].insert(
            0, "scripts/vps_candidate.sh verify [focused_test_label ...]"
        )
        selected_checks["candidate"].insert(
            1, "ephemeral health/browser evidence on 127.0.0.1:18766"
        )
    elif deployment == "FINAL_TRUSTED_ONLY":
        selected_checks["final"].insert(
            1, "container/build exact-head GitHub and trusted runtime verification after ready push"
        )

    if risk != "PRESENTATION":
        browser = "NOT_APPLICABLE"
    elif final_candidate:
        browser = "FULL_MATRIX_ONCE"
    elif change_class == "MICRO":
        browser = "TARGETED_AFFECTED_STATES_ONLY"
    else:
        browser = "TARGETED_THEN_FULL_ON_FINAL_HEAD"

    return {
        "repository": repository,
        "base_sha": base_sha,
        "head_sha": head_sha,
        "purpose": purpose,
        "mode": mode,
        "change_class": change_class,
        "risk_profile": risk,
        "risk_profiles_seen": risks,
        "changed_files": [asdict(item) for item in items],
        "deployment": deployment,
        "checks": selected_checks,
        "browser_evidence": browser,
        "retry_policy": [
            "extract primary cause before retrying code/test failures",
            "retry one failed job only for a proven infrastructure timeout",
            "a second identical timeout is a blocker",
            "new working-tree changes invalidate local candidate evidence",
            "do not push intermediate repair states merely to obtain candidate evidence",
        ],
        "publication_policy": [
            "VPS working tree is volatile candidate state, not canonical history",
            "ready push only after local checks, candidate health/browser evidence and acceptance",
            "run exact-head GitHub gates once for the ready pushed candidate",
        ],
        "timeouts_minutes": {
            "preflight": 2,
            "focused_checks": 10,
            "vps_local_candidate": 15,
            "final_trusted_development": 35,
        },
        "success_evidence": (
            "pre-push: VPS-local candidate checks + health/browser evidence; "
            "after ready push: exact-head GitHub and trusted runtime evidence"
        ),
        "direct_main_exception": exception_id,
    }


def markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# EOD work-item preflight",
        "",
        f"- Purpose: {plan['purpose']}",
        f"- Base SHA: `{plan['base_sha']}`",
        f"- Class: **{plan['change_class']}**",
        f"- Risk: **{plan['risk_profile']}**",
        f"- Deployment: **{plan['deployment']}**",
        f"- Browser evidence: **{plan['browser_evidence']}**",
        "",
        "## Changed files",
        "",
    ]
    lines += [
        f"- `{item['status']}` `{item['path']}`" for item in plan["changed_files"]
    ]
    for section in ("fast", "candidate", "final"):
        lines += ["", f"## {section.title()} checks", ""]
        lines += [f"- {item}" for item in plan["checks"][section]]
    return "\n".join(lines) + "\n"


def handoff(manifest: dict[str, Any], plan: dict[str, Any]) -> str:
    acceptance = manifest.get("acceptance", [])
    return "\n".join(
        [
            f"# Task: {plan['purpose']}",
            "",
            f"- Repository: `{plan['repository']}`",
            f"- Starting SHA: `{plan['base_sha']}`",
            f"- Change class: `{plan['change_class']}`",
            f"- Risk profile: `{plan['risk_profile']}`",
            f"- Delivery: `{plan['deployment']}`",
            "",
            "## Allowed paths",
            *[f"- `{item}`" for item in manifest.get("allowed_paths", [])],
            "",
            "## Forbidden paths",
            *[f"- `{item}`" for item in manifest.get("forbidden_paths", [])],
            "",
            "## Acceptance",
            *[f"- {item}" for item in acceptance],
            "",
            "Return STARTING SHA, FINAL SHA, CHANGED FILES, CHECKS, "
            "DEPLOYMENT, LIVE SHA, ROLLBACK, PREVIEW and MERGE.",
            "Do not claim success without exact evidence.",
            "",
        ]
    )


def write(path_value: str | None, content: str) -> None:
    if path_value:
        target = Path(path_value)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")


def self_test() -> None:
    micro = build_plan(
        {
            "repository": "genrudko/electronic-operational-docs",
            "base_sha": "a" * 40,
            "purpose": "CSS repair",
            "changed_files": [
                {"path": "src/static/system/theme.css", "status": "modified"}
            ],
        }
    )
    assert micro["change_class"] == "MICRO"
    assert micro["deployment"] == "VPS_LOCAL_CANDIDATE"
    try:
        build_plan(
            {
                "repository": "genrudko/electronic-operational-docs",
                "base_sha": "b" * 40,
                "purpose": "unsafe",
                "mode": "direct_main",
                "changed_files": [{"path": "src/app.py", "status": "modified"}],
            }
        )
    except PreflightError:
        pass
    else:
        raise AssertionError("direct_main guard failed")


def main() -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)
    classify = sub.add_parser("classify")
    classify.add_argument("--manifest", required=True)
    classify.add_argument("--json-out")
    classify.add_argument("--markdown-out")
    classify.add_argument("--handoff-out")
    sub.add_parser("self-test")
    args = parser.parse_args()
    try:
        if args.command == "self-test":
            self_test()
            print("work_item_preflight self-test: OK")
            return 0
        manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
        plan = build_plan(manifest)
        payload = json.dumps(plan, ensure_ascii=False, indent=2) + "\n"
        write(args.json_out, payload)
        write(args.markdown_out, markdown(plan))
        write(args.handoff_out, handoff(manifest, plan))
        if not any((args.json_out, args.markdown_out, args.handoff_out)):
            print(payload, end="")
        return 0
    except (PreflightError, OSError, json.JSONDecodeError) as exc:
        print(f"PROCESS PREFLIGHT BLOCKED: {exc}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
