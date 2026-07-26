# ЭОД — текущий handoff

**Обновлено:** 26.07.2026

```text
repository:
genrudko/electronic-operational-docs

accepted application baseline:
main / 937d2cd2b187c17fac3088ccfc52079fc4608306

current main history HEAD:
b75db8bc073e4b02a3254512e9b99d00f3e6e0e2

last accepted work item:
PLAN-001 / PR #7 / MERGED / ACCEPTED

current work:
DEFECT-001 — Source-bound Equipment Defect Journal Vertical Slice

branch:
feature/defect-001-equipment-defect-journal

PR:
#16 / OPEN / DRAFT / NOT MERGED
```

## 1. Accepted foundation

- AUTO-001A/B are accepted and practically verified.
- Trusted controller deploys an exact PR SHA only to development.
- Preview is isolated.
- PLAN-001 evidence and classifier repair are accepted and merged.
- The first product vertical slice is the equipment defect journal.

## 2. Current implementation

Draft PR #16 contains:

1. exact published type `journal-equipment-defects`;
2. source-bound contract for `И-00-007-ОР-2025 версия 2`, section 11,
   appendix 8;
3. exact six-column registry and print form;
4. mandatory equipment link and dispatcher-name snapshot;
5. separate discovered/registered employees;
6. roles `DISCOVERED_BY`, `OPERATIONS_RESPONSIBLE`,
   `RESOLUTION_RESPONSIBLE`, `OPERATIONAL_ACKNOWLEDGER`;
7. lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
8. separate deadline confirmation, extension, resolution, acknowledgement and
   close actions;
9. immutable action evidence with employee/position/time/version/snapshot/SHA-256;
10. minimum source-bound volume without cloning unresolved records;
11. explicit operational-log entry link and reverse UI action;
12. deterministic five-state presentation data;
13. focused tests, including PostgreSQL numbering concurrency;
14. generic-route guard forcing defect work into the dedicated UI;
15. canonical documentation update.

Detailed contract: `docs/project/DEFECT_001_IMPLEMENTATION.md`.

## 3. Current status

```text
implementation: IN PROGRESS
focused CI: PENDING FINAL EXACT HEAD
full PostgreSQL suite: PENDING FINAL EXACT HEAD
five exact-head workflows: PENDING
development deployment: NOT STARTED
preview: UNTOUCHED
user acceptance: PENDING
merge authorization: ABSENT
```

Do not interpret a source commit, a partial workflow or a green infrastructure job
as product acceptance.

## 4. Required process

```text
final GitHub exact head
→ focused regression result
→ one full PostgreSQL suite
→ five green exact-head workflows
→ label vps-development-refresh
→ trusted AUTO-001B deployment
→ exact-SHA controller evidence and health
→ user development UI review
→ separate explicit merge command
```

The user does not edit code, run tests, collect logs, operate the VPS or apply
patches. VPS is not a source of code.

## 5. Runtime facts

```text
preview:
eod-preview / 127.0.0.1:8765 / eod_preview

development:
eod-development / 127.0.0.1:8766 / eod_development

controller:
/usr/local/sbin/eod-development-controller

release root:
/srv/eod/automation/releases

state:
/srv/eod/automation/state
```

Final controller evidence must show:

```text
current_sha=<final exact PR head>
transaction=NONE
pending_run_id=NONE
preview=UNTOUCHED
```

## 6. Source-bound acceptance scenario

1. Open a registered operational-log entry about an identified issue.
2. Select `Создать дефект`.
3. Confirm equipment and the person who discovered the defect.
4. Register the defect description.
5. Confirm the deadline and operations-responsible person.
6. Extend the deadline once and verify the preserved history.
7. Confirm the resolution date, responsible person and completed work.
8. A member of operational staff selects `Ознакомиться`.
9. Close the defect.
10. Verify registry, card, history, operational-log link, terminal lock and print
    representation.

## 7. Exit criteria

```text
source-bound published type: PRESENT
dedicated journal UI: PRESENT
create/update/extend/resolve/acknowledge/close: WORKING
equipment mandatory link: WORKING
operational-log link: WORKING
immutable revisions/audit: WORKING
terminal lock: WORKING
print view: PRESENT
deterministic presentation data: PRESENT
focused tests: PASS
full PostgreSQL suite: PASS
five exact-head workflows: PASS
development exact-SHA deployment: HEALTHY
preview: UNTOUCHED
manual VPS actions by user: ZERO
```

Only the first nine implementation items are presently represented in branch code.
The PASS/HEALTHY items remain pending evidence.

## 8. Prohibited actions

- merge without a separate user command;
- automatic merge;
- preview write;
- new infrastructure/controller/gateway/workflow for DEFECT-001;
- manual user VPS commands;
- real enterprise personal or operational data;
- claims of paperless legal equivalence, УКЭП or industrial readiness;
- scope expansion into a universal timeline, archive subsystem or other journals.
