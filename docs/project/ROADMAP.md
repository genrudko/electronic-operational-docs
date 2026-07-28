# ЭОД — roadmap

**Актуализировано:** 26.07.2026

## Принцип

Roadmap управляется evidence и acceptance. Исторический номер patch не
доказывает готовность. Каждый work item имеет exact head, CI, runtime evidence,
user decision и явный merge gate.

## Current baseline

```text
current main:
b75db8bc073e4b02a3254512e9b99d00f3e6e0e2

accepted application baseline:
937d2cd2b187c17fac3088ccfc52079fc4608306

active work item:
DEFECT-001 / Draft PR #16 / NOT MERGED
```

## Завершено

| Этап | Статус | Основной результат |
|---|---|---|
| INFRA-001–003 | Accepted | Linux/PostgreSQL CI, preview, isolated development |
| DOCS-001–003 | Accepted | Canonical docs and provisional UX contract |
| QUALITY-001 | Accepted | Full `python manage.py test apps` discovery |
| AUTO-000 | Accepted | Automation/security/acceptance contract |
| AUTO-001A | Accepted | Trusted controller foundation |
| AUTO-001B | Accepted | Restricted exact-SHA VPS development controller |
| AUTO-001B repair | Accepted | Trusted validator module entrypoint |
| PLAN-001 / PR #7 | Accepted and merged | Exact-SHA evidence, classifier repair and first slice decision |

## Текущий product stage

### DEFECT-001 — Source-bound Equipment Defect Journal Vertical Slice

```text
branch:
feature/defect-001-equipment-defect-journal

Draft PR:
#16

status:
IMPLEMENTATION IN PROGRESS / NOT DEPLOYED / NOT ACCEPTED

preview:
UNTOUCHED
```

Source authority:

```text
И-00-007-ОР-2025 версия 2
section 11
appendix 8
```

Implementation scope:

- exact published type `journal-equipment-defects`;
- exact six-column registry and print representation;
- mandatory structured equipment link and dispatcher-name snapshot;
- separate `created_by` and `DISCOVERED_BY`;
- lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
- separate deadline confirmation, extension, resolution, acknowledgement and close;
- immutable action evidence with employee, position, time, record version,
  canonical snapshot and SHA-256;
- exact history text `Срок устранения продлен`;
- explicit immutable operational-log link;
- minimum non-cloning volume contract;
- dedicated Russian UI and generic-route guard;
- deterministic five-state presentation dataset;
- focused subject tests and PostgreSQL concurrency test;
- browser-printable approved paper form with signature spaces.

Current exit gate:

1. stable final exact head;
2. focused source-bound tests pass;
3. one full PostgreSQL suite passes on that head;
4. all five exact-head workflows are green;
5. trusted AUTO-001B exact-SHA development deployment;
6. development health and controller evidence;
7. preview remains untouched;
8. user product and visual acceptance;
9. separate explicit merge command.

Green CI alone does not complete this stage.

## Subsequent structured journals

Only after DEFECT-001 product/visual acceptance and merge decision:

1. PRODUCT-D2 — Application Journal.
2. PRODUCT-D3 — Disposition Journal.
3. PRODUCT-D4 — Equipment Commissioning.
4. PRODUCT-D5 — RZA and Telemechanics.
5. Work journals — after normative decision.

Each slice must repeat the source-bound pattern: source traceability, specialized
business rules, dedicated UI, deterministic presentation data, automated gates,
exact-SHA runtime and user acceptance.

## Operational Journal Lifecycle

Separate stage after the active vertical slice:

- draft finalization;
- handover preparation;
- сдача/приёмка;
- close shift;
- action evidence;
- editor stabilization;
- templates and abbreviations.

DEFECT-001 links only registered operational-log entries and does not expand the
unfinished shift lifecycle.

## Work Permit and Switching

### Work permits/orders

After normative research:

- register;
- briefings/admissions;
- crew/workplace changes;
- suspension/resumption;
- completion/closure/archive;
- paper/hybrid/electronic boundaries;
- signatures/action evidence.

### Switching minimum

- registry/card;
- equipment and basis;
- participants/dates;
- attachment;
- operational-log link;
- manual sequence.

Automatic generation and safety engine remain later stages.

## Internal Prototype Release

Exit criteria:

- whole-system demonstration;
- 6–8 scenarios;
- deterministic presentation reset;
- accepted defect/application/disposition flows;
- operational journal lifecycle;
- basic permit/switching registries;
- honest paper-first limitations;
- regression and user acceptance.

## Full Demonstration Release

Adds:

- richer lifecycles;
- cross-document relations;
- print/export/archive;
- roles/audit/signatures according to accepted boundary;
- complete demo package and guidance.

## Правила изменения

- infrastructure does not expand without evidence;
- source catalog presence does not equal implementation;
- staging rows do not equal canonical dataset;
- green global tests do not equal subject acceptance;
- provisional UX does not equal visual acceptance;
- automatic merge is forbidden;
- merge requires explicit user command;
- user manual VPS commands for DEFECT-001 remain zero.
