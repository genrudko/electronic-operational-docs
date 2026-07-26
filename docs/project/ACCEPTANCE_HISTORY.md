# ЭОД — история приёмок

Этот документ разделяет technical success, runtime evidence, предметную,
визуальную и integration acceptance.

## Исторические product/infrastructure приёмки

| Этап | Статус | Ключевое доказательство |
|---|---|---|
| Patch 011.6.2 Repair 4 | Technical + visual accepted | 485 tests |
| Patch 011.7 Repair 1 Revision 10 | Technical accepted, затем repaired | 495 tests |
| Patch 011.7 Repair 2 | Technical + visual accepted | Source-bound forms boundary |
| INFRA-001 | Accepted | Linux/Python/PostgreSQL CI |
| INFRA-002 | Accepted | Healthy preview, `eod_preview`, HTTP 200 |
| INFRA-003 | Accepted | Isolated `eod-development`, `eod_development` |
| DOCS-001 | Accepted | Canonical project operating system |
| DOCS-002 | Accepted | Baseline metadata |
| DOCS-003 | Provisional accepted | UX v0.3, no visual acceptance |
| QUALITY-001 | Technical accepted | `497/497 OK` |
| AUTO-000 | Accepted | Automation contract and security boundary |

## AUTO-001A/B

**Статус:** accepted and practically verified.

### Accepted implementation

- trusted workflow/controller foundation;
- restricted `eod-automation` user;
- forced SSH gateway;
- read-only GitHub deploy key;
- root-owned fixed controller/Compose/Dockerfile;
- exact PR SHA fetch;
- exact-SHA image;
- isolated PostgreSQL checks and full tests;
- development backup/migrations/health;
- confirm/rollback transaction;
- preview isolation;
- no automatic merge.

### Main history

```text
AUTO-001B merge:
21e101f957808d744052da99709d63f1410b7bc3

trusted validator repair/current main:
37a2390a2a45e2abb73e60318d5429ed326efb53
```

### Practical verification

Canary exact SHA was deployed to development through trusted controller,
validated and closed without merge. Preview remained untouched. Controller
status/rollback path was practically checked.

## PLAN-001 evidence acceptance

**Статус:** evidence collection accepted by permanent integration Chat 0.

```text
PR:
#7

evidence exact head:
fb313f270254720b0f7d7815fffc2cb05d577901

evidence ZIP SHA-256:
58df47f83d1758d2e6aa8b32e1d5a70efb8c453454d8759e25d913e7f031619a

Django tests:
502 / OK

manifest:
VERIFIED
```

Подтверждено:

- exact release/image source parity;
- development database `eod_development`;
- migrations clean;
- global executable gates pass;
- package manifest/checksums valid;
- development healthy;
- controller transaction `NONE`;
- pending run ID `NONE`;
- preview healthy and `UNTOUCHED`.

## PLAN-001 integration decision

Это ручное решение Чата 0, не machine verdict:

```text
generic structured-journal core:
SUBSTANTIALLY IMPLEMENTED

structured journals pack:
NOT COMPLETE

operational journal:
ADVANCED BUT LIFECYCLE INCOMPLETE

work permits/orders:
NOT IMPLEMENTED AS VERTICAL SLICE

switching documents:
NOT IMPLEMENTED AS VERTICAL SLICE

repeatable presentation dataset:
BLOCKING GAP

recommended first vertical slice:
DEFECT JOURNAL
```

## PR #7 acceptance status

```text
merge:
BLOCKED PENDING NARROW REPAIR

branch:
plan/001-evidence-audit

state:
OPEN / DRAFT / NOT MERGED
```

До acceptance нужны:

- explicit ownership classifier;
- absent/unknown/not-applicable semantics;
- runtime data provenance split;
- source catalog/published type/records split;
- false-positive regression;
- canonical docs;
- five exact-head CI;
- one final AUTO-001B deployment/evidence run;
- separate user merge decision.

Функциональная реализация Defect Journal ещё не начата и не считается частью
PLAN-001 acceptance.
