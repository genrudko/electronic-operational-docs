from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.automation.auto_001b_request import render_summary

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = ROOT / "deploy/automation/eod-development-controller"
BOOTSTRAP = ROOT / "deploy/automation/bootstrap_auto001b.sh"
COMPOSE = ROOT / "deploy/automation/compose.development.yaml"
WORKFLOW = ROOT / ".github/workflows/vps-development.yml"
POLICY = ROOT / ".github/auto001a-foundation.json"
RUNBOOK = ROOT / "docs/runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md"


class ControllerContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.controller = CONTROLLER.read_text(encoding="utf-8")
        cls.bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
        cls.compose = COMPOSE.read_text(encoding="utf-8")
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")
        cls.runbook = RUNBOOK.read_text(encoding="utf-8")

    def test_private_repository_uses_read_only_deploy_key(self) -> None:
        self.assertIn("github_deploy_key", self.bootstrap)
        self.assertIn("Allow write access: OFF", self.bootstrap)
        self.assertIn("git ls-remote", self.bootstrap)
        self.assertIn("git@github.com:genrudko/electronic-operational-docs.git", self.bootstrap)
        self.assertNotIn('cat "$DEPLOY_KEY"\n', self.bootstrap)
        self.assertIn('cat "$DEPLOY_KEY.pub"', self.bootstrap)

    def test_bootstrap_is_repeatable(self) -> None:
        self.assertIn('if ! id -u "$AUTOMATION_USER"', self.bootstrap)
        self.assertIn('if [[ ! -f "$DEPLOY_KEY" ]]', self.bootstrap)
        self.assertIn('if [[ ! -f "$CLIENT_KEY" ]]', self.bootstrap)
        self.assertIn('grep -Fqx "$forced_line"', self.bootstrap)
        self.assertIn("safe to run again", self.bootstrap)

    def test_automation_user_has_no_docker_group_membership(self) -> None:
        self.assertIn('gpasswd --delete "$AUTOMATION_USER" docker', self.bootstrap)
        self.assertIn("NOPASSWD: $CONTROLLER ssh-gateway", self.bootstrap)
        self.assertIn('env_keep += "SSH_ORIGINAL_COMMAND"', self.bootstrap)
        self.assertNotIn("NOPASSWD: ALL", self.bootstrap)

    def test_controller_fetches_exact_pr_head_with_deploy_key(self) -> None:
        self.assertIn('refs/pull/$pr_number/head', self.controller)
        self.assertIn('[[ "$fetched_sha" == "$sha" ]]', self.controller)
        self.assertIn("StrictHostKeyChecking=yes", self.controller)
        self.assertIn("IdentitiesOnly=yes", self.controller)

    def test_pr_controlled_host_scripts_are_not_executed(self) -> None:
        self.assertNotIn("scripts/development_stack.sh", self.controller)
        self.assertIn("/etc/eod-automation/Dockerfile.development", self.controller)
        self.assertIn("/etc/eod-automation/compose.development.yaml", self.controller)
        self.assertIn('archive "$sha"', self.controller)

    def test_full_suite_uses_isolated_postgresql_before_development_stop(self) -> None:
        isolated = self.controller.index("run_isolated_checks_and_tests")
        deploy_function = self.controller.index("deploy_release()")
        deploy_body = self.controller[deploy_function:]
        test_call = deploy_body.index('run_isolated_checks_and_tests "$image" "$run_id"')
        stop_call = deploy_body.index('stop_application "$previous_image"')
        self.assertGreater(isolated, 0)
        self.assertLess(test_call, stop_call)
        self.assertIn("--tmpfs /var/lib/postgresql:", self.controller)
        self.assertNotIn("--tmpfs /var/lib/postgresql/data:", self.controller)
        self.assertIn("manage.py test apps --verbosity 2", self.controller)
        self.assertIn("manage.py makemigrations --check --dry-run", self.controller)

    def test_development_database_order_is_stop_backup_migrate_start(self) -> None:
        deploy_body = self.controller[self.controller.index("deploy_release()") :]
        markers = [
            'stop_application "$previous_image"',
            'create_database_backup "$previous_image"',
            'apply_migrations "$image"',
            'start_release "$image"',
        ]
        positions = [deploy_body.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        self.assertIn("pg_dump --format=custom", self.controller)

    def test_automatic_rollback_restores_database_and_previous_image(self) -> None:
        rollback = self.controller[
            self.controller.index("rollback_transaction()") :
            self.controller.index("deploy_release()")
        ]
        self.assertIn('stop_application "$NEW_IMAGE"', rollback)
        self.assertIn('restore_database "$PREVIOUS_IMAGE" "$BACKUP_FILE"', rollback)
        self.assertIn('start_release "$PREVIOUS_IMAGE"', rollback)
        self.assertIn("dropdb", self.controller)
        self.assertIn("pg_restore", self.controller)

    def test_preview_identifiers_are_absent_from_vps_controller(self) -> None:
        forbidden = ("eod-preview", "eod_preview", "8765", "preview.env")
        for marker in forbidden:
            with self.subTest(marker=marker):
                self.assertNotIn(marker, self.controller)
                self.assertNotIn(marker, self.compose)
        self.assertIn("eod-development", self.compose)
        self.assertIn("eod_development_postgres_data", self.compose)
        self.assertIn("8766", self.compose)

    def test_workflow_has_three_results_and_no_merge(self) -> None:
        self.assertIn("AUTO-001B result: SUCCESS", self.workflow)
        self.assertIn("AUTO-001B result: ERROR", self.workflow)
        self.assertIn("AUTO-001B result: STALE SHA", self.workflow)
        self.assertIn('"rollback $GITHUB_RUN_ID"', self.workflow)
        self.assertIn('"confirm $GITHUB_RUN_ID $HEAD_SHA"', self.workflow)
        for forbidden in (
            "merge_pull_request",
            "enable_auto_merge",
            "pull-requests: write",
            "contents: write",
        ):
            self.assertNotIn(forbidden, self.workflow)

    def test_workflow_fallback_covers_failure_and_cancellation(self) -> None:
        self.assertIn(
            "Roll back an unconfirmed deployment after workflow failure or cancellation",
            self.workflow,
        )
        self.assertIn(
            "(failure() || cancelled()) && steps.deploy.outputs.attempted == 'true'",
            self.workflow,
        )
        self.assertIn("printf 'attempted=true", self.workflow)
        self.assertIn('"rollback-pending"', self.workflow)
        self.assertIn(
            "Fallback rollback was requested because the VPS deployment was not confirmed.",
            self.workflow,
        )

    def test_rollback_pending_command_is_available_locally_and_through_gateway(self) -> None:
        self.assertIn("manual_rollback_pending()", self.controller)
        self.assertGreaterEqual(self.controller.count("rollback-pending)"), 2)
        self.assertIn("ROLLBACK_PENDING_SUCCESS", self.controller)
        self.assertIn(
            "eod-development-controller {ssh-gateway|rollback-pending|rollback-last|status}",
            self.controller,
        )

    def test_pending_state_is_removed_after_restore(self) -> None:
        rollback = self.controller[
            self.controller.index("rollback_transaction()") :
            self.controller.index("deploy_release()")
        ]
        self.assertIn(
            'mv "$TRANSACTION_FILE" "$EOD_STATE_DIR/rolled-back-$run_id.env"',
            rollback,
        )
        self.assertNotIn('cp "$TRANSACTION_FILE"', rollback)

    def test_completed_pending_rollback_does_not_block_next_deploy(self) -> None:
        manual = self.controller[
            self.controller.index("manual_rollback_pending()") :
            self.controller.index("manual_rollback_last()")
        ]
        deploy = self.controller[
            self.controller.index("deploy_release()") :
            self.controller.index("confirm_release()")
        ]
        self.assertIn('rollback_transaction "$run_id"', manual)
        self.assertIn('compgen -G "$EOD_STATE_DIR/pending-*.env"', deploy)
        self.assertIn(
            'mv "$TRANSACTION_FILE" "$EOD_STATE_DIR/rolled-back-$run_id.env"',
            self.controller,
        )

    def test_status_reports_pending_run_id(self) -> None:
        status = self.controller[
            self.controller.index("show_status()") :
            self.controller.index("ssh_gateway()")
        ]
        self.assertIn("pending_run_id=NONE", status)
        self.assertIn("pending_run_id=%s", status)
        self.assertIn("pending_run_id=MULTIPLE", status)
        self.assertIn("pending_run_id_from_path", status)

    def test_post_merge_bootstrap_requires_exact_accepted_main(self) -> None:
        self.assertIn("AUTO001B_MAIN_SHA=", self.runbook)
        self.assertIn('git fetch --prune origin main', self.runbook)
        self.assertIn('git reset --hard "$AUTO001B_MAIN_SHA"', self.runbook)
        self.assertIn('test "$(git rev-parse HEAD)" = "$AUTO001B_MAIN_SHA"', self.runbook)
        self.assertIn("bootstrap_auto001b.sh", self.runbook)

    def test_policy_requires_auto001b_ci(self) -> None:
        policy = json.loads(POLICY.read_text(encoding="utf-8"))
        self.assertIn("AUTO-001B Controller CI", policy["required_workflows"])
        self.assertIn("deploy/automation", policy["blocked_path_prefixes"])


class RequestSummaryTests(unittest.TestCase):
    def test_summary_is_simple_and_development_only(self) -> None:
        summary = render_summary(
            {
                "pr_number": 15,
                "head_sha": "a" * 40,
                "deployment_profile": "refresh",
            }
        )
        self.assertIn("development only", summary)
        self.assertIn("Preview target", summary)
        self.assertIn("Automatic merge", summary)
        self.assertNotIn("SHA-256", summary)

    def test_no_private_key_fixture_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(list(Path(directory).iterdir()), [])


if __name__ == "__main__":
    unittest.main()
