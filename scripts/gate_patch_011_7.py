from __future__ import annotations

from pathlib import Path

import gate_patch_011_7_core as core
import project_state_contract

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    core.main()
    state = project_state_contract.require_repository(ROOT, verify_context=True)
    print(f"CURRENT_PROJECT_STATE_CONTRACT=PASSED WORK_ITEM={state.active_work_item or 'NONE'}")


if __name__ == "__main__":
    main()
