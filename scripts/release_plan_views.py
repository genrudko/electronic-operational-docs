"""Deterministic Markdown projections for canonical planning state."""

from __future__ import annotations

import json
from typing import Any

try:
    from .release_plan_model import Program
except ImportError:
    from release_plan_model import Program


def render_module_map(plan: dict[str, Any]) -> str:
    lines = [
        "# Модульная карта Demo-релиза",
        "",
        "> GENERATED VIEW. Единственный machine-readable владелец статусов — "
        "`docs/project/DEMO_RELEASE_PLAN.yaml`. Ручное изменение этого файла "
        "будет отклонено Documentation Contract.",
        "",
        "| # | Модуль | Назначение | Depth | Release | Code | Work item | "
        "Accepted slices |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for module in sorted(plan["modules"], key=lambda value: value["order"]):
        accepted = module.get("accepted") or "—"
        lines.append(
            f"| {module['order']} | `{module['id']}` | {module['name']} | "
            f"`{module['depth']}` | `{module['status']}` | `{module['code']}` | "
            f"`{module['work_item']}` | `{accepted}` |"
        )
    lines.extend(
        [
            "",
            "## Интерпретация",
            "",
            "- `Release` — готовность заявленного Demo-depth, а не наличие "
            "отдельных моделей.",
            "- `Code` — доказанное состояние реализации.",
            "- Принятый work item не остаётся в execution queue.",
            "- `READY` у `SHIFT` не означает старт работы: domain queue "
            "приостановлена до `SAFE-CONTINUATION` и отдельного решения владельца.",
            "",
        ]
    )
    return "\n".join(lines)


def render_sequence(plan: dict[str, Any], program: Program) -> str:
    modules = {item["id"]: item for item in plan["modules"]}
    statuses = {item["id"]: item["status"] for item in plan["work_items"]}
    lines = [
        "# Последовательность реализации",
        "",
        "> GENERATED VIEW. Dependency topology и статусы выводятся из "
        "`DEMO_RELEASE_PLAN.yaml` и принятого `INDUSTRIALIZATION_PROGRAM.yaml`.",
        "",
        "## 1. Топологический порядок Demo-модулей",
        "",
    ]
    for number, module_id in enumerate(plan["dependency_order"], start=1):
        dependencies = modules[module_id].get("deps", [])
        dependency_text = (
            ", ".join(f"`{dependency}`" for dependency in dependencies)
            if dependencies
            else "нет"
        )
        lines.append(
            f"{number}. `{module_id}` — зависимости: {dependency_text}."
        )
    lines.extend(
        [
            "",
            "## 2. Текущая программа исполнения",
            "",
            "`SAFE-CONTINUATION`: **ещё не достигнут**.",
            "",
            "| Фаза | Work item | Статус | Зависимости |",
            "|---:|---|---|---|",
        ]
    )
    ordered_items = sorted(
        program.items.values(), key=lambda value: (value.phase, value.id)
    )
    for item in ordered_items:
        dependency_text = (
            ", ".join(f"`{dependency}`" for dependency in item.dependencies)
            or "—"
        )
        lines.append(
            f"| {item.phase} | `{item.id}` | `{statuses[item.id]}` | "
            f"{dependency_text} |"
        )
    lines.extend(
        [
            "",
            "## 3. Предметная очередь Demo",
            "",
            f"Статус очереди: `{plan['execution']['domain_queue_status']}`.",
            "",
            "Работа `SHIFT-HANDOVER-001` и следующие предметные work items не "
            "стартуют автоматически. После достижения `SAFE-CONTINUATION` "
            "требуется отдельное явное решение владельца.",
            "",
            "| # | Work item | Модуль | Цель |",
            "|---:|---|---|---|",
        ]
    )
    for item in plan["execution"]["domain_queue"]:
        lines.append(
            f"| {item['order']} | `{item['work_item']}` | "
            f"`{item['module_id']}` | {item['goal']} |"
        )
    lines.extend(
        [
            "",
            "## 4. Принятые границы OPJ / SHIFT / CROSS-DOC",
            "",
            "- `OPJ-LIFECYCLE-001` принят: immutable registration, "
            "correction/cancellation новыми фактами и фиксация оперативно "
            "значимого результата переговоров.",
            "- `SHIFT-HANDOVER-001` остаётся отдельным не начатым work item: "
            "отчёт передачи смены и независимые подтверждения сторон.",
            "- `CROSS-DOC-001` остаётся отдельным work item общего relation "
            "engine; внутренние lifecycle-связи принятых модулей его не подменяют.",
            "",
        ]
    )
    return "\n".join(lines)


def render_checklist(plan: dict[str, Any], program: Program) -> str:
    statuses = {item["id"]: item["status"] for item in plan["work_items"]}
    lines = [
        "# Demo release master checklist",
        "",
        "> GENERATED VIEW. Checkbox и Markdown не владеют состоянием; источник — "
        "`DEMO_RELEASE_PLAN.yaml`.",
        "",
        "## 1. Demo-модули",
        "",
    ]
    for module in sorted(plan["modules"], key=lambda value: value["order"]):
        marker = "x" if module["status"] == "ACCEPTED" else " "
        accepted = (
            f"; accepted `{module['accepted']}`" if module.get("accepted") else ""
        )
        work_item_status = statuses.get(module["work_item"], "MISSING")
        lines.append(
            f"- [{marker}] `{module['id']}` / `{module['capability']}` / "
            f"`{module['acceptance']}` / `{module['depth']}` — release "
            f"`{module['status']}`, code `{module['code']}`, work item "
            f"`{module['work_item']}` (`{work_item_status}`){accepted}."
        )
    for heading, gate_id in (
        ("## 2. SAFE-CONTINUATION", "SAFE-CONTINUATION"),
        ("## 3. PILOT-READY mandatory core", "PILOT-READY"),
    ):
        lines.extend(["", heading, ""])
        for work_item_id in program.gates[gate_id].required:
            status = statuses.get(work_item_id, "MISSING")
            marker = "x" if status == "ACCEPTED" else " "
            lines.append(f"- [{marker}] `{work_item_id}` — `{status}`.")
    lines.extend(
        [
            "",
            "`PILOT-READY` дополнительно требует применимости scope-dependent "
            "work, закрытия/явного принятия рисков и отдельного решения владельца.",
            "",
        ]
    )
    return "\n".join(lines)


def render_program_markdown(raw: dict[str, Any]) -> str:
    lines = [
        "# ЭОД — программа индустриализации платформы",
        "",
        "> GENERATED HUMAN VIEW. Machine-readable definition: "
        "`docs/project/INDUSTRIALIZATION_PROGRAM.yaml`; work-item statuses: "
        "`docs/project/DEMO_RELEASE_PLAN.yaml`. Ручное изменение этого файла "
        "будет отклонено Documentation Contract.",
        "",
        f"**Версия:** `{raw['version']}`",
        f"**Дата:** `{raw['date']}`",
        f"**Источник:** `{raw['program_id']}`",
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
    lines.extend(["", "## 2. Gates", ""])
    for gate in raw.get("gates", []):
        required = gate.get("required_work_items")
        if required is None:
            required = gate.get("required_core_work_items", [])
        lines.extend(
            [
                f"### `{gate['id']}`",
                "",
                str(gate["purpose"]),
                "",
                "Обязательные work items:",
                "",
            ]
        )
        lines.extend(f"- `{work_item_id}`" for work_item_id in required)
        if gate.get("post_gate_policy"):
            lines.extend(["", "Post-gate policy:", "", "```json"])
            lines.append(json_dump(gate["post_gate_policy"]))
            lines.extend(["```", ""])
        for policy_name in (
            "critical_risk_policy",
            "browser_gate_policy",
            "residual_risk_policy",
        ):
            if gate.get(policy_name):
                lines.extend(
                    [
                        "",
                        f"{policy_name}:",
                        "",
                        "```json",
                        json_dump(gate[policy_name]),
                        "```",
                    ]
                )
        if gate.get("scope_dependent_work_items"):
            lines.extend(["", "Scope-dependent work items:", ""])
            for entry in gate["scope_dependent_work_items"]:
                lines.append(f"- `{entry['id']}` — {entry['trigger']}")
        lines.extend(["", "Acceptance:", ""])
        lines.extend(f"- {value}" for value in gate.get("acceptance", []))
        lines.append("")
    lines.extend(["## 3. Risk-ranked phases", ""])
    for phase in raw.get("phases", []):
        lines.extend(
            [
                f"### Фаза {phase['id']} — {phase['name']}",
                "",
                str(phase["objective"]),
                "",
            ]
        )
        for item in phase.get("work_items", []):
            risks = (
                ", ".join(f"`{risk}`" for risk in item.get("risks", []))
                or "—"
            )
            dependencies = (
                ", ".join(
                    f"`{dependency}`" for dependency in item.get("dependencies", [])
                )
                or "нет"
            )
            lines.extend(
                [
                    f"#### `{item['id']}`",
                    "",
                    f"- Приоритет: `{item['priority']}`.",
                    f"- Тип: `{item['type']}`.",
                    f"- Риски: {risks}.",
                    f"- Зависимости: {dependencies}.",
                    "- Acceptance:",
                ]
            )
            lines.extend(f"  - {value}" for value in item.get("acceptance", []))
            lines.append("")
    lines.extend(
        [
            "## 4. Consistency contract",
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
        ]
    )
    return "\n".join(lines)


def json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)
