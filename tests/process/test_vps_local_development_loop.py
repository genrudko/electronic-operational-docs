from __future__ import annotations

import os
import subprocess
import unittest
from pathlib import Path

from scripts.automation.work_item_preflight import build_plan

ROOT = Path(__file__).resolve().parents[2]


class VPSLocalDevelopmentLoopTests(unittest.TestCase):
    def plan(self, path: str, *, status: str = "modified") -> dict:
        return build_plan(
            {
                "repository": "genrudko/electronic-operational-docs",
                "base_sha": "a" * 40,
                "purpose": "VPS-local candidate",
                "changed_files": [{"path": path, "status": status}],
            }
        )

    def test_runtime_source_uses_unprivileged_local_candidate(self) -> None:
        for path in (
            "src/static/system/theme.css",
            "src/templates/base.html",
            "src/apps/system/views.py",
        ):
            with self.subTest(path=path):
                plan = self.plan(path)
                self.assertEqual(plan["deployment"], "VPS_LOCAL_CANDIDATE")
                candidate = "\n".join(plan["checks"]["candidate"])
                self.assertIn("scripts/vps_candidate.sh verify", candidate)
                self.assertIn("127.0.0.1:18766", candidate)
                self.assertNotIn("GitHub", candidate)
                self.assertNotIn("trusted exact-head", candidate.lower())

    def test_source_tests_and_docs_need_no_runtime_candidate(self) -> None:
        for path in (
            "src/apps/system/tests/test_system.py",
            "src/apps/equipment_defects/test_source_contract.py",
            "docs/process/DEVELOPMENT_WORKFLOW.md",
        ):
            with self.subTest(path=path):
                self.assertEqual(self.plan(path)["deployment"], "NONE")

    def test_schema_candidate_keeps_postgresql_and_exact_head_final_gates(self) -> None:
        plan = self.plan("src/apps/example/migrations/0002_add_field.py")
        self.assertEqual(plan["deployment"], "VPS_LOCAL_CANDIDATE")
        final = "\n".join(plan["checks"]["final"])
        self.assertIn("PostgreSQL", final)
        self.assertIn("ready push", final)
        self.assertIn("exact-head GitHub", final)

    def test_build_inputs_are_not_claimed_by_sqlite_candidate(self) -> None:
        for path in ("Dockerfile", "compose.development.yaml", "requirements/locks/runtime.txt"):
            with self.subTest(path=path):
                plan = self.plan(path)
                self.assertEqual(plan["deployment"], "FINAL_TRUSTED_ONLY")
                final = "\n".join(plan["checks"]["final"])
                self.assertIn("container", final.lower())
                self.assertIn("exact-head GitHub", final)

    def test_candidate_harness_is_unprivileged_locked_and_ephemeral(self) -> None:
        script = (ROOT / "scripts/vps_candidate.sh").read_text(encoding="utf-8")
        self.assertIn('DEFAULT_PORT="18766"', script)
        self.assertIn("requirements/locks/browser.txt", script)
        self.assertIn("uv pip sync", script)
        self.assertIn("--require-hashes", script)
        self.assertIn("EOD_ALLOW_SQLITE_PATH_OVERRIDE=1", script)
        self.assertIn("runserver", script)
        self.assertIn("playwright.sync_api", script)
        self.assertIn("with-server", script)
        self.assertNotIn("sudo ", script)
        self.assertNotIn("docker ", script)
        self.assertNotIn("github", script.lower())

    def test_candidate_harness_does_not_require_home_environment(self) -> None:
        env = os.environ.copy()
        env.pop("HOME", None)
        result = subprocess.run(
            ["bash", str(ROOT / "scripts/vps_candidate.sh"), "--help"],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Usage:", result.stdout)

    def test_candidate_harness_reuses_unprivileged_browser_runtime_libs(self) -> None:
        script = (ROOT / "scripts/vps_candidate.sh").read_text(encoding="utf-8")
        self.assertIn("EOD_VPS_CANDIDATE_CHROMIUM_LIBS", script)
        self.assertIn("runtime-libs/usr/lib/x86_64-linux-gnu", script)
        self.assertIn("LD_LIBRARY_PATH", script)

    def test_candidate_harness_reuses_existing_browser_without_download(self) -> None:
        script = (ROOT / "scripts/vps_candidate.sh").read_text(encoding="utf-8")
        self.assertIn("EOD_VPS_CANDIDATE_CHROMIUM", script)
        self.assertIn("chrome-cft/chrome-linux64/chrome", script)
        self.assertIn("chromium-*/chrome-linux64/chrome", script)
        self.assertIn("executable_path", script)
        self.assertNotIn("playwright install", script)

    def test_process_contract_says_ready_push_only_after_local_candidate(self) -> None:
        docs = [
            ROOT / "AGENTS.md",
            ROOT / "docs/process/DEVELOPMENT_WORKFLOW.md",
            ROOT / "docs/process/DEVELOPMENT_ACCELERATION.md",
            ROOT / "docs/process/PROCESS_HARDENING.md",
        ]
        for path in docs:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.name):
                self.assertIn("VPS-local candidate", text)
                self.assertIn("ready push", text)
        workflow = (ROOT / "docs/process/DEVELOPMENT_WORKFLOW.md").read_text(encoding="utf-8")
        self.assertIn("scripts/vps_candidate.sh", workflow)
        self.assertNotIn("/eod-hot-refresh <exact-head-sha>", workflow)


if __name__ == "__main__":
    unittest.main()
