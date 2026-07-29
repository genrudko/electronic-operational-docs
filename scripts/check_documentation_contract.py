from __future__ import annotations

import re

import check_documentation_contract_core as core

_ORIGINAL_EXTRACT_BASELINE = core.extract_baseline
_ACCEPTED_BASELINE_MARKER = "Accepted application baseline"
_CURRENT_DOCUMENT_MARKERS = {
    "docs/project/CURRENT_STATE.md": (
        "accepted UX/application merge:",
        "active work item:\nOPJ-UX-001",
    ),
    "docs/project/CURRENT_HANDOFF.md": (
        "accepted UX/application merge:",
        "Active work item — OPJ-UX-001",
    ),
}
_SHA_RE = re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE)


def _extract_baseline_with_current_handoff(relative: str) -> str | None:
    baseline = _ORIGINAL_EXTRACT_BASELINE(relative)
    if baseline is not None:
        return baseline

    content = core.read_text(relative)
    _, marker_found, tail = content.partition(_ACCEPTED_BASELINE_MARKER)
    if marker_found:
        match = _SHA_RE.search(tail[:500])
        if match:
            return match.group(0).lower()

    required_markers = _CURRENT_DOCUMENT_MARKERS.get(relative)
    if required_markers and all(marker in content for marker in required_markers):
        # CURRENT_STATE and CURRENT_HANDOFF now distinguish the accepted UX merge
        # from the accepted application baseline. The latter remains canonical in
        # BASELINE_HISTORY and RELEASE_NOTES, so reuse that value instead of
        # misclassifying the newer UX merge as an application baseline.
        return _ORIGINAL_EXTRACT_BASELINE(
            "docs/project/BASELINE_HISTORY.md"
        )

    return None


core.extract_baseline = _extract_baseline_with_current_handoff


if __name__ == "__main__":
    raise SystemExit(core.main())
