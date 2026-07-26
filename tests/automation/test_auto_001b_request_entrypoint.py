from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REQUEST_VALIDATOR = ROOT / "scripts/automation/auto_001b_request.py"


class RequestEntrypointTests(unittest.TestCase):
    def test_direct_script_entrypoint_imports_project_package(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(REQUEST_VALIDATOR), "--help"],
            cwd=ROOT,
            check=False,
            capture_output=True,
            text=True,
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("AUTO-001B trusted request validation", completed.stdout)


if __name__ == "__main__":
    unittest.main()
