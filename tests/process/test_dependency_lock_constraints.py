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


    def test_all_accepted_lock_versions_are_explicit_constraints(self) -> None:
        registry = json.loads((ROOT / "supply-chain/registry.json").read_text(encoding="utf-8"))
        observed: dict[str, str] = {}
        for lock_path in sorted((ROOT / "requirements/locks").glob("*.txt")):
            for name, record in implementation.parse_lock(lock_path).items():
                previous = observed.setdefault(name, record["version"])
                self.assertEqual(previous, record["version"], f"cross-profile version drift for {name}")

        self.assertEqual(set(implementation.ACCEPTED_RESOLUTION), set(observed))
        self.assertEqual(set(registry["accepted_resolution"]), set(observed))
        for name, version in observed.items():
            with self.subTest(name=name):
                self.assertEqual(implementation.ACCEPTED_RESOLUTION[name], version)
                self.assertEqual(registry["accepted_resolution"][name], version)


if __name__ == "__main__":
    unittest.main()
