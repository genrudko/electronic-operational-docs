from __future__ import annotations

import copy
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.industrialization_execution import (
    EXECUTION_VIEW_PATH,
    load_raw,
    render_execution_backlog,
    validate_execution_contract,
    validate_execution_view,
)
from scripts.release_plan_model import PLAN_PATH, PROGRAM_PATH, RISK_PATH

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests/process/fixtures/industrialization_execution_cases.json"


class IndustrializationExecutionFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.catalog = json.loads(CASES.read_text(encoding="utf-8"))

    def _copy_inputs(self, target: Path) -> None:
        for relative in (PLAN_PATH, PROGRAM_PATH, RISK_PATH, EXECUTION_VIEW_PATH):
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    def _load(self, root: Path, relative: str) -> dict:
        return json.loads((root / relative).read_text(encoding="utf-8"))

    def _write(self, root: Path, relative: str, value: dict) -> None:
        (root / relative).write_text(
            json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def _program_item(self, program: dict, item_id: str) -> dict:
        return next(
            item
            for phase in program["phases"]
            for item in phase["work_items"]
            if item["id"] == item_id
        )

    def _plan_item(self, plan: dict, item_id: str) -> dict:
        return next(item for item in plan["work_items"] if item["id"] == item_id)

    def _residual_record(self) -> dict:
        return {
            "risk_id": "PSR-034",
            "applicability": "TEMPORARILY_RETAINED",
            "owner_role": "PROJECT_GOVERNANCE_OWNER",
            "accountable_owner": "UNASSIGNED",
            "compensating_controls": ["Documentation Contract blocks drift"],
            "due_date": "2026-08-31",
            "review_condition": "Before SAFE-CONTINUATION decision",
            "affected_gate": "SAFE-CONTINUATION",
            "acceptance_authority": "PRODUCT_OWNER",
            "acceptance_status": "PROPOSED",
            "evidence_reference": "fixture",
            "expires_or_review_at": "2026-08-31",
        }

    def _mutate(
        self,
        root: Path,
        mutation: dict,
        github_evidence: dict,
    ) -> dict:
        mutation_type = mutation["type"]
        if mutation_type == "none":
            return github_evidence
        plan = self._load(root, PLAN_PATH)
        program = self._load(root, PROGRAM_PATH)
        if mutation_type == "program_remove_item_field":
            self._program_item(program, mutation["work_item_id"]).pop(
                mutation["field"]
            )
        elif mutation_type == "program_set_item_field":
            self._program_item(program, mutation["work_item_id"])[
                mutation["field"]
            ] = mutation["value"]
        elif mutation_type == "program_remove_gate_item":
            gate = next(
                gate for gate in program["gates"] if gate["id"] == mutation["gate_id"]
            )
            key = "required_work_items" if "required_work_items" in gate else "required_core_work_items"
            gate[key].remove(mutation["work_item_id"])
        elif mutation_type == "program_set_contract_field":
            program["execution_contract"][mutation["field"]] = mutation["value"]
        elif mutation_type == "plan_set_transition":
            item = self._plan_item(plan, mutation["work_item_id"])
            item["transition"] = {
                "from": mutation["from"],
                "to": mutation["to"],
                "evidence_reference": "fixture",
            }
        elif mutation_type == "plan_set_status":
            item = self._plan_item(plan, mutation["work_item_id"])
            item["status"] = mutation["status"]
            if mutation.get("remove_evidence"):
                item.pop("evidence", None)
            if mutation.get("remove_transition"):
                item.pop("transition", None)
        elif mutation_type == "append_residual_risk":
            record = self._residual_record()
            record.update(mutation.get("overrides", {}))
            program["residual_risks"].append(record)
        elif mutation_type == "github_evidence_set":
            github_evidence[mutation["work_item_id"]][mutation["field"]] = mutation["value"]
        elif mutation_type == "append_view_text":
            path = root / EXECUTION_VIEW_PATH
            path.write_text(path.read_text(encoding="utf-8") + mutation["text"], encoding="utf-8")
        elif mutation_type == "plan_add_active_queue":
            plan["execution"]["industrial_active_queue"] = [
                {"work_item": mutation["work_item_id"]}
            ]
        else:
            raise AssertionError(mutation_type)
        self._write(root, PLAN_PATH, plan)
        self._write(root, PROGRAM_PATH, program)
        return github_evidence

    def test_positive_and_negative_execution_fixtures(self) -> None:
        for case in self.catalog["cases"]:
            with self.subTest(case=case["id"]):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    self._copy_inputs(root)
                    github_evidence = copy.deepcopy(self.catalog["github_evidence"])
                    github_evidence = self._mutate(
                        root, case["mutation"], github_evidence
                    )
                    program, plan = load_raw(root)
                    errors = validate_execution_contract(
                        program,
                        plan,
                        root,
                        github_evidence=github_evidence,
                    )
                    errors.extend(validate_execution_view(program, plan, root))
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

    def test_all_thirty_items_are_rendered_with_execution_state(self) -> None:
        program, plan = load_raw(ROOT)
        rendered = render_execution_backlog(program, plan)
        ids = [
            item["id"]
            for phase in program["phases"]
            for item in phase["work_items"]
        ]
        self.assertEqual(len(ids), 30)
        for item_id in ids:
            self.assertIn(f"`{item_id}`", rendered)


if __name__ == "__main__":
    unittest.main()
