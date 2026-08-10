from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts import dependency_provenance_implementation as implementation

ROOT = Path(__file__).resolve().parents[2]


class DependencyLockConstraintTests(unittest.TestCase):
    def test_browser_greenlet_transitive_is_part_of_accepted_resolution(self) -> None:
        browser = implementation.parse_lock(ROOT / "requirements/locks/browser.txt")
        registry = json.loads((ROOT / "supply-chain/registry.json").read_text(encoding="utf-8"))

        self.assertEqual(browser["greenlet"]["version"], "3.5.4")
        self.assertEqual(implementation.ACCEPTED_RESOLUTION["greenlet"], "3.5.4")
        self.assertEqual(registry["accepted_resolution"]["greenlet"], "3.5.4")


if __name__ == "__main__":
    unittest.main()
