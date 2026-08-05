from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from scripts.module_contract_status_projection import (
    validate_module_contract_status_projections,
)
from scripts.release_plan_model import load_plan

ROOT = Path(__file__).resolve().parents[2]


class ModuleContractStatusProjectionTests(unittest.TestCase):
    def test_all_module_contract_statuses_match_canonical_plan(self) -> None:
        plan = load_plan(ROOT)
        self.assertEqual(
            validate_module_contract_status_projections(plan, ROOT),
            [],
        )

    def test_unmarked_legacy_contract_status_drift_fails_closed(self) -> None:
        plan = load_plan(ROOT)
        platform = next(
            module for module in plan["modules"]
            if module["id"] == "PLATFORM"
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            relative = platform["contract"]
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
            target.write_text(
                target.read_text(encoding="utf-8").replace(
                    "`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`",
                    "`ABSENT`; release `NOT_STARTED`",
                    1,
                ),
                encoding="utf-8",
            )
            errors = validate_module_contract_status_projections(plan, root)
            self.assertTrue(
                any(
                    "rule=module-current-status-projection" in error
                    and "[PLATFORM]" in error
                    for error in errors
                ),
                msg="\n".join(errors),
            )


if __name__ == "__main__":
    unittest.main()
