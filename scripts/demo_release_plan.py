#!/usr/bin/env python3
"""Canonical EOD release/program state validator and derived-view generator.

The module intentionally uses only the Python standard library.  It validates:
* DEMO_RELEASE_PLAN.yaml (JSON, which is valid YAML);
* INDUSTRIALIZATION_PROGRAM.yaml (the accepted human-friendly YAML subset);
* risk-register work-item references and program dependencies;
* SAFE-CONTINUATION and PILOT-READY dependency closure;
* single-owner and accepted-state rules;
* exact generated Markdown projections.

Every diagnostic names the file, identifier, violated rule, expected state and
actual value so a failed CI run is actionable.
"""

from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = "docs/project/DEMO_RELEASE_PLAN.yaml"
PROGRAM_PATH = "docs/project/INDUSTRIALIZATION_PROGRAM.yaml"
PROGRAM_MD_PATH = "docs/project/INDUSTRIALIZATION_PROGRAM.md"
RISK_PATH = "docs/audits/PROJECT_SUSTAINABILITY_RISK_REGISTER_20260805.csv"

EXPECTED_MODULE_IDS = {
    "PLATFORM", "UX", "NORMATIVE-EVIDENCE", "MASTER-DATA",
    "PERSONNEL-AUTHORITY", "WORKPLACE-DOCS", "SCHEMES-DOCUMENTS", "OPJ",
    "SHIFT", "APPLICATION", "OPERATIONAL-ORDERS", "DEFECT", "GROUNDING",
    "SWITCHING-DOCUMENTS", "WORK-PERMIT", "PERMIT-WORK-JOURNAL",
    "ORDER-WORK-JOURNAL", "CURRENT-OPERATION-WORKS",
    "EQUIPMENT-INSPECTIONS", "EQUIPMENT-COMMISSIONING", "RZA-TM",
    "BREAKER-INTERRUPTIONS", "BATTERY-INSPECTION", "EMERGENCY-READINESS",
    "CROSS-DOC", "DASHBOARD-REPORTING", "DEMO-DATA",
}
ALLOWED_MODULE_STATUS = {
    "NOT_STARTED", "READY", "IN_PROGRESS", "BLOCKED", "AT_REVIEW",
    "ACCEPTED", "DEFERRED", "EXCLUDED",
}
ALLOWED_CODE_STATUS = {
    "IMPLEMENTED-ACCEPTED", "IMPLEMENTED-PARTIAL", "FOUNDATION-ONLY",
    "PRESENTATION-ONLY", "PLANNED-ONLY", "ABSENT", "VERIFY",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
WORK_ITEM_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)*-\d{3}$")
MODULE_MARKERS = (
    "## MODULE ID", "## НАЗНАЧЕНИЕ", "## КРИТИЧЕСКИЕ СЦЕНАРИИ",
    "## PRIMARY FACTS / DERIVED VIEWS", "## РОЛИ И ПОЛНОМОЧИЯ",
    "## ДОКУМЕНТЫ И LEGAL MODE", "## СВЯЗИ",
    "## SOURCE IDS / BENCHMARK", "## DEMO / POST-DEMO",
    "## CURRENT CODE STATUS / CAPABILITIES",
    "## DEPENDENCIES / UX CONTRACT",
    "## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS",
)
GATE_BEGIN = "<!-- BEGIN GENERATED INDUSTRIALIZATION GATE PROJECTION -->"
GATE_END = "<!-- END GENERATED INDUSTRIALIZATION GATE PROJECTION -->"


def diagnostic(
    file: str, identifier: str, rule: str, expected: object, actual: object
) -> str:
    return (
        f"{file}: [{identifier}] rule={rule}; "
        f"expected={expected!r}; actual={actual!r}"
    )


def load_plan(root: Path = ROOT) -> dict[str, Any]:
    path = root / PLAN_PATH
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError("root must be an object")
    return loaded


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


def _inline_list(value: str) -> tuple[str, ...]:
    value = value.strip()
    if not (value.startswith("[") and value.endswith("]")):
        return ()
    body = value[1:-1].strip()
    if not body:
        return ()
    return tuple(part.strip().strip("'\"") for part in body.split(",") if part.strip())


def parse_program(text: str) -> Program:
    """Parse only the stable, machine-contract subset of the accepted YAML."""
    version_match = re.search(r"(?m)^version:\s*(\S+)\s*$", text)
    status_match = re.search(r"(?m)^status:\s*(\S+)\s*$", text)
    if version_match is None or status_match is None:
        raise ValueError("program version/status missing")

    lines = text.splitlines()
    try:
        phases_start = lines.index("phases:")
        deferred_start = lines.index("deferred_modules:")
        gates_start = lines.index("gates:")
    except ValueError as exc:
        raise ValueError(f"program section missing: {exc}") from exc

    items: dict[str, ProgramItem] = {}
    current_phase: int | None = None
    i = phases_start + 1
    while i < deferred_start:
        line = lines[i]
        phase_match = re.fullmatch(r"  - id:\s*(\d+)\s*", line)
        if phase_match:
            current_phase = int(phase_match.group(1))
            i += 1
            continue
        item_match = re.fullmatch(r"      - id:\s*([A-Z][A-Z0-9-]+-\d{3})\s*", line)
        if item_match:
            if current_phase is None:
                raise ValueError(f"work item before phase: {item_match.group(1)}")
            wid = item_match.group(1)
            deps: tuple[str, ...] = ()
            j = i + 1
            while j < deferred_start:
                nxt = lines[j]
                if re.fullmatch(r"      - id:\s*[A-Z][A-Z0-9-]+-\d{3}\s*", nxt):
                    break
                if re.fullmatch(r"  - id:\s*\d+\s*", nxt):
                    break
                inline = re.fullmatch(r"        dependencies:\s*(\[.*\])\s*", nxt)
                if inline:
                    deps = _inline_list(inline.group(1))
                elif nxt == "        dependencies:":
                    block: list[str] = []
                    k = j + 1
                    while k < deferred_start:
                        dep_match = re.fullmatch(
                            r"          -\s*([A-Z][A-Z0-9-]+-\d{3})\s*", lines[k]
                        )
                        if dep_match is None:
                            break
                        block.append(dep_match.group(1))
                        k += 1
                    deps = tuple(block)
                j += 1
            if wid in items:
                raise ValueError(f"duplicate program work item: {wid}")
            items[wid] = ProgramItem(wid, current_phase, deps)
        i += 1

    gate_lines = lines[gates_start + 1 : phases_start]
    gates: dict[str, Gate] = {}
    scope_dependent: set[str] = set()
    current_gate: str | None = None
    list_target: str | None = None
    for line in gate_lines:
        gate_match = re.fullmatch(r"  - id:\s*([A-Z][A-Z0-9-]+)\s*", line)
        if gate_match:
            current_gate = gate_match.group(1)
            list_target = None
            continue
        if line.strip() in {"required_work_items:", "required_core_work_items:"}:
            list_target = line.strip().removesuffix(":")
            if current_gate:
                gates[current_gate] = Gate(current_gate, ())
            continue
        if line.strip() == "scope_dependent_work_items:":
            list_target = "scope_dependent_work_items"
            continue
        if list_target in {"required_work_items", "required_core_work_items"}:
            item_match = re.fullmatch(r"      -\s*([A-Z][A-Z0-9-]+-\d{3})\s*", line)
            if item_match and current_gate:
                gate = gates[current_gate]
                gates[current_gate] = Gate(gate.id, gate.required + (item_match.group(1),))
        elif list_target == "scope_dependent_work_items":
            item_match = re.fullmatch(
                r"      - id:\s*([A-Z][A-Z0-9-]+-\d{3})\s*", line
            )
            if item_match:
                scope_dependent.add(item_match.group(1))

    return Program(
        version=version_match.group(1),
        status=status_match.group(1),
        items=items,
        gates=gates,
        scope_dependent=frozenset(scope_dependent),
    )


def parse_program_object(raw: dict[str, Any]) -> Program:
    items: dict[str, ProgramItem] = {}
    for phase in raw.get("phases", []):
        phase_id = int(phase["id"])
        for item in phase.get("work_items", []):
            wid = str(item["id"])
            if wid in items:
                raise ValueError(f"duplicate program work item: {wid}")
            items[wid] = ProgramItem(
                wid,
                phase_id,
                tuple(str(dep) for dep in item.get("dependencies", [])),
            )
    gates: dict[str, Gate] = {}
    scope_dependent: set[str] = set()
    for gate in raw.get("gates", []):
        gid = str(gate["id"])
        required = gate.get("required_work_items")
        if required is None:
            required = gate.get("required_core_work_items", [])
        gates[gid] = Gate(gid, tuple(str(wid) for wid in required))
        for entry in gate.get("scope_dependent_work_items", []):
            if isinstance(entry, dict) and "id" in entry:
                scope_dependent.add(str(entry["id"]))
    return Program(
        version=str(raw.get("version", "")),
        status=str(raw.get("status", "")),
        items=items,
        gates=gates,
        scope_dependent=frozenset(scope_dependent),
    )


def load_program_raw(root: Path = ROOT) -> dict[str, Any] | None:
    text = (root / PROGRAM_PATH).read_text(encoding="utf-8")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, dict):
        raise ValueError("program root must be an object")
    return raw


def load_program(root: Path = ROOT) -> Program:
    text = (root / PROGRAM_PATH).read_text(encoding="utf-8")
    try:
        raw = json.loads(text)
    except json.JSONDecodeError:
        return parse_program(text)
    if not isinstance(raw, dict):
        raise ValueError("program root must be an object")
    return parse_program_object(raw)


def _split_work_item_refs(raw: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"\s*->\s*|\s*\|\s*", raw or "")
        if part.strip()
    ]


def render_module_map(plan: dict[str, Any]) -> str:
    lines = [
        "# Модульная карта Demo-релиза",
        "",
        "> GENERATED VIEW. Единственный machine-readable владелец статусов — "
        "`docs/project/DEMO_RELEASE_PLAN.yaml`. Ручное изменение этого файла "
        "будет отклонено Documentation Contract.",
        "",
        "| # | Модуль | Назначение | Depth | Release | Code | Work item | Accepted slices |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for m in sorted(plan["modules"], key=lambda item: item["order"]):
        accepted = m.get("accepted") or "—"
        lines.append(
            f"| {m['order']} | `{m['id']}` | {m['name']} | `{m['depth']}` | "
            f"`{m['status']}` | `{m['code']}` | `{m['work_item']}` | `{accepted}` |"
        )
    lines += [
        "",
        "## Интерпретация",
        "",
        "- `Release` — готовность заявленного Demo-depth, а не наличие отдельных моделей.",
        "- `Code` — доказанное состояние реализации.",
        "- Принятый work item не остаётся в execution queue.",
        "- `READY` у `SHIFT` не означает старт работы: domain queue приостановлена до "
        "`SAFE-CONTINUATION` и отдельного решения владельца.",
        "",
    ]
    return "\n".join(lines)


def render_sequence(plan: dict[str, Any], program: Program) -> str:
    module_by_id = {m["id"]: m for m in plan["modules"]}
    status_by_id = {w["id"]: w["status"] for w in plan["work_items"]}
    lines = [
        "# Последовательность реализации",
        "",
        "> GENERATED VIEW. Dependency topology и статусы выводятся из "
        "`DEMO_RELEASE_PLAN.yaml` и принятого `INDUSTRIALIZATION_PROGRAM.yaml`.",
        "",
        "## 1. Топологический порядок Demo-модулей",
        "",
    ]
    for number, mid in enumerate(plan["dependency_order"], 1):
        deps = module_by_id[mid].get("deps", [])
        dep_text = ", ".join(f"`{dep}`" for dep in deps) if deps else "нет"
        lines.append(f"{number}. `{mid}` — зависимости: {dep_text}.")
    lines += [
        "",
        "## 2. Текущая программа исполнения",
        "",
        "`SAFE-CONTINUATION`: **ещё не достигнут**.",
        "",
        "| Фаза | Work item | Статус | Зависимости |",
        "|---:|---|---|---|",
    ]
    for item in sorted(program.items.values(), key=lambda x: (x.phase, x.id)):
        deps = ", ".join(f"`{dep}`" for dep in item.dependencies) or "—"
        lines.append(
            f"| {item.phase} | `{item.id}` | `{status_by_id[item.id]}` | {deps} |"
        )
    lines += [
        "",
        "## 3. Предметная очередь Demo",
        "",
        f"Статус очереди: `{plan['execution']['domain_queue_status']}`.",
        "",
        "Работа `SHIFT-HANDOVER-001` и следующие предметные work items не стартуют "
        "автоматически. После достижения `SAFE-CONTINUATION` требуется отдельное "
        "явное решение владельца.",
        "",
        "| # | Work item | Модуль | Цель |",
        "|---:|---|---|---|",
    ]
    for item in plan["execution"]["domain_queue"]:
        lines.append(
            f"| {item['order']} | `{item['work_item']}` | `{item['module_id']}` | "
            f"{item['goal']} |"
        )
    lines += [
        "",
        "## 4. Принятые границы OPJ / SHIFT / CROSS-DOC",
        "",
        "- `OPJ-LIFECYCLE-001` принят: immutable registration, correction/cancellation "
        "новыми фактами и фиксация оперативно значимого результата переговоров.",
        "- `SHIFT-HANDOVER-001` остаётся отдельным не начатым work item: отчёт передачи "
        "смены и независимые подтверждения сторон.",
        "- `CROSS-DOC-001` остаётся отдельным work item общего relation engine; "
        "внутренние lifecycle-связи принятых модулей его не подменяют.",
        "",
    ]
    return "\n".join(lines)


def render_checklist(plan: dict[str, Any], program: Program) -> str:
    status_by_id = {w["id"]: w["status"] for w in plan["work_items"]}
    lines = [
        "# Demo release master checklist",
        "",
        "> GENERATED VIEW. Checkbox и Markdown не владеют состоянием; источник — "
        "`DEMO_RELEASE_PLAN.yaml`.",
        "",
        "## 1. Demo-модули",
        "",
    ]
    for m in sorted(plan["modules"], key=lambda item: item["order"]):
        mark = "x" if m["status"] == "ACCEPTED" else " "
        accepted = f"; accepted `{m['accepted']}`" if m.get("accepted") else ""
        lines.append(
            f"- [{mark}] `{m['id']}` / `{m['capability']}` / `{m['acceptance']}` / "
            f"`{m['depth']}` — release `{m['status']}`, code `{m['code']}`, "
            f"work item `{m['work_item']}` (`{status_by_id.get(m['work_item'], 'MISSING')}`){accepted}."
        )
    lines += ["", "## 2. SAFE-CONTINUATION", ""]
    for wid in program.gates["SAFE-CONTINUATION"].required:
        status = status_by_id.get(wid, "MISSING")
        mark = "x" if status == "ACCEPTED" else " "
        lines.append(f"- [{mark}] `{wid}` — `{status}`.")
    lines += ["", "## 3. PILOT-READY mandatory core", ""]
    for wid in program.gates["PILOT-READY"].required:
        status = status_by_id.get(wid, "MISSING")
        mark = "x" if status == "ACCEPTED" else " "
        lines.append(f"- [{mark}] `{wid}` — `{status}`.")
    lines += [
        "",
        "`PILOT-READY` дополнительно требует применимости scope-dependent work, "
        "закрытия/явного принятия рисков и отдельного решения владельца.",
        "",
    ]
    return "\n".join(lines)


def render_program_markdown(raw: dict[str, Any]) -> str:
    program = parse_program_object(raw)
    lines = [
        "# ЭОД — программа индустриализации платформы",
        "",
        "> GENERATED HUMAN VIEW. Machine-readable definition: "
        "`docs/project/INDUSTRIALIZATION_PROGRAM.yaml`; work-item statuses: "
        "`docs/project/DEMO_RELEASE_PLAN.yaml`. Ручное изменение этого файла "
        "будет отклонено Documentation Contract.",
        "",
        f"**Версия:** `{raw['version']}`  ",
        f"**Дата:** `{raw['date']}`  ",
        f"**Источник:** `{raw['program_id']}`  ",
        f"**Статус:** `{raw['status']}`",
        "",
        "## 1. Принципы",
        "",
    ]
    for principle in raw.get("principles", []):
        lines.append(
            f"- **[{principle['classification']}] `{principle['id']}`:** "
            f"{principle['statement']}"
        )

    lines += ["", "## 2. Gates", ""]
    for gate in raw.get("gates", []):
        gid = gate["id"]
        required = gate.get("required_work_items", gate.get("required_core_work_items", []))
        lines += [
            f"### `{gid}`",
            "",
            gate["purpose"],
            "",
            "Обязательные work items:",
            "",
        ]
        for wid in required:
            lines.append(f"- `{wid}`")
        if gate.get("critical_risk_policy"):
            lines += ["", "Critical-risk policy:", ""]
            for key, value in gate["critical_risk_policy"].items():
                lines.append(f"- `{key}`: `{value}`")
        if gate.get("scope_dependent_work_items"):
            lines += ["", "Scope-dependent work items:", ""]
            for entry in gate["scope_dependent_work_items"]:
                lines.append(f"- `{entry['id']}` — {entry['trigger']}")
        if gate.get("browser_gate_policy"):
            policy = gate["browser_gate_policy"]
            lines += [
                "",
                "Browser-gate policy:",
                "",
                f"- route scope: `{policy['route_scope']}`;",
                f"- screen scope: `{', '.join(policy['screen_scope'])}`;",
                f"- general UX refactor required: `{str(policy['requires_general_ux_refactor']).lower()}`;",
                "- UX foundation/page templates trigger: "
                f"`{', '.join(policy['ux_foundation_and_page_templates_required_when'])}`.",
            ]
        if gate.get("residual_risk_policy"):
            lines += ["", "Residual-risk policy:", ""]
            for key, value in gate["residual_risk_policy"].items():
                lines.append(f"- `{key}`: `{value}`")
        lines += ["", "Acceptance:", ""]
        for criterion in gate.get("acceptance", []):
            lines.append(f"- {criterion}")
        if gate.get("post_gate_policy"):
            policy = gate["post_gate_policy"]
            lines += [
                "",
                "Post-gate boundary:",
                "",
                "- limited existing contour work: only by "
                f"`{policy['limited_existing_contour_work']['allowed_only_by']}` "
                f"(example `{policy['limited_existing_contour_work']['example']}`);",
                "- mass new journals/modules only after "
                + ", ".join(
                    f"`{wid}`"
                    for wid in policy["mass_new_journals_and_modules"]["allowed_after"]
                )
                + ";",
                "- exception requires "
                + ", ".join(
                    f"`{item}`" for item in policy["exception"]["requires"]
                )
                + ".",
            ]
        lines.append("")

    lines += ["## 3. Risk-ranked phases", ""]
    for phase in raw.get("phases", []):
        lines += [
            f"### Фаза {phase['id']} — {phase['name']}",
            "",
            phase["objective"],
            "",
        ]
        for item in phase.get("work_items", []):
            deps = ", ".join(f"`{dep}`" for dep in item.get("dependencies", [])) or "нет"
            risks = ", ".join(f"`{risk}`" for risk in item.get("risks", [])) or "нет"
            lines += [
                f"#### `{item['id']}`",
                "",
                f"- Приоритет: `{item['priority']}`.",
                f"- Тип: `{item['type']}`.",
                f"- Риски: {risks}.",
                f"- Зависимости: {deps}.",
                "- Acceptance:",
            ]
            for criterion in item.get("acceptance", []):
                lines.append(f"  - {criterion}")
            lines.append("")

    lines += ["## 4. Deferred modules", ""]
    for item in raw.get("deferred_modules", []):
        deps = item.get("earliest_dependencies", item.get("dependencies", []))
        dep_text = ", ".join(f"`{dep}`" for dep in deps) or "нет"
        lines.append(
            f"- `{item['id']}` / `{item['classification']}` / `{item['target']}`; "
            f"dependencies: {dep_text}. {item['notes']}"
        )

    lines += [
        "",
        "## 5. Consistency contract",
        "",
        "- Work-item IDs are unique.",
        "- Every risk-register `proposed_work_item` resolves.",
        "- Every dependency resolves and normal phase ordering is forward-safe.",
        "- Gate work items exist.",
        "- `PILOT-READY` mandatory core is direct/transitively closed.",
        "- Hidden scope-dependent mandatory dependencies are forbidden.",
        "- Markdown/YAML gate projection and required derived views are exact.",
        "- Work-item/module accepted status and canonical ownership are fail-closed.",
        "",
        render_gate_projection(program),
        "",
    ]
    return "\n".join(lines)


def render_gate_projection(program: Program) -> str:
    lines = [
        GATE_BEGIN,
        "## Machine-checked gate projection",
        "",
        f"- Program version: `{program.version}`.",
        f"- Program status: `{program.status}`.",
        f"- Work items: `{len(program.items)}`.",
        "",
    ]
    for gate_id in ("SAFE-CONTINUATION", "PILOT-READY"):
        gate = program.gates[gate_id]
        lines += [f"### `{gate_id}`", ""]
        for wid in gate.required:
            lines.append(f"- `{wid}`")
        lines.append("")
    lines += ["### `PILOT-READY` scope-dependent work items", ""]
    for wid in sorted(program.scope_dependent):
        lines.append(f"- `{wid}`")
    lines += ["", GATE_END]
    return "\n".join(lines)


def replace_gate_projection(markdown: str, projection: str) -> str:
    if GATE_BEGIN in markdown or GATE_END in markdown:
        if markdown.count(GATE_BEGIN) != 1 or markdown.count(GATE_END) != 1:
            raise ValueError("gate projection markers must occur exactly once")
        before, rest = markdown.split(GATE_BEGIN, 1)
        _, after = rest.split(GATE_END, 1)
        return before.rstrip() + "\n\n" + projection + after
    return markdown.rstrip() + "\n\n" + projection + "\n"


def validate_plan(plan: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    file = PLAN_PATH
    if plan.get("schema") != 2:
        errors.append(diagnostic(file, "schema", "plan-schema", 2, plan.get("schema")))
    if plan.get("baseline_status") != "ACCEPTED":
        errors.append(diagnostic(file, "DEMO-RELEASE", "baseline-status", "ACCEPTED", plan.get("baseline_status")))

    modules = plan.get("modules")
    if not isinstance(modules, list):
        return errors + [diagnostic(file, "modules", "module-list", "list", type(modules).__name__)]
    ids = [m.get("id") for m in modules if isinstance(m, dict)]
    if len(ids) != len(set(ids)):
        errors.append(diagnostic(file, "modules", "module-id-uniqueness", "unique", ids))
    if set(ids) != EXPECTED_MODULE_IDS:
        errors.append(diagnostic(file, "modules", "module-set", sorted(EXPECTED_MODULE_IDS), sorted(set(ids))))
    by_id = {m["id"]: m for m in modules if isinstance(m, dict) and "id" in m}

    work_items = plan.get("work_items")
    if not isinstance(work_items, list):
        return errors + [diagnostic(file, "work_items", "work-item-list", "list", type(work_items).__name__)]
    work_ids = [w.get("id") for w in work_items if isinstance(w, dict)]
    if len(work_ids) != len(set(work_ids)):
        errors.append(diagnostic(file, "work_items", "work-item-id-uniqueness", "unique", work_ids))
    work_by_id = {w["id"]: w for w in work_items if isinstance(w, dict) and "id" in w}
    for wid, item in work_by_id.items():
        if not WORK_ITEM_RE.fullmatch(wid):
            errors.append(diagnostic(file, wid, "work-item-id-format", WORK_ITEM_RE.pattern, wid))
        if item.get("status") not in ALLOWED_MODULE_STATUS:
            errors.append(diagnostic(file, wid, "work-item-status", sorted(ALLOWED_MODULE_STATUS), item.get("status")))
        if item.get("status") == "ACCEPTED":
            evidence = item.get("evidence")
            if not isinstance(evidence, dict):
                errors.append(diagnostic(file, wid, "accepted-evidence", "object", evidence))
            else:
                for key in ("exact_head", "merge_commit"):
                    if not SHA_RE.fullmatch(str(evidence.get(key, ""))):
                        errors.append(diagnostic(file, wid, f"accepted-{key}", "40 lowercase hex", evidence.get(key)))

    reconciled_accepted = plan.get("reconciliation", {}).get(
        "accepted_work_items", []
    )
    for wid in reconciled_accepted:
        item = work_by_id.get(wid)
        if item is None:
            errors.append(
                diagnostic(
                    file,
                    wid,
                    "reconciled-accepted-work-item-exists",
                    "work item projection",
                    "missing",
                )
            )
            continue
        if item.get("status") != "ACCEPTED":
            errors.append(
                diagnostic(
                    file,
                    wid,
                    "stale-accepted-status",
                    "ACCEPTED",
                    item.get("status"),
                )
            )
        module = next(
            (entry for entry in modules if entry.get("work_item") == wid),
            None,
        )
        if module is not None and module.get("status") != "ACCEPTED":
            errors.append(
                diagnostic(
                    file,
                    module.get("id", wid),
                    "stale-accepted-status",
                    "module ACCEPTED",
                    module.get("status"),
                )
            )

    for mid, module in by_id.items():
        if module.get("status") not in ALLOWED_MODULE_STATUS:
            errors.append(diagnostic(file, mid, "module-status", sorted(ALLOWED_MODULE_STATUS), module.get("status")))
        if module.get("code") not in ALLOWED_CODE_STATUS:
            errors.append(diagnostic(file, mid, "module-code-status", sorted(ALLOWED_CODE_STATUS), module.get("code")))
        wid = module.get("work_item")
        if wid not in work_by_id:
            errors.append(diagnostic(file, mid, "module-work-item-reference", "existing work item", wid))
        for dep in module.get("deps", []):
            if dep not in by_id:
                errors.append(diagnostic(file, mid, "module-dependency-reference", "existing module", dep))
        if module.get("status") == "ACCEPTED":
            if module.get("code") != "IMPLEMENTED-ACCEPTED":
                errors.append(diagnostic(file, mid, "accepted-module-code", "IMPLEMENTED-ACCEPTED", module.get("code")))
            if not module.get("accepted"):
                errors.append(diagnostic(file, mid, "accepted-module-capabilities", "non-empty", module.get("accepted")))
            if wid in work_by_id and work_by_id[wid].get("status") != "ACCEPTED":
                errors.append(diagnostic(file, mid, "stale-accepted-status", "work item ACCEPTED", work_by_id[wid].get("status")))

        contract = root / str(module.get("contract", ""))
        if not contract.is_file():
            errors.append(diagnostic(file, mid, "module-contract-exists", module.get("contract"), "missing"))
        else:
            text = contract.read_text(encoding="utf-8")
            if f"`{mid}`" not in text:
                errors.append(diagnostic(module["contract"], mid, "contract-module-id", f"`{mid}`", "missing"))
            for marker in MODULE_MARKERS:
                if marker not in text:
                    errors.append(diagnostic(module["contract"], mid, "contract-marker", marker, "missing"))

    dep_order = plan.get("dependency_order", [])
    if set(dep_order) != EXPECTED_MODULE_IDS or len(dep_order) != len(set(dep_order)):
        errors.append(diagnostic(file, "dependency_order", "dependency-order-membership", sorted(EXPECTED_MODULE_IDS), dep_order))
    else:
        position = {mid: index for index, mid in enumerate(dep_order)}
        for mid, module in by_id.items():
            for dep in module.get("deps", []):
                if dep in position and position[dep] >= position[mid]:
                    errors.append(diagnostic(file, mid, "dependency-topology", f"{dep} before {mid}", dep_order))

    queue = plan.get("execution", {}).get("domain_queue", [])
    queue_orders = [item.get("order") for item in queue if isinstance(item, dict)]
    if queue_orders != list(range(1, len(queue_orders) + 1)):
        errors.append(diagnostic(file, "domain_queue", "queue-order", list(range(1, len(queue_orders) + 1)), queue_orders))
    for item in queue:
        wid = item.get("work_item")
        if wid not in work_by_id:
            errors.append(diagnostic(file, str(wid), "queue-work-item-reference", "existing work item", wid))
        elif work_by_id[wid].get("status") == "ACCEPTED":
            errors.append(diagnostic(file, wid, "accepted-work-item-not-queued", "absent from queue", "present"))
        if item.get("module_id") not in by_id:
            errors.append(diagnostic(file, str(wid), "queue-module-reference", "existing module", item.get("module_id")))

    if plan.get("execution", {}).get("domain_queue_status") != "PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION":
        errors.append(diagnostic(file, "domain_queue", "safe-continuation-pause", "PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION", plan.get("execution", {}).get("domain_queue_status")))

    return errors


def _transitive_dependencies(program: Program, start: Iterable[str]) -> set[str]:
    found: set[str] = set()
    stack = list(start)
    while stack:
        wid = stack.pop()
        item = program.items.get(wid)
        if item is None:
            continue
        for dep in item.dependencies:
            if dep not in found:
                found.add(dep)
                stack.append(dep)
    return found


def validate_program(program: Program, plan: dict[str, Any], root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    file = PROGRAM_PATH
    if program.version != "1.0":
        errors.append(diagnostic(file, "version", "accepted-program-version", "1.0", program.version))
    if program.status != "ACCEPTED":
        errors.append(diagnostic(file, "status", "accepted-program-status", "ACCEPTED", program.status))
    if len(program.items) != 30:
        errors.append(diagnostic(file, "phases", "program-work-item-count", 30, len(program.items)))

    status_by_id = {w["id"]: w["status"] for w in plan.get("work_items", []) if isinstance(w, dict) and "id" in w}
    for wid, item in program.items.items():
        if wid not in status_by_id:
            errors.append(diagnostic(PLAN_PATH, wid, "industrialization-status-projection", "work item status exists", "missing"))
        for dep in item.dependencies:
            if dep not in program.items:
                errors.append(diagnostic(file, wid, "dependency-reference", "existing work item", dep))
            elif program.items[dep].phase > item.phase:
                errors.append(diagnostic(file, wid, "phase-order", f"dependency phase <= {item.phase}", f"{dep} phase {program.items[dep].phase}"))

    for gate_id in ("SAFE-CONTINUATION", "PILOT-READY"):
        gate = program.gates.get(gate_id)
        if gate is None:
            errors.append(diagnostic(file, gate_id, "gate-exists", "present", "missing"))
            continue
        for wid in gate.required:
            if wid not in program.items:
                errors.append(diagnostic(file, gate_id, "gate-work-item-reference", "existing work item", wid))

    pilot = program.gates.get("PILOT-READY")
    if pilot:
        core = set(pilot.required)
        closure = _transitive_dependencies(program, core)
        for dep in sorted(closure):
            if dep not in program.items:
                errors.append(diagnostic(file, "PILOT-READY", "mandatory-core-dependency-exists", "program work item", dep))
            elif dep not in core:
                errors.append(diagnostic(file, "PILOT-READY", "mandatory-core-transitive-closure", "dependency inside required_core_work_items", dep))
                if dep in program.scope_dependent:
                    errors.append(diagnostic(file, "PILOT-READY", "hidden-scope-dependent-dependency", "no scope-dependent dependency in mandatory core closure", dep))

    risk_path = root / RISK_PATH
    if not risk_path.is_file():
        errors.append(diagnostic(RISK_PATH, "risk-register", "risk-register-exists", "file", "missing"))
    else:
        with risk_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle, delimiter=";"))
        for row in rows:
            rid = row.get("identifier", "<unknown>")
            for wid in _split_work_item_refs(row.get("proposed_work_item", "")):
                if wid not in program.items:
                    errors.append(diagnostic(RISK_PATH, rid, "risk-proposed-work-item-reference", "existing program work item", wid))

    return errors


def validate_views(plan: dict[str, Any], program: Program, root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    expected = {
        plan["views"]["module_map"]: render_module_map(plan),
        plan["views"]["sequence"]: render_sequence(plan, program),
        plan["views"]["checklist"]: render_checklist(plan, program),
    }
    for relative, content in expected.items():
        path = root / relative
        actual = path.read_text(encoding="utf-8") if path.is_file() else None
        if actual != content:
            errors.append(diagnostic(relative, "derived-view", "exact-generated-projection", "generator output", "missing or stale"))

    md_path = root / PROGRAM_MD_PATH
    if not md_path.is_file():
        errors.append(diagnostic(PROGRAM_MD_PATH, "program-markdown", "markdown-projection-file", "present", "missing"))
    else:
        raw = load_program_raw(root)
        text = md_path.read_text(encoding="utf-8")
        if raw is None:
            expected_projection = render_gate_projection(program)
            if GATE_BEGIN not in text or GATE_END not in text:
                errors.append(diagnostic(PROGRAM_MD_PATH, "gates", "markdown-yaml-projection", expected_projection, "markers missing"))
            else:
                actual_projection = GATE_BEGIN + text.split(GATE_BEGIN, 1)[1].split(GATE_END, 1)[0] + GATE_END
                if actual_projection != expected_projection:
                    errors.append(diagnostic(PROGRAM_MD_PATH, "gates", "markdown-yaml-projection", expected_projection, actual_projection))
        else:
            expected_md = render_program_markdown(raw)
            if text != expected_md:
                errors.append(diagnostic(PROGRAM_MD_PATH, "program-markdown", "exact-generated-projection", "generator output", "missing or stale"))
    return errors


def validate_repository(root: Path = ROOT) -> list[str]:
    errors: list[str] = []
    try:
        plan = load_plan(root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        return [diagnostic(PLAN_PATH, "load", "plan-load", "valid JSON object", str(exc))]
    errors.extend(validate_plan(plan, root))
    try:
        program = load_program(root)
    except (OSError, ValueError) as exc:
        return errors + [diagnostic(PROGRAM_PATH, "load", "program-load", "accepted YAML contract", str(exc))]
    errors.extend(validate_program(program, plan, root))
    errors.extend(validate_views(plan, program, root))
    return errors


def main() -> int:
    errors = validate_repository(ROOT)
    if errors:
        print("Demo release / industrialization state contract: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    plan = load_plan(ROOT)
    program = load_program(ROOT)
    print("Demo release / industrialization state contract: OK")
    print(f"Modules: {len(plan['modules'])}")
    print(f"Work-item status projections: {len(plan['work_items'])}")
    print(f"Industrialization work items: {len(program.items)}")
    print(f"PILOT-READY mandatory core: {len(program.gates['PILOT-READY'].required)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
