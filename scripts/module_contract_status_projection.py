"""Validate every mutable module-contract status against the canonical plan."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

PLAN_PATH = "docs/project/DEMO_RELEASE_PLAN.yaml"
SECTION = "## CURRENT CODE STATUS / CAPABILITIES"
PROJECTION_RE = re.compile(
    r"`(?P<code>IMPLEMENTED-ACCEPTED|IMPLEMENTED-PARTIAL|FOUNDATION-ONLY|"
    r"PRESENTATION-ONLY|PLANNED-ONLY|ABSENT|VERIFY)`;\s*"
    r"release\s+`(?P<status>NOT_STARTED|READY|IN_PROGRESS|BLOCKED|AT_REVIEW|"
    r"ACCEPTED|DEFERRED|EXCLUDED)`",
    re.IGNORECASE,
)


def _error(
    file: str,
    module_id: str,
    expected: object,
    actual: object,
) -> str:
    return (
        f"{file}: [{module_id}] rule=module-current-status-projection; "
        f"expected={expected!r}; actual={actual!r}"
    )


def validate_module_contract_status_projections(
    plan: dict[str, Any], root: Path
) -> list[str]:
    """Require an exact code/release projection in every module contract."""
    errors: list[str] = []
    for module in plan.get("modules", []):
        if not isinstance(module, dict):
            continue
        module_id = str(module.get("id", "<missing>"))
        relative = str(module.get("contract", ""))
        path = root / relative
        if not path.is_file():
            continue
        text = path.read_text(encoding="utf-8")
        if SECTION not in text:
            continue
        section = text.split(SECTION, 1)[1].split("\n## ", 1)[0]
        match = PROJECTION_RE.search(section)
        actual = (
            None
            if match is None
            else (
                match.group("code").upper(),
                match.group("status").upper(),
            )
        )
        expected = (module.get("code"), module.get("status"))
        if actual != expected:
            errors.append(_error(relative, module_id, expected, actual))
    return errors
