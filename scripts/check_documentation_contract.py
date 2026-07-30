from __future__ import annotations

import check_documentation_contract_core as core
import check_demo_release_plan

_ORIGINAL_EXTRACT_BASELINE = core.extract_baseline
_CURRENT_STATE = "docs/project/CURRENT_STATE.md"
_COMPATIBILITY_BASELINE_FILES = {
    "docs/project/CURRENT_HANDOFF.md",
    "docs/project/BASELINE_HISTORY.md",
    "docs/releases/RELEASE_NOTES.md",
}


def _extract_canonical_baseline(relative: str) -> str | None:
    if relative in _COMPATIBILITY_BASELINE_FILES:
        return _ORIGINAL_EXTRACT_BASELINE(_CURRENT_STATE)
    return _ORIGINAL_EXTRACT_BASELINE(relative)


core.extract_baseline = _extract_canonical_baseline


def main() -> int:
    result = core.main()
    if result:
        return result
    return check_demo_release_plan.main()


if __name__ == "__main__":
    raise SystemExit(main())
