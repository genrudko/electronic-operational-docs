from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLAN_PATH = ROOT / "docs/project/DEMO_RELEASE_PLAN.yaml"
CURRENT_STATE_PATH = ROOT / "docs/project/CURRENT_STATE.md"
ACCEPTANCE_HISTORY_PATH = ROOT / "docs/project/ACCEPTANCE_HISTORY.md"
BASELINE_HISTORY_PATH = ROOT / "docs/project/BASELINE_HISTORY.md"
VIEWS_PATH = ROOT / "scripts/release_plan_views.py"
EXECUTION_RENDERER_PATH = ROOT / "scripts/industrialization_execution.py"

SECURITY_HEAD = "b59a9485187dbd588c7b9f35bfd634c89344ea9d"
SECURITY_MERGE = "862b682ba19b6747ea6f4d41fd31322808140b82"
SECURITY_WORKFLOWS = {
    "auto_001a": 31392880243,
    "auto_001b": 31392880203,
    "eod_ci": 31392880182,
    "documentation_contract": 31392880153,
    "development_stack": 31392880249,
    "secret_hygiene": 31392880240,
    "dependency_provenance": 31392880171,
    "backup_restore_drill": 31392880341,
    "deployment_profile": 31392880255,
}
APPROVED_ROUTE = (
    "SAFE closure -> MODULE-REGISTRY-001 -> UX-PLATFORM-FOUNDATION-001 + "
    "PAGE-TEMPLATE-LIBRARY-001 with controlled existing-UI migration -> "
    "new product/module development -> PILOT-READY hardening in risk-based portions"
)
DOMAIN_QUEUE_STATUS = "PAUSED_PENDING_MODULE_REGISTRY_AND_UX_FOUNDATIONS"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def transition_plan() -> dict[str, object]:
    plan = json.loads(PLAN_PATH.read_text(encoding="utf-8"))
    items = {item["id"]: item for item in plan["work_items"]}
    security = items["SECURITY-BASELINE-001"]
    registry = items["MODULE-REGISTRY-001"]

    require(
        security["status"] in {"IN_PROGRESS", "ACCEPTED"},
        f"unexpected SECURITY-BASELINE state: {security['status']}",
    )
    require(
        registry["status"] in {"NOT_STARTED", "IN_PROGRESS"},
        f"unexpected MODULE-REGISTRY state: {registry['status']}",
    )

    security.clear()
    security.update(
        {
            "id": "SECURITY-BASELINE-001",
            "status": "ACCEPTED",
            "transition": {
                "from": "IN_PROGRESS",
                "to": "ACCEPTED",
                "evidence_reference": (
                    "PR #66 / explicit product-owner acceptance / ordinary merge commit"
                ),
            },
            "evidence": {
                "pr": 66,
                "exact_head": SECURITY_HEAD,
                "merge_commit": SECURITY_MERGE,
                "workflow_runs": SECURITY_WORKFLOWS,
                "owner_acceptance": "PASSED",
                "threat_model_and_negative_tests": (
                    "repository-grounded threat model accepted; production admin unrouted "
                    "fail-closed; explicit cookie/session/header decisions; real logout CSRF "
                    "negative evidence; deferred MFA/SAST/upload/module guards remain named "
                    "future work; Preview/VPS untouched"
                ),
            },
        }
    )
    registry.clear()
    registry.update(
        {
            "id": "MODULE-REGISTRY-001",
            "status": "IN_PROGRESS",
            "transition": {
                "from": "NOT_STARTED",
                "to": "IN_PROGRESS",
                "evidence_reference": (
                    "issue #67 / Draft PR #68 / platform/module-registry-001 / "
                    "explicit post-SAFE product-owner route"
                ),
            },
        }
    )

    accepted = plan["reconciliation"]["accepted_work_items"]
    if "SECURITY-BASELINE-001" not in accepted:
        accepted.append("SECURITY-BASELINE-001")
    plan["execution"]["domain_queue_status"] = DOMAIN_QUEUE_STATUS
    PLAN_PATH.write_text(
        json.dumps(plan, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return plan


def transition_current_state() -> None:
    text = CURRENT_STATE_PATH.read_text(encoding="utf-8")
    old_block = """```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 860e189bbb5bc05a6da4a7680acd5f719b4874af
active work item: SECURITY-BASELINE-001
active issue: #65
active PR: #66 / OPEN / DRAFT / NOT MERGED
active branch: security/security-baseline-001
runtime impact: NONE
preview: UNTOUCHED
```"""
    new_block = f"""```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / {SECURITY_MERGE}
active work item: MODULE-REGISTRY-001
active issue: #67
active PR: #68 / OPEN / DRAFT / NOT MERGED
active branch: platform/module-registry-001
runtime impact: REPOSITORY / DATABASE SCHEMA ONLY; LIVE RUNTIME UNTOUCHED
preview: UNTOUCHED
```"""
    require(old_block in text or new_block in text, "CURRENT_STATE header shape changed")
    text = text.replace(old_block, new_block, 1)

    start = text.find("## Active SECURITY-BASELINE-001 execution")
    end = text.find("## Accepted BACKUP-RESTORE-DRILL-001 baseline")
    if start != -1:
        require(end > start, "CURRENT_STATE accepted-backup anchor missing")
        replacement = f"""## Active MODULE-REGISTRY-001 execution

`MODULE-REGISTRY-001` выполняется только в issue #67, ветке
`platform/module-registry-001` и Draft PR #68. Accepted architecture из PR #62
реализуется как runtime control plane без dynamic Django app loading, per-site builds
или отдельной module database. Live Preview/VPS не изменяются.

`SAFE-CONTINUATION` фактически и канонически достигнут: **8/8 ACCEPTED**.
После SAFE владелец отдельно утвердил маршрут:

`{APPROVED_ROUTE}`.

Предметная очередь остаётся приостановленной на время `MODULE-REGISTRY-001` и
следующего UX foundation/page-template этапа; `SHIFT-HANDOVER-001` не стартовал.

## Accepted SECURITY-BASELINE-001 baseline

`SECURITY-BASELINE-001` принят владельцем и merged обычным merge commit:

```text
accepted PR: #66 / CLOSED / MERGED
accepted exact head: {SECURITY_HEAD}
merge commit / accepted main: {SECURITY_MERGE}
issue: #65 / CLOSED / COMPLETED
owner acceptance: PASSED
runtime impact: NONE
preview: UNTOUCHED
```

Accepted baseline включает repository-grounded threat model, fail-closed production
security settings, production `/admin/` unrouted by default, real CSRF negative
evidence и явные residual handoffs без ложных PASS для MFA/SAST/upload/module
registry. Все девять применимых exact-head workflows завершились `SUCCESS`:

```text
AUTO-001A Foundation CI:     31392880243 / SUCCESS
AUTO-001B Controller CI:     31392880203 / SUCCESS
EOD CI:                      31392880182 / SUCCESS
EOD Documentation Contract: 31392880153 / SUCCESS
EOD Development Stack:      31392880249 / SUCCESS
EOD Secret Hygiene:          31392880240 / SUCCESS
EOD Dependency Provenance:   31392880171 / SUCCESS
EOD Backup Restore Drill:    31392880341 / SUCCESS
EOD Deployment Profile:      31392880255 / SUCCESS
```

"""
        text = text[:start] + replacement + text[end:]
    CURRENT_STATE_PATH.write_text(text, encoding="utf-8")


def append_histories() -> None:
    acceptance = ACCEPTANCE_HISTORY_PATH.read_text(encoding="utf-8")
    row = (
        f"| `SECURITY-BASELINE-001` | #66 | `{SECURITY_HEAD}` | `{SECURITY_MERGE}` | "
        "repository-grounded threat model and fail-closed production security baseline accepted; Preview untouched |"
    )
    if row not in acceptance:
        lines = acceptance.splitlines()
        insert_at = next(
            (i + 1 for i, line in enumerate(lines) if "`BACKUP-RESTORE-DRILL-001` | #64" in line),
            None,
        )
        require(insert_at is not None, "ACCEPTANCE_HISTORY ledger anchor missing")
        lines.insert(insert_at, row)
        acceptance = "\n".join(lines) + "\n"
    if "## SECURITY-BASELINE-001 exact-head evidence" not in acceptance:
        acceptance += f"""
## SECURITY-BASELINE-001 exact-head evidence

Accepted exact head `{SECURITY_HEAD}` was merged as `{SECURITY_MERGE}`; issue #65
is `CLOSED / COMPLETED` and owner acceptance is `PASSED`. Exact-head workflows:
AUTO-001A `31392880243`, AUTO-001B `31392880203`, EOD CI `31392880182`,
Documentation Contract `31392880153`, Development Stack `31392880249`, Secret
Hygiene `31392880240`, Dependency Provenance `31392880171`, Backup Restore Drill
`31392880341`, Deployment Profile `31392880255` — all `SUCCESS`. Production admin
is unrouted fail-closed and deferred MFA/SAST/upload/module-registry controls were
not misrepresented as implemented. `SAFE-CONTINUATION` therefore reached 8/8.
"""
    ACCEPTANCE_HISTORY_PATH.write_text(acceptance, encoding="utf-8")

    baseline = BASELINE_HISTORY_PATH.read_text(encoding="utf-8")
    row = (
        f"| 2026-08-10 | `{SECURITY_MERGE}` | SECURITY-BASELINE-001 merge | "
        "accepted threat model / fail-closed production-security baseline; SAFE-CONTINUATION 8/8 |"
    )
    if row not in baseline:
        lines = baseline.splitlines()
        insert_at = next(
            (i + 1 for i, line in enumerate(lines) if "BACKUP-RESTORE-DRILL-001 merge" in line),
            None,
        )
        require(insert_at is not None, "BASELINE_HISTORY ledger anchor missing")
        lines.insert(insert_at, row)
        baseline = "\n".join(lines) + "\n"
    if "## Strategy decision — 2026-08-10 / post SAFE-CONTINUATION" not in baseline:
        baseline += f"""
## Strategy decision — 2026-08-10 / post SAFE-CONTINUATION

`SECURITY-BASELINE-001` принят по exact head `{SECURITY_HEAD}` и merged в
`{SECURITY_MERGE}`. `SAFE-CONTINUATION = 8/8 ACCEPTED`.

Владелец отдельно утвердил дальнейший маршрут:

`{APPROVED_ROUTE}`.

Это решение прекращает автоматическое наращивание hardening после SAFE. Текущий
активный work item — `MODULE-REGISTRY-001`; предметная очередь не стартует до
завершения registry и утверждённого UX foundation/page-template этапа.
"""
    BASELINE_HISTORY_PATH.write_text(baseline, encoding="utf-8")


def fix_post_safe_renderers() -> None:
    views = VIEWS_PATH.read_text(encoding="utf-8")
    old = '    statuses = {item["id"]: item["status"] for item in plan["work_items"]}\n    lines = ['
    new = (
        '    statuses = {item["id"]: item["status"] for item in plan["work_items"]}\n'
        '    safe_required = program.gates["SAFE-CONTINUATION"].required\n'
        '    safe_achieved = all(statuses.get(item_id) == "ACCEPTED" for item_id in safe_required)\n'
        '    lines = ['
    )
    # The first matching statuses block belongs to render_sequence after render_module_map.
    sequence_marker = "def render_sequence(plan: dict[str, Any], program: Program) -> str:\n"
    before, separator, after = views.partition(sequence_marker)
    require(bool(separator), "render_sequence marker missing")
    after = after.replace(old, new, 1)
    after = after.replace(
        '            "`SAFE-CONTINUATION`: **ещё не достигнут**.",',
        '            f"`SAFE-CONTINUATION`: **{\'достигнут\' if safe_achieved else \'ещё не достигнут\'}**.",',
        1,
    )
    after = after.replace(
        '            "Работа `SHIFT-HANDOVER-001` и следующие предметные work items не "\n'
        '            "стартуют автоматически. После достижения `SAFE-CONTINUATION` "\n'
        '            "требуется отдельное явное решение владельца.",',
        '            "Предметная очередь не стартует автоматически. После SAFE владелец "\n'
        '            "явно выбрал MODULE-REGISTRY -> UX foundation/page templates -> "\n'
        '            "product/module development; SHIFT-HANDOVER-001 пока не стартовал.",',
        1,
    )
    views = before + separator + after
    views = views.replace(
        '            "- `READY` у `SHIFT` не означает старт работы: domain queue "\n'
        '            "приостановлена до `SAFE-CONTINUATION` и отдельного решения владельца.",',
        '            "- `READY` у `SHIFT` не означает старт работы: после SAFE владелец "\n'
        '            "выбрал сначала module registry и общую UX-платформу/page templates.",',
        1,
    )
    VIEWS_PATH.write_text(views, encoding="utf-8")

    execution = EXECUTION_RENDERER_PATH.read_text(encoding="utf-8")
    execution = execution.replace(
        '        f"- `SAFE-CONTINUATION`: `{safe_done}/{safe_total}` accepted; **NOT ACHIEVED**.",',
        '        f"- `SAFE-CONTINUATION`: `{safe_done}/{safe_total}` accepted; "\n'
        '        f"**{\'ACHIEVED\' if safe_done == safe_total else \'NOT ACHIEVED\'}**.",',
        1,
    )
    execution = execution.replace(
        '        "- Предметная очередь: "\n'
        '        "`PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION`.",',
        '        "- Предметная очередь: "\n'
        '        f"`{plan.get(\'execution\', {}).get(\'domain_queue_status\', \'UNKNOWN\')}`.",',
        1,
    )
    EXECUTION_RENDERER_PATH.write_text(execution, encoding="utf-8")


def regenerate_views(plan: dict[str, object]) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from industrialization_execution import render_execution_backlog
    from release_plan_model import load_program
    from release_plan_views import render_checklist, render_module_map, render_sequence

    program = load_program(ROOT)
    (ROOT / "docs/product/MODULE_MAP.md").write_text(
        render_module_map(plan), encoding="utf-8"
    )
    (ROOT / "docs/product/IMPLEMENTATION_SEQUENCE.md").write_text(
        render_sequence(plan, program), encoding="utf-8"
    )
    (ROOT / "docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md").write_text(
        render_checklist(plan, program), encoding="utf-8"
    )
    (ROOT / "docs/project/INDUSTRIALIZATION_EXECUTION_BACKLOG.md").write_text(
        render_execution_backlog(program.raw, plan), encoding="utf-8"
    )


def main() -> None:
    plan = transition_plan()
    transition_current_state()
    append_histories()
    fix_post_safe_renderers()
    regenerate_views(plan)
    print("SAFE_CLOSURE_AND_MODULE_REGISTRY_TRANSITION=OK")


if __name__ == "__main__":
    main()
