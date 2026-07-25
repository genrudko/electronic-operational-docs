from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from scripts.automation.auto_001a_foundation import (
    EXPECTED_READ_PERMISSIONS,
    FoundationValidationError,
    canonical_json_bytes,
    extract_top_level_permissions,
    run_policy_check,
    sha256_hex,
    validate_request,
    validate_trusted_workflow_text,
)

HEAD_SHA = "1" * 40
TRUSTED_SHA = "2" * 40


def build_policy() -> dict[str, object]:
    return {
        "schema_version": 1,
        "repository": "genrudko/electronic-operational-docs",
        "base_ref": "main",
        "allowed_labels": {
            "vps-development-refresh": "refresh",
            "vps-development-rebuild": "rebuild",
        },
        "allowed_actor_permissions": ["admin", "maintain", "write"],
        "required_workflows": [
            "EOD CI",
            "EOD Development Stack",
            "EOD Documentation Contract",
            "AUTO-001A Foundation CI",
        ],
        "blocked_path_prefixes": [
            ".github/workflows/",
            "scripts/automation/",
            "deploy/automation/",
        ],
        "blocked_exact_paths": [
            ".github/auto001a-foundation.json",
            "docs/automation/AUTO_001_SECURITY_MODEL.md",
            "docs/automation/AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md",
            "docs/adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md",
            "docs/runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md",
        ],
        "trusted_workflow": ".github/workflows/vps-development.yml",
        "foundation_ci_workflow": ".github/workflows/auto-001a-foundation-ci.yml",
        "manifest_schema_version": 1,
        "artifact_retention_days": 14,
    }


def build_request() -> dict[str, object]:
    workflow_names = build_policy()["required_workflows"]
    assert isinstance(workflow_names, list)
    runs = [
        {
            "id": index + 100,
            "run_attempt": 1,
            "name": name,
            "head_sha": HEAD_SHA,
            "event": "pull_request",
            "status": "completed",
            "conclusion": "success",
        }
        for index, name in enumerate(workflow_names)
    ]
    return {
        "observed_at": "2026-07-25T20:00:00Z",
        "event": {
            "repository": "genrudko/electronic-operational-docs",
            "action": "labeled",
            "label": "vps-development-refresh",
            "actor": "genrudko",
            "pr_number": 11,
            "base_ref": "main",
            "head_sha": HEAD_SHA,
            "head_repo_full_name": "genrudko/electronic-operational-docs",
            "workflow_run_id": 9001,
            "workflow_run_attempt": 1,
            "trusted_workflow_sha": TRUSTED_SHA,
        },
        "live_pr": {
            "number": 11,
            "state": "open",
            "base_ref": "main",
            "head_ref": "feature/example",
            "head_sha": HEAD_SHA,
            "head_repo_full_name": "genrudko/electronic-operational-docs",
        },
        "actor_permission": "admin",
        "changed_files": ["src/apps/example.py", "tests/test_example.py"],
        "workflow_runs": runs,
    }


class RequestValidationTests(unittest.TestCase):
    def assert_blocked(self, request: dict[str, object], message: str) -> None:
        with self.assertRaisesRegex(FoundationValidationError, message):
            validate_request(request, build_policy())

    def test_valid_request_produces_immutable_blocked_manifest(self) -> None:
        request = build_request()
        first = validate_request(request, build_policy())
        second = validate_request(copy.deepcopy(request), build_policy())

        self.assertEqual(first, second)
        self.assertEqual(first["state"], "VALIDATED_STAGE_A")
        self.assertEqual(first["vps_phase"], "BLOCKED")
        self.assertEqual(first["vps_side_effects"], "NONE_STAGE_A")
        self.assertEqual(first["head_sha"], HEAD_SHA)
        self.assertEqual(first["deployment_profile"], "refresh")
        self.assertEqual(
            sha256_hex(canonical_json_bytes(first)),
            sha256_hex(canonical_json_bytes(second)),
        )

    def test_rebuild_label_selects_rebuild_profile(self) -> None:
        request = build_request()
        event = request["event"]
        assert isinstance(event, dict)
        event["label"] = "vps-development-rebuild"
        manifest = validate_request(request, build_policy())
        self.assertEqual(manifest["deployment_profile"], "rebuild")

    def test_wrong_repository_is_blocked(self) -> None:
        request = build_request()
        event = request["event"]
        assert isinstance(event, dict)
        event["repository"] = "other/repository"
        self.assert_blocked(request, "Repository does not match")

    def test_unknown_label_is_blocked(self) -> None:
        request = build_request()
        event = request["event"]
        assert isinstance(event, dict)
        event["label"] = "deploy-anything"
        self.assert_blocked(request, "Label is not allowlisted")

    def test_closed_pr_is_blocked(self) -> None:
        request = build_request()
        live_pr = request["live_pr"]
        assert isinstance(live_pr, dict)
        live_pr["state"] = "closed"
        self.assert_blocked(request, "must still be open")

    def test_non_main_base_is_blocked(self) -> None:
        request = build_request()
        live_pr = request["live_pr"]
        assert isinstance(live_pr, dict)
        live_pr["base_ref"] = "release"
        self.assert_blocked(request, "base must be main")

    def test_fork_head_is_blocked(self) -> None:
        request = build_request()
        live_pr = request["live_pr"]
        assert isinstance(live_pr, dict)
        live_pr["head_repo_full_name"] = "attacker/fork"
        self.assert_blocked(request, "Fork or cross-repository")

    def test_stale_event_sha_is_blocked(self) -> None:
        request = build_request()
        event = request["event"]
        assert isinstance(event, dict)
        event["head_sha"] = "3" * 40
        self.assert_blocked(request, "request is superseded")

    def test_unauthorised_actor_is_blocked(self) -> None:
        request = build_request()
        request["actor_permission"] = "read"
        self.assert_blocked(request, "lacks allowlisted")

    def test_blocked_security_paths_are_rejected(self) -> None:
        blocked_paths = (
            ".github/workflows/evil.yml",
            "scripts/automation/evil.py",
            "deploy/automation/evil.sh",
            ".github/auto001a-foundation.json",
            "docs/automation/AUTO_001_SECURITY_MODEL.md",
        )
        for path in blocked_paths:
            with self.subTest(path=path):
                request = build_request()
                request["changed_files"] = [path]
                self.assert_blocked(request, "blocked automation/security path")

    def test_missing_required_workflow_is_blocked(self) -> None:
        request = build_request()
        runs = request["workflow_runs"]
        assert isinstance(runs, list)
        runs.pop()
        self.assert_blocked(request, "has no exact-SHA run")

    def test_latest_failed_rerun_wins_over_older_success(self) -> None:
        request = build_request()
        runs = request["workflow_runs"]
        assert isinstance(runs, list)
        runs.append(
            {
                "id": 999,
                "run_attempt": 2,
                "name": "EOD CI",
                "head_sha": HEAD_SHA,
                "event": "pull_request",
                "status": "completed",
                "conclusion": "failure",
            }
        )
        self.assert_blocked(request, "is not successful")

    def test_run_for_different_sha_does_not_satisfy_gate(self) -> None:
        request = build_request()
        runs = request["workflow_runs"]
        assert isinstance(runs, list)
        for run in runs:
            assert isinstance(run, dict)
            if run["name"] == "EOD CI":
                run["head_sha"] = "4" * 40
        self.assert_blocked(request, "has no exact-SHA run")


class WorkflowPolicyTests(unittest.TestCase):
    def test_permission_parser_requires_exact_read_only_contract(self) -> None:
        text = """permissions:
  contents: read
  pull-requests: read
  actions: read
  checks: read
  statuses: read

jobs:
  validate:
    runs-on: ubuntu-24.04
"""
        self.assertEqual(
            extract_top_level_permissions(text),
            EXPECTED_READ_PERMISSIONS,
        )

    def test_write_permission_is_rejected(self) -> None:
        policy = build_policy()
        trusted = self._trusted_workflow_text().replace(
            "contents: read",
            "contents: write",
        )
        with self.assertRaisesRegex(FoundationValidationError, "Forbidden"):
            validate_trusted_workflow_text(trusted, policy)

    def test_pr_artifact_download_is_rejected(self) -> None:
        policy = build_policy()
        trusted = self._trusted_workflow_text().replace(
            "actions/upload-artifact@v7",
            "actions/download-artifact@v7",
        )
        with self.assertRaisesRegex(
            FoundationValidationError,
            "download-artifact",
        ):
            validate_trusted_workflow_text(trusted, policy)

    def test_policy_check_reads_repository_files(self) -> None:
        policy = build_policy()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            policy_path = root / ".github/auto001a-foundation.json"
            trusted_path = root / str(policy["trusted_workflow"])
            ci_path = root / str(policy["foundation_ci_workflow"])
            policy_path.parent.mkdir(parents=True)
            trusted_path.parent.mkdir(parents=True, exist_ok=True)
            ci_path.parent.mkdir(parents=True, exist_ok=True)
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            trusted_path.write_text(
                self._trusted_workflow_text(),
                encoding="utf-8",
            )
            ci_path.write_text(
                """name: AUTO-001A Foundation CI
on:
  pull_request:
permissions:
  contents: read
jobs:
  test:
    runs-on: ubuntu-24.04
""",
                encoding="utf-8",
            )
            run_policy_check(root, policy)

    @staticmethod
    def _trusted_workflow_text() -> str:
        return """name: EOD Trusted Development Controller
on:
  pull_request_target:
    types: [labeled]
permissions:
  contents: read
  pull-requests: read
  actions: read
  checks: read
  statuses: read
concurrency:
  group: eod-vps-development
  cancel-in-progress: false
jobs:
  validate:
    runs-on: ubuntu-24.04
    steps:
      - uses: actions/checkout@v6
        with:
          ref: ${{ github.sha }}
          persist-credentials: false
      - uses: actions/upload-artifact@v7
        with:
          name: manifest
          path: manifest.json
  vps-stage-a-blocked:
    runs-on: ubuntu-24.04
    steps:
      - run: echo BLOCKED
# vps-development-refresh
# vps-development-rebuild
"""


if __name__ == "__main__":
    unittest.main()
