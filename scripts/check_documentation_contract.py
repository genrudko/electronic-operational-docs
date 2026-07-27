from __future__ import annotations

import re

import check_documentation_contract_core as core

_ORIGINAL_EXTRACT_BASELINE = core.extract_baseline
_ACCEPTED_BASELINE_MARKER = "Accepted application baseline"
_SHA_RE = re.compile(r"\b[0-9a-f]{40}\b", re.IGNORECASE)


def _extract_baseline_with_current_handoff(relative: str) -> str | None:
    baseline = _ORIGINAL_EXTRACT_BASELINE(relative)
    if baseline is not None or relative != "docs/project/CURRENT_HANDOFF.md":
        return baseline

    content = core.read_text(relative)
    _, marker_found, tail = content.partition(_ACCEPTED_BASELINE_MARKER)
    if not marker_found:
        return None

    match = _SHA_RE.search(tail[:500])
    return match.group(0).lower() if match else None


core.extract_baseline = _extract_baseline_with_current_handoff


if __name__ == "__main__":
    raise SystemExit(core.main())
