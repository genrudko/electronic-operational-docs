from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from scripts.check_documentation_contract import (
    apply_module_fixture_mutation,
    load_module_activation_contract,
    validate_module_activation_contract,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = ROOT / "tests/process/fixtures/module_activation_contract_cases.json"


class ModuleActivationContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_module_activation_contract(ROOT)
        cls.catalog = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def test_canonical_contract_is_valid(self) -> None:
        self.assertEqual(validate_module_activation_contract(self.contract), [])

    def test_positive_and_fail_closed_negative_fixtures(self) -> None:
        for case in self.catalog["cases"]:
            with self.subTest(case=case["id"]):
                candidate = copy.deepcopy(self.contract)
                if case["mutation"] is not None:
                    candidate = apply_module_fixture_mutation(
                        candidate, case["mutation"]
                    )
                errors = validate_module_activation_contract(candidate)
                expected_rule = case["expected_rule"]
                if expected_rule is None:
                    self.assertEqual(errors, [])
                    continue
                self.assertTrue(
                    any(f"rule={expected_rule}" in error for error in errors),
                    msg="\n".join(errors),
                )

    def test_fixture_ids_cover_required_negative_invariants(self) -> None:
        required = set(self.contract["negative_architecture_invariants"])
        actual = {
            case["id"]
            for case in self.catalog["cases"]
            if case["id"].startswith("N")
        }
        self.assertEqual(actual, required)

    def test_behavior_matrix_preserves_history_outside_active(self) -> None:
        matrix = self.contract["behavior_matrix"]
        for state in ("CONFIGURED", "INACTIVE", "RETIRED"):
            self.assertIn(
                "ALLOW_RETAINED_HISTORY", matrix[state]["detail_history"]
            )
            self.assertEqual(matrix[state]["create"], "DENY")
            self.assertEqual(matrix[state]["edit_transition"], "DENY")

    def test_reactivation_is_two_step_and_identity_preserving(self) -> None:
        lifecycle = self.contract["lifecycle"]
        history = self.contract["history_and_reactivation"]
        self.assertEqual(
            lifecycle["reactivation_paths"]["INACTIVE"],
            ["INACTIVE", "CONFIGURED", "ACTIVE"],
        )
        self.assertEqual(
            lifecycle["reactivation_paths"]["RETIRED"],
            ["RETIRED", "CONFIGURED", "ACTIVE"],
        )
        self.assertFalse(history["reactivation_creates_new_module_identity"])
        self.assertTrue(history["stale_configuration_revalidated_before_active"])

    def test_scope_contract_matches_current_v1_topology(self) -> None:
        scope = self.contract["scope_resolution"]
        self.assertEqual(
            scope["ordinary_precedence"],
            ["WORKPLACE", "ENERGY_SITE", "ORGANIZATION"],
        )
        self.assertFalse(scope["workplace_is_child_of_energy_site"])
        self.assertEqual(scope["same_scope_duplicate_result"], "DENY")
        self.assertTrue(scope["child_may_override_parent_inactive_to_active"])


if __name__ == "__main__":
    unittest.main()
