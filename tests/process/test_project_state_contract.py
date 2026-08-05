from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.demo_release_plan import (
    PROGRAM_PATH,
    load_plan,
    load_program,
    render_checklist,
    render_module_map,
    render_program_markdown,
    render_sequence,
)
from scripts.project_state_contract import (
    parse_current_state,
    validate_execution_context,
    validate_handoff,
    validate_plan_ownership,
    validate_repository,
)

ROOT = Path(__file__).resolve().parents[2]
FIXTURE_PATH = (
    ROOT / "tests/process/fixtures/documentation_state_contract.json"
)
SHA = "1234567890abcdef1234567890abcdef12345678"
LATER_SHA = "abcdef1234567890abcdef1234567890abcdef12"


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
                "coverage_source": (
                    "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv"
                ),
                "coverage_decisions": (
                    "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv"
                ),
            }
        }
        self.assertEqual(validate_plan_ownership(plan), [])
        plan["accepted_main"] = SHA
        plan["active"] = {"work_item": None, "issue": None, "pr": None}
        errors = validate_plan_ownership(plan)
        self.assertIn(
            "DEMO_RELEASE_PLAN duplicates accepted main owned by CURRENT_STATE",
            errors,
        )
        self.assertIn(
            "DEMO_RELEASE_PLAN duplicates active work owned by CURRENT_STATE",
            errors,
        )


class ExecutionContextTests(unittest.TestCase):
    def test_pull_request_context_is_derived_not_hard_coded(self) -> None:
        state = parse_current_state(current_state())
        event = {
            "number": 39,
            "pull_request": {
                "state": "open",
                "draft": True,
                "merged": False,
                "base": {"sha": SHA},
                "head": {"ref": "repair/process-gate-state-001"},
            },
        }
        self.assertEqual(validate_execution_context(state, event=event), [])

    def test_post_merge_coordination_commit_may_follow_accepted_main(self) -> None:
        state = parse_current_state(current_state())
        event = {
            "number": 39,
            "pull_request": {
                "state": "open",
                "draft": True,
                "merged": False,
                "base": {"sha": LATER_SHA},
                "head": {"ref": "repair/process-gate-state-001"},
            },
        }
        self.assertEqual(validate_execution_context(state, event=event), [])

    def test_main_tip_may_follow_accepted_merge_baseline(self) -> None:
        state = parse_current_state(current_state())
        self.assertEqual(
            validate_execution_context(state, origin_main=LATER_SHA),
            [],
        )

    def test_mismatched_pull_request_is_rejected(self) -> None:
        state = parse_current_state(current_state())
        event = {
            "number": 35,
            "pull_request": {
                "state": "open",
                "draft": True,
                "merged": False,
                "base": {"sha": SHA},
                "head": {"ref": "feature/master-data-alignment-001"},
            },
        }
        errors = validate_execution_context(state, event=event)
        self.assertIn(
            "CURRENT_STATE active PR does not match workflow pull request", errors
        )
        self.assertIn(
            "CURRENT_STATE active branch does not match workflow pull request",
            errors,
        )


class DocumentationStateContractFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))

    def _copy_contract_inputs(self, target: Path) -> None:
        relative_paths = [
            "docs/project/CURRENT_STATE.md",
            "docs/project/CURRENT_HANDOFF.md",
            "docs/project/DEMO_RELEASE_PLAN.yaml",
            "docs/project/INDUSTRIALIZATION_PROGRAM.yaml",
            "docs/project/INDUSTRIALIZATION_PROGRAM.md",
            "docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md",
            "docs/product/MODULE_MAP.md",
            "docs/product/IMPLEMENTATION_SEQUENCE.md",
            "docs/audits/PROJECT_SUSTAINABILITY_RISK_REGISTER_20260805.csv",
            "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv",
            "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv",
            "docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISION_PROFILES.csv",
            "docs/evidence/SOURCE_REGISTRY.csv",
            "docs/evidence/COMPETITOR_CAPABILITY_MATRIX.csv",
            "docs/evidence/DOCUMENT_LEGAL_MODE_MATRIX.csv",
            "docs/evidence/PERSONNEL_AUTHORITY_MATRIX.csv",
        ]
        plan = load_plan(ROOT)
        relative_paths.extend(
            module["contract"] for module in plan["modules"]
        )
        for relative in relative_paths:
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    def _load_json(self, root: Path, relative: str) -> dict:
        return json.loads((root / relative).read_text(encoding="utf-8"))

    def _write_json(self, root: Path, relative: str, value: dict) -> None:
        (root / relative).write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _apply_mutation(self, root: Path, mutation: dict) -> None:
        mutation_type = mutation["type"]
        if mutation_type == "none":
            return
        if mutation_type == "plan_module_set":
            plan = self._load_json(
                root, "docs/project/DEMO_RELEASE_PLAN.yaml"
            )
            module = next(
                item
                for item in plan["modules"]
                if item["id"] == mutation["module_id"]
            )
            module[mutation["field"]] = mutation["value"]
            self._write_json(
                root, "docs/project/DEMO_RELEASE_PLAN.yaml", plan
            )
            return
        if mutation_type == "plan_duplicate_work_item":
            plan = self._load_json(
                root, "docs/project/DEMO_RELEASE_PLAN.yaml"
            )
            item = next(
                entry
                for entry in plan["work_items"]
                if entry["id"] == mutation["work_item_id"]
            )
            plan["work_items"].append(copy.deepcopy(item))
            self._write_json(
                root, "docs/project/DEMO_RELEASE_PLAN.yaml", plan
            )
            return
        if mutation_type.startswith("program_"):
            program = self._load_json(root, PROGRAM_PATH)
            if mutation_type == "program_append_dependency":
                item = next(
                    item
                    for phase in program["phases"]
                    for item in phase["work_items"]
                    if item["id"] == mutation["work_item_id"]
                )
                item["dependencies"].append(mutation["dependency"])
            elif mutation_type in {
                "program_remove_gate_item",
                "program_append_gate_item",
            }:
                gate = next(
                    gate
                    for gate in program["gates"]
                    if gate["id"] == mutation["gate_id"]
                )
                key = (
                    "required_work_items"
                    if "required_work_items" in gate
                    else "required_core_work_items"
                )
                if mutation_type == "program_remove_gate_item":
                    gate[key].remove(mutation["work_item_id"])
                else:
                    gate[key].append(mutation["work_item_id"])
            else:
                raise AssertionError(mutation_type)
            self._write_json(root, PROGRAM_PATH, program)
            return
        if mutation_type == "append_text":
            path = root / mutation["path"]
            path.write_text(
                path.read_text(encoding="utf-8") + mutation["text"],
                encoding="utf-8",
            )
            return
        if mutation_type == "replace_text":
            path = root / mutation["path"]
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(
                    mutation["old"],
                    mutation["new"],
                    mutation.get("count", -1),
                ),
                encoding="utf-8",
            )
            return
        raise AssertionError(f"unknown mutation {mutation_type}")

    def test_positive_and_fail_closed_negative_fixtures(self) -> None:
        for case in self.catalog["cases"]:
            with self.subTest(case=case["id"]):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    self._copy_contract_inputs(root)
                    self._apply_mutation(root, case["mutation"])
                    errors = validate_repository(root)
                    expected_rule = case["expected_rule"]
                    if expected_rule is None:
                        self.assertEqual(errors, [])
                        continue
                    self.assertTrue(
                        any(f"rule={expected_rule}" in error for error in errors),
                        msg="\n".join(errors),
                    )
                    for error in errors:
                        if "rule=" in error:
                            self.assertIn("expected=", error)
                            self.assertIn("actual=", error)

    def test_all_required_generated_views_are_exact(self) -> None:
        plan = load_plan(ROOT)
        program = load_program(ROOT)
        raw_program = json.loads(
            (ROOT / PROGRAM_PATH).read_text(encoding="utf-8")
        )
        expected = {
            ROOT / "docs/product/MODULE_MAP.md": render_module_map(plan),
            ROOT / "docs/product/IMPLEMENTATION_SEQUENCE.md": render_sequence(
                plan, program
            ),
            ROOT
            / "docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md": render_checklist(
                plan, program
            ),
            ROOT
            / "docs/project/INDUSTRIALIZATION_PROGRAM.md": render_program_markdown(
                raw_program
            ),
        }
        for path, content in expected.items():
            with self.subTest(path=path):
                self.assertEqual(path.read_text(encoding="utf-8"), content)


if __name__ == "__main__":
    unittest.main()
