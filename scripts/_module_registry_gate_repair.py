from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CURRENT_STATE = ROOT / "docs/project/CURRENT_STATE.md"
CASES = ROOT / "tests/process/fixtures/industrialization_execution_cases.json"
RENDERER = ROOT / "scripts/industrialization_execution.py"


def main() -> None:
    state = CURRENT_STATE.read_text(encoding="utf-8")
    old = "runtime impact: REPOSITORY / DATABASE SCHEMA ONLY; LIVE RUNTIME UNTOUCHED"
    if old in state:
        state = state.replace(old, "runtime impact: NONE", 1)
    if "runtime impact: NONE" not in state.split("```", 2)[1]:
        raise RuntimeError("CURRENT_STATE canonical runtime impact was not repaired")
    CURRENT_STATE.write_text(state, encoding="utf-8")

    catalog = json.loads(CASES.read_text(encoding="utf-8"))
    by_id = {case["id"]: case for case in catalog["cases"]}
    by_id["in-progress-with-blocked-dependency"]["mutation"] = {
        "type": "plan_set_status",
        "work_item_id": "MODULE-MIGRATION-COMPATIBILITY-001",
        "status": "IN_PROGRESS",
    }
    by_id["dependency-bypass"]["mutation"] = {
        "type": "plan_set_status",
        "work_item_id": "OBSERVABILITY-001",
        "status": "READY",
    }
    CASES.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    renderer = RENDERER.read_text(encoding="utf-8")
    old_sentence = (
        '            "Completion of all eight items still requires an explicit "\n'
        '            "product-owner decision before any limited domain continuation.",'
    )
    new_sentence = (
        '            "SAFE-CONTINUATION is complete. The product owner explicitly selected "\n'
        '            "MODULE-REGISTRY -> UX foundation/page templates -> product/module "\n'
        '            "development before remaining risk-based PILOT-READY hardening.",'
    )
    if old_sentence in renderer:
        renderer = renderer.replace(old_sentence, new_sentence, 1)
    RENDERER.write_text(renderer, encoding="utf-8")

    print("MODULE_REGISTRY_GATE_REPAIR=OK")


if __name__ == "__main__":
    main()
