from __future__ import annotations

import copy
import csv
import json
import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.project_state_contract import (
    parse_current_state,
    validate_duplicate_volatile_owners,
    validate_execution_context,
)
from scripts.release_plan_compat_validation import (
    validate_release_plan_compatibility,
)
from scripts.release_plan_model import (
    COMPETITOR_MATRIX_PATH,
    COVERAGE_DECISIONS_PATH,
    COVERAGE_SOURCE_PATH,
    DECISION_PROFILES_PATH,
    LEGAL_MODE_MATRIX_PATH,
    PERSONNEL_AUTHORITY_MATRIX_PATH,
    PLAN_PATH,
    SOURCE_REGISTRY_PATH,
    load_plan,
)

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "tests/process/fixtures/release_plan_compatibility_cases.json"
SHA = "1234567890abcdef1234567890abcdef12345678"


def state_text(
    *,
    repository: str = "genrudko/electronic-operational-docs",
    work_item: str = "PROJECT-STATE-RECONCILIATION-001",
    issue: str = "#50",
    pr: str = "#51 / OPEN / DRAFT / NOT MERGED",
    branch: str = "governance/project-state-reconciliation-001",
    runtime: str = "NONE",
    preview: str = "UNTOUCHED",
    duplicate: str = "",
) -> str:
    return f"""# State
```text
repository: {repository}
accepted main baseline: main / {SHA}
active work item: {work_item}
active issue: {issue}
active PR: {pr}
active branch: {branch}
runtime impact: {runtime}
preview: {preview}
{duplicate}```
"""


class StrictCurrentStateTests(unittest.TestCase):
    def test_valid_full_descriptor(self) -> None:
        state = parse_current_state(state_text())
        self.assertEqual(state.active_pr_state, "OPEN")
        self.assertEqual(state.active_pr_review, "DRAFT")
        self.assertEqual(state.active_pr_merge, "NOT MERGED")

    def test_requested_negative_states(self) -> None:
        cases = (
            (state_text(repository="other/repo"), "repository invalid"),
            (state_text(work_item="bad item"), "work item ID invalid"),
            (state_text(issue="#0"), "active issue invalid"),
            (state_text(branch="bad/../branch"), "active branch invalid"),
            (state_text(branch="bad.lock"), "active branch invalid"),
            (state_text(runtime="PRODUCTION"), "runtime impact invalid"),
            (state_text(preview="LIVE"), "preview status invalid"),
            (state_text(duplicate="active issue: #51\n"), "duplicate key"),
        )
        for text, message in cases:
            with self.subTest(message=message):
                with self.assertRaisesRegex(ValueError, message):
                    parse_current_state(text)

    def test_event_descriptor_mismatch_is_rejected(self) -> None:
        state = parse_current_state(
            state_text(pr="#51 / CLOSED / READY / MERGED")
        )
        event = {
            "number": 51,
            "pull_request": {
                "state": "open",
                "draft": True,
                "merged": False,
                "head": {"ref": "governance/project-state-reconciliation-001"},
            },
        }
        errors = validate_execution_context(state, event=event)
        self.assertTrue(any("PR state" in error for error in errors))
        self.assertTrue(any("review state" in error for error in errors))
        self.assertTrue(any("merge state" in error for error in errors))

    def test_unknown_second_owner_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "docs/project/SECOND_CURRENT_STATE.md"
            path.parent.mkdir(parents=True)
            path.write_text("active PR: #999\n", encoding="utf-8")
            errors = validate_duplicate_volatile_owners(root)
            self.assertTrue(
                any("rule=single-volatile-owner" in error for error in errors)
            )


class ReleasePlanCompatibilityFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = json.loads(CASES.read_text(encoding="utf-8"))["cases"]

    def _copy_inputs(self, target: Path) -> None:
        plan = load_plan(ROOT)
        paths = [
            PLAN_PATH,
            COVERAGE_SOURCE_PATH,
            COVERAGE_DECISIONS_PATH,
            DECISION_PROFILES_PATH,
            SOURCE_REGISTRY_PATH,
            COMPETITOR_MATRIX_PATH,
            LEGAL_MODE_MATRIX_PATH,
            PERSONNEL_AUTHORITY_MATRIX_PATH,
            *(module["contract"] for module in plan["modules"]),
        ]
        for relative in paths:
            source = ROOT / relative
            destination = target / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)

    def _read_csv(self, root: Path, relative: str) -> tuple[list[str], list[dict]]:
        with (root / relative).open(encoding="utf-8", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=";")
            return list(reader.fieldnames or []), list(reader)

    def _write_csv(
        self, root: Path, relative: str, fields: list[str], rows: list[dict]
    ) -> None:
        with (root / relative).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, delimiter=";")
            writer.writeheader()
            writer.writerows(rows)

    def _mutate(self, case: str, root: Path, plan: dict) -> None:
        modules = plan["modules"]
        first = modules[0]
        if case == "missing-version":
            plan.pop("version")
        elif case == "missing-release":
            plan.pop("release")
        elif case == "damaged-status-vocabulary":
            plan["statuses"].pop()
        elif case == "damaged-depth-vocabulary":
            plan["depths"].pop()
        elif case == "damaged-code-vocabulary":
            plan["code_statuses"].pop()
        elif case == "missing-module":
            modules.pop()
        elif case == "duplicate-module-id":
            modules[1]["id"] = first["id"]
        elif case == "duplicate-module-order":
            modules[1]["order"] = first["order"]
        elif case == "invalid-module-depth":
            first["depth"] = "BROKEN"
        elif case == "missing-module-group":
            first.pop("group")
        elif case == "missing-module-sources":
            first.pop("sources")
        elif case == "missing-capability":
            first["capability"] = ""
        elif case == "duplicate-acceptance":
            modules[1]["acceptance"] = first["acceptance"]
        elif case == "missing-work-item":
            first["work_item"] = ""
        elif case == "unknown-source":
            first["sources"] = "SRC-DOES-NOT-EXIST"
        elif case == "dependency-topology":
            plan["dependency_order"] = list(reversed(plan["dependency_order"]))
        elif case == "accepted-slice-reset":
            next(m for m in modules if m["id"] == "OPJ")["accepted"] = ""
        elif case == "mutable-status-drift":
            next(m for m in modules if m["id"] == "OPJ")["code"] = "ABSENT"
        elif case == "post-demo-loss":
            plan["post_demo"].pop()
        elif case == "scenario-loss":
            plan["scenarios"].pop()
        elif case in {"contract-id-loss", "generic-boilerplate"}:
            path = root / first["contract"]
            text = path.read_text(encoding="utf-8")
            if case == "contract-id-loss":
                text = text.replace(f"`{first['id']}`", "`BROKEN-ID`", 1)
            else:
                text += "\nСоздать или выбрать первичный факт, проверить полномочие\n"
            path.write_text(text, encoding="utf-8")
        elif case == "coverage-row-loss":
            fields, rows = self._read_csv(root, COVERAGE_SOURCE_PATH)
            self._write_csv(root, COVERAGE_SOURCE_PATH, fields, rows[:-1])
        elif case == "decision-profile-loss":
            fields, rows = self._read_csv(root, COVERAGE_DECISIONS_PATH)
            rows[0]["profile_id"] = "PROFILE-MISSING"
            self._write_csv(root, COVERAGE_DECISIONS_PATH, fields, rows)
        elif case in {"ref-od-059-split", "ref-od-063-boundary"}:
            _, decisions = self._read_csv(root, COVERAGE_DECISIONS_PATH)
            reference = "REF-OD-059" if "059" in case else "REF-OD-063"
            profile_id = next(
                row["profile_id"] for row in decisions
                if row["reference_id"] == reference
            )
            fields, profiles = self._read_csv(root, DECISION_PROFILES_PATH)
            profile = next(row for row in profiles if row["profile_id"] == profile_id)
            if "059" in case:
                profile["module_ids"] = "WORK-PERMIT"
            else:
                profile["post_demo_contour"] = ""
            self._write_csv(root, DECISION_PROFILES_PATH, fields, profiles)
        elif case == "competitor-catalog-loss":
            fields, rows = self._read_csv(root, COMPETITOR_MATRIX_PATH)
            self._write_csv(root, COMPETITOR_MATRIX_PATH, fields, rows[:-1])
        elif case == "legal-mode-drift":
            fields, rows = self._read_csv(root, LEGAL_MODE_MATRIX_PATH)
            rows[0]["proven_legal_mode"] = "ELECTRONIC_ORIGINAL"
            self._write_csv(root, LEGAL_MODE_MATRIX_PATH, fields, rows)
        elif case == "personnel-marker-loss":
            path = root / PERSONNEL_AUTHORITY_MATRIX_PATH
            path.write_text(
                path.read_text(encoding="utf-8").replace("operational right", ""),
                encoding="utf-8",
            )
        else:
            raise AssertionError(case)

    def test_positive_baseline(self) -> None:
        self.assertEqual(validate_release_plan_compatibility(load_plan(ROOT), ROOT), [])

    def test_major_data_class_regressions_fail_closed(self) -> None:
        for case, expected_rule in self.cases:
            with self.subTest(case=case):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    self._copy_inputs(root)
                    plan = copy.deepcopy(load_plan(ROOT))
                    self._mutate(case, root, plan)
                    errors = validate_release_plan_compatibility(plan, root)
                    self.assertTrue(
                        any(f"rule={expected_rule}" in error for error in errors),
                        msg="\n".join(errors),
                    )


if __name__ == "__main__":
    unittest.main()
