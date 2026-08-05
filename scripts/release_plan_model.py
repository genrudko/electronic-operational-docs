"""Shared model and loader primitives for the documentation state contract."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = "docs/project/DEMO_RELEASE_PLAN.yaml"
PROGRAM_PATH = "docs/project/INDUSTRIALIZATION_PROGRAM.yaml"
PROGRAM_MD_PATH = "docs/project/INDUSTRIALIZATION_PROGRAM.md"
RISK_PATH = "docs/audits/PROJECT_SUSTAINABILITY_RISK_REGISTER_20260805.csv"
ALLOWED_STATUSES = {
    "NOT_STARTED",
    "READY",
    "IN_PROGRESS",
    "BLOCKED",
    "AT_REVIEW",
    "ACCEPTED",
    "DEFERRED",
    "EXCLUDED",
}
ALLOWED_CODE_STATUSES = {
    "IMPLEMENTED-ACCEPTED",
    "IMPLEMENTED-PARTIAL",
    "FOUNDATION-ONLY",
    "PRESENTATION-ONLY",
    "PLANNED-ONLY",
    "ABSENT",
    "VERIFY",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
WORK_ITEM_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}$")
MODULE_MARKERS = (
    "## MODULE ID",
    "## НАЗНАЧЕНИЕ",
    "## КРИТИЧЕСКИЕ СЦЕНАРИИ",
    "## PRIMARY FACTS / DERIVED VIEWS",
    "## РОЛИ И ПОЛНОМОЧИЯ",
    "## ДОКУМЕНТЫ И LEGAL MODE",
    "## СВЯЗИ",
    "## SOURCE IDS / BENCHMARK",
    "## DEMO / POST-DEMO",
    "## CURRENT CODE STATUS / CAPABILITIES",
    "## DEPENDENCIES / UX CONTRACT",
    "## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS",
)


def diagnostic(
    file: str, identifier: object, rule: str, expected: object, actual: object
) -> str:
    return (
        f"{file}: [{identifier}] rule={rule}; "
        f"expected={expected!r}; actual={actual!r}"
    )


def _load_json(root: Path, relative: str) -> dict[str, Any]:
    loaded = json.loads((root / relative).read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("root must be an object")
    return loaded


def load_plan(root: Path = ROOT) -> dict[str, Any]:
    return _load_json(root, PLAN_PATH)


@dataclass(frozen=True)
class ProgramItem:
    id: str
    phase: int
    dependencies: tuple[str, ...]


@dataclass(frozen=True)
class Gate:
    id: str
    required: tuple[str, ...]


@dataclass(frozen=True)
class Program:
    version: str
    status: str
    items: dict[str, ProgramItem]
    gates: dict[str, Gate]
    scope_dependent: frozenset[str]
    raw: dict[str, Any]


def load_program(root: Path = ROOT) -> Program:
    raw = _load_json(root, PROGRAM_PATH)
    items: dict[str, ProgramItem] = {}
    for phase in raw.get("phases", []):
        for item in phase.get("work_items", []):
            work_item_id = str(item["id"])
            if work_item_id in items:
                raise ValueError(f"duplicate program work item: {work_item_id}")
            items[work_item_id] = ProgramItem(
                id=work_item_id,
                phase=int(phase["id"]),
                dependencies=tuple(
                    str(dependency) for dependency in item.get("dependencies", [])
                ),
            )
    gates: dict[str, Gate] = {}
    scope_dependent: set[str] = set()
    for gate in raw.get("gates", []):
        gate_id = str(gate["id"])
        required = gate.get("required_work_items")
        if required is None:
            required = gate.get("required_core_work_items", [])
        gates[gate_id] = Gate(
            id=gate_id,
            required=tuple(str(work_item_id) for work_item_id in required),
        )
        scope_dependent.update(
            str(entry["id"])
            for entry in gate.get("scope_dependent_work_items", [])
            if isinstance(entry, dict) and "id" in entry
        )
    return Program(
        version=str(raw.get("version", "")),
        status=str(raw.get("status", "")),
        items=items,
        gates=gates,
        scope_dependent=frozenset(scope_dependent),
        raw=raw,
    )


def identifiers(values: list[dict[str, Any]]) -> list[str]:
    return [str(value.get("id")) for value in values if isinstance(value, dict)]
