# ЭОД — roadmap

**Актуализировано:** 26.07.2026

## Принцип

Roadmap управляется evidence и acceptance. Исторический номер patch не
доказывает готовность. Каждый work item имеет exact head, CI, runtime evidence,
user decision и явный merge gate.

## Current baseline

```text
current main:
37a2390a2a45e2abb73e60318d5429ed326efb53

accepted application baseline:
937d2cd2b187c17fac3088ccfc52079fc4608306
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
| PLAN-001 evidence | Accepted | Exact-SHA evidence and first slice decision |

## Текущий этап

### PLAN-001 Narrow Repair — PR #7

```text
branch:
plan/001-evidence-audit

status:
OPEN / DRAFT / NOT MERGED

product behavior:
UNCHANGED
```

Scope:

- explicit ownership map;
- `absent` / `unknown` / `not applicable`;
- canonical/staging/presentation/system runtime data split;
- source catalog vs installed/published type vs records;
- AUTO false-positive regression;
- manual Chat 0 decision in report;
- canonical docs;
- final evidence run.

Exit gate:

1. новый exact head;
2. пять green CI;
3. AUTO-001B exact-SHA deployment;
4. one final audit;
5. manifest and ZIP checksum;
6. corrected matrix;
7. development healthy, transaction/pending none;
8. preview healthy and untouched;
9. explicit user merge decision.

## Следующий product stage

### PRODUCT-D1 — Defect Journal Vertical Slice

Начинается только после отдельного starter и merge decision PR #7.

Scope:

- source-bound defect schema;
- equipment;
- participants;
- statuses;
- revisions/audit;
- operational-log link;
- deterministic presentation reset;
- automated and browser acceptance.

## Subsequent structured journals

1. PRODUCT-D2 — Application Journal.
2. PRODUCT-D3 — Disposition Journal.
3. PRODUCT-D4 — Equipment Commissioning.
4. PRODUCT-D5 — RZA and Telemechanics.
5. Work journals — after normative decision.

Каждый slice доводится полностью до acceptance до следующего.

## Operational Journal Lifecycle

Отдельный этап:

- draft finalization;
- handover preparation;
- сдача/приёмка;
- close shift;
- action evidence;
- editor stabilization;
- templates/abbreviations.

## Work Permit and Switching

### Work permits/orders

После normative research:

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

Automatic generation and safety engine are later stages.

## Internal Prototype Release

Exit criteria:

- whole-system demonstration;
- 6–8 scenarios;
- deterministic presentation reset;
- defect/application/disposition flows;
- operational journal lifecycle;
- basic permit/switching registries;
- honest paper-first keys limitation;
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
- merge requires explicit user command.
