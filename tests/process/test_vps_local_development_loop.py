from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class VPSLocalDevelopmentLoopTests(unittest.TestCase):
    def test_vps_candidate_feature_does_not_modify_protected_automation(self) -> None:
        """The local candidate loop must live in unprivileged scripts without touching protected paths."""
        candidate_script = ROOT / "scripts/vps_candidate.sh"
        self.assertTrue(candidate_script.exists())
        self.assertFalse(str(candidate_script).startswith(str(ROOT / "scripts/automation")))

        # Protected automation path invariants
        policy_path = ROOT / ".github/auto001a-foundation.json"
        if policy_path.exists():
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            blocked_prefixes = policy.get("blocked_path_prefixes", [])
            self.assertIn("scripts/automation", blocked_prefixes)

        # Preflight script in protected automation must not depend on vps_candidate.sh
        preflight_text = (ROOT / "scripts/automation/work_item_preflight.py").read_text(encoding="utf-8")
        self.assertNotIn("scripts/vps_candidate.sh", preflight_text)
        self.assertNotIn("VPS_LOCAL_CANDIDATE", preflight_text)
        self.assertNotIn("FINAL_TRUSTED_ONLY", preflight_text)

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
        script = (ROOT / "scripts/vps_candidate.sh").read_text(encoding="utf-8")
        self.assertIn('USER_HOME="${HOME:-}"', script)
        self.assertIn('getent passwd "$(id -u)"', script)
        self.assertIn('[[ -n "$USER_HOME" ]]', script)

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

    def test_process_contract_preserves_canonical_preflight_and_protected_policy(self) -> None:
        hardening = (ROOT / "docs/process/PROCESS_HARDENING.md").read_text(encoding="utf-8")
        self.assertIn("HOT_REFRESH / FULL_DEVELOPMENT", hardening)
        self.assertNotIn("VPS_LOCAL_CANDIDATE", hardening)
        self.assertNotIn("FINAL_TRUSTED_ONLY", hardening)


if __name__ == "__main__":
    unittest.main()
