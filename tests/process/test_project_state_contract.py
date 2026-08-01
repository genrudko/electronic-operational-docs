from __future__ import annotations

import unittest

from scripts.project_state_contract import (
    parse_current_state,
    validate_execution_context,
    validate_handoff,
    validate_plan_ownership,
)

SHA = "1234567890abcdef1234567890abcdef12345678"


def current_state(
    *,
    sha: str = SHA,
    work_item: str = "PROCESS-GATE-STATE-001",
    issue: str = "#38",
    pr: str = "#39 / OPEN / DRAFT / NOT MERGED",
    branch: str = "repair/process-gate-state-001",
) -> str:
    return f"""# ЭОД — текущее состояние

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / {sha}
active work item: {work_item}
active issue: {issue}
active PR: {pr}
active branch: {branch}
runtime impact: NONE
preview: UNTOUCHED
```
"""


class CurrentStateParsingTests(unittest.TestCase):
    def test_current_contract_accepts_nonhistorical_baseline_and_active_repair(self) -> None:
        state = parse_current_state(current_state())

        self.assertEqual(state.accepted_main, SHA)
        self.assertEqual(state.active_work_item, "PROCESS-GATE-STATE-001")
        self.assertEqual(state.active_issue, 38)
        self.assertEqual(state.active_pr, 39)
        self.assertEqual(state.active_branch, "repair/process-gate-state-001")

    def test_inactive_state_requires_all_active_fields_to_be_none(self) -> None:
        state = parse_current_state(
            current_state(work_item="NONE", issue="NONE", pr="NONE", branch="NONE")
        )

        self.assertIsNone(state.active_work_item)
        self.assertIsNone(state.active_pr)

    def test_partial_active_tuple_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "all set or all NONE"):
            parse_current_state(current_state(issue="NONE"))

    def test_invalid_accepted_main_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "SHA invalid"):
            parse_current_state(current_state(sha="2a9b923"))


class OwnershipTests(unittest.TestCase):
    def test_handoff_is_navigation_only(self) -> None:
        handoff = (
            "[`CURRENT_STATE.md`](CURRENT_STATE.md)\n"
            "[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml)\n"
        )
        self.assertEqual(validate_handoff(handoff), [])

    def test_handoff_rejects_sha_and_volatile_fields(self) -> None:
        handoff = (
            "[`CURRENT_STATE.md`](CURRENT_STATE.md)\n"
            "[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml)\n"
            f"active PR: #39\nmain / {SHA}\n"
        )
        errors = validate_handoff(handoff)
        self.assertIn("CURRENT_HANDOFF contains volatile SHA", errors)
        self.assertIn("CURRENT_HANDOFF contains volatile state field", errors)

    def test_plan_must_not_own_volatile_state(self) -> None:
        plan = {
            "owners": {
                "state": "docs/project/CURRENT_STATE.md",
                "plan": "docs/project/DEMO_RELEASE_PLAN.yaml",
                "coverage_source": "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv",
                "coverage_decisions": "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv",
            }
        }
        self.assertEqual(validate_plan_ownership(plan), [])

        plan["accepted_main"] = SHA
        plan["active"] = {"work_item": None, "issue": None, "pr": None}
        errors = validate_plan_ownership(plan)
        self.assertIn(
            "DEMO_RELEASE_PLAN duplicates accepted main owned by CURRENT_STATE", errors
        )
        self.assertIn(
            "DEMO_RELEASE_PLAN duplicates active work owned by CURRENT_STATE", errors
        )


class ExecutionContextTests(unittest.TestCase):
    def test_pull_request_context_is_derived_not_hard_coded(self) -> None:
        state = parse_current_state(current_state())
        event = {
            "number": 39,
            "pull_request": {
                "state": "open",
                "draft": True,
                "base": {"sha": SHA},
                "head": {"ref": "repair/process-gate-state-001"},
            },
        }
        self.assertEqual(validate_execution_context(state, event=event), [])

    def test_mismatched_pull_request_is_rejected(self) -> None:
        state = parse_current_state(current_state())
        event = {
            "number": 35,
            "pull_request": {
                "state": "open",
                "draft": True,
                "base": {"sha": SHA},
                "head": {"ref": "feature/master-data-alignment-001"},
            },
        }
        errors = validate_execution_context(state, event=event)
        self.assertIn("CURRENT_STATE active PR does not match workflow pull request", errors)
        self.assertIn(
            "CURRENT_STATE active branch does not match workflow pull request", errors
        )


if __name__ == "__main__":
    unittest.main()
