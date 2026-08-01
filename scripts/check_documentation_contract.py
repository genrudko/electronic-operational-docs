from __future__ import annotations

import re
from pathlib import Path

import check_demo_release_plan
import check_documentation_contract_core as core

_ORIGINAL_EXTRACT_BASELINE = core.extract_baseline
_ORIGINAL_PLAN_VALIDATE = check_demo_release_plan.validate
_ROOT = Path(__file__).resolve().parents[1]
_CURRENT_STATE = "docs/project/CURRENT_STATE.md"
_COMPATIBILITY_BASELINE_FILES = {
    "docs/project/CURRENT_HANDOFF.md",
    "docs/project/BASELINE_HISTORY.md",
    "docs/releases/RELEASE_NOTES.md",
}
_OBSOLETE_PLAN_ERRORS = {
    "accepted main baseline invalid",
    "CURRENT_STATE owner invalid",
    "CURRENT_HANDOFF duplicates volatile state",
}
_ACCEPTED_APPLICATION_RE = re.compile(
    r"accepted application baseline:\s*main\s*/\s*([0-9a-f]{40})"
)


def _extract_canonical_baseline(relative: str) -> str | None:
    if relative in _COMPATIBILITY_BASELINE_FILES:
        return _ORIGINAL_EXTRACT_BASELINE(_CURRENT_STATE)
    return _ORIGINAL_EXTRACT_BASELINE(relative)


def _validate_current_plan(plan: dict[str, object]) -> list[str]:
    errors = [
        error
        for error in _ORIGINAL_PLAN_VALIDATE(plan)
        if error not in _OBSOLETE_PLAN_ERRORS
    ]
    state = (_ROOT / _CURRENT_STATE).read_text(encoding="utf-8")
    handoff = (_ROOT / "docs/project/CURRENT_HANDOFF.md").read_text(
        encoding="utf-8"
    )

    match = _ACCEPTED_APPLICATION_RE.search(state)
    if match is None or plan.get("accepted_main") != match.group(1):
        errors.append("accepted application baseline owner mismatch")

    required_state_markers = (
        "**Единственный владелец:** accepted application SHA, active work item/PR и runtime state.",
        "plan version: 1.0 / ACCEPTED",
        "preview: UNTOUCHED",
    )
    if any(marker not in state for marker in required_state_markers):
        errors.append("CURRENT_STATE owner invalid")

    required_handoff_markers = (
        "Volatile state: [`CURRENT_STATE.md`](CURRENT_STATE.md)",
        "Release/module state: [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml)",
    )
    if any(marker not in handoff for marker in required_handoff_markers):
        errors.append("CURRENT_HANDOFF navigation contract invalid")
    if re.search(r"\b[0-9a-f]{40}\b", handoff) or "active work item:" in handoff.lower():
        errors.append("CURRENT_HANDOFF duplicates volatile state")
    return errors


core.extract_baseline = _extract_canonical_baseline
check_demo_release_plan.validate = _validate_current_plan


def main() -> int:
    result = core.main()
    if result:
        return result
    return check_demo_release_plan.main()


if __name__ == "__main__":
    raise SystemExit(main())
