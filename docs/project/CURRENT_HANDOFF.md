# CHAT 0 — CURRENT HANDOFF

**Проект:** Электронная оперативная документация  
**Репозиторий:** `genrudko/electronic-operational-docs`  
**Дата:** 29.07.2026  
**Назначение:** current integration context, active work item и следующие решения.

## 1. Роли

Chat 0:

- baseline;
- priorities;
- architecture and product decisions;
- acceptance;
- merge authorization;
- canonical documentation.

Implementation chat:

- factual audit конкретного work item;
- code/tests/docs в одной branch/PR;
- CI/runtime evidence;
- repairs;
- возврат в Chat 0 при blocker или merge readiness.

Research chat:

- evidence;
- source catalog;
- decision proposals;
- не меняет architecture или code самостоятельно.

## 2. Current baseline

```text
accepted UX/application merge:
a880a632b750309c7fbfb918af15b49d99b5a93f

accepted UX source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

UX-FOUNDATION-001:
issue #22 / PR #23 / MERGED / ACCEPTED

DEFECT-001:
PR #16 / MERGED / ACCEPTED

DEV-FAST-001:
issue #18 / COMPLETED

preview:
UNTOUCHED
```

Metadata-only documentation commits не являются новым application baseline.

## 3. Active work item — OPJ-UX-001

```text
issue:
#24

Draft PR:
#25

branch:
ux/opj-ux-001

current candidate head:
663086c9c0b0dfa0d4e970185f0f52269be20a61

state:
OPEN / DRAFT / NOT MERGED
```

Factual candidate evidence:

- 14 changed files;
- templates/static + focused source-contract test;
- models/migrations/services/routes unchanged;
- five exact-head workflows success;
- PostgreSQL suite `564 / OK`;
- trusted development delivery success;
- rollback not required;
- preview untouched.

### Revised scope

OPJ-UX-001 не создаёт `opj-da-*` как вторую design system.

Он реализует:

```text
shared Direction A layer
→ home/defect/operational shell alignment
→ OPJ registry and registered view
→ specialized shift workspace
```

Shared:

- shell/sidebar/topbar;
- visual tokens;
- page header;
- buttons/fields/tabs/cards/statuses;
- hierarchy selectors;
- overlays;
- responsive behavior.

Specialized:

- operational three-column form;
- page/spread geometry;
- ribbon;
- editor schema v4;
- normative marks;
- semantic references.

### Current gate

Пользователь проверяет desktop/mobile runtime. Repairs остаются в PR #25.

Full final gate выполняется только на окончательном accepted head. Merge — только по отдельной команде пользователя в Chat 0.

## 4. Accepted product and UX principles

Canonical:

```text
docs/project/PRODUCT_UX_PRINCIPLES.md
```

Основные решения:

1. same-purpose UI elements выглядят и работают одинаково;
2. Direction A — system-wide language;
3. feature-specific copy не является shared system;
4. critical daily scenario сравнивается с бумагой/Excel/узким продуктом;
5. один primary object формирует derived registries/reports;
6. authoring и lifecycle проектируются раздельно;
7. handover — отдельный workflow;
8. rounds — отдельная route/checkpoint entity;
9. SCADA — optional integration;
10. research evidence классифицируется `ADOPT/ADAPT/REJECT/DEFER/VERIFY`.

## 5. Research integration

Accepted package:

- 16 products/modules;
- 27 sources;
- 18 UX patterns;
- 16 decisions;
- 8 attributed research images in the external package.

Public repository contains no third-party images.

Canonical files:

```text
docs/research/VERTICAL_PRODUCTS_RESEARCH_20260729.md
docs/research/VERTICAL_PRODUCTS_SOURCE_CATALOG_20260729.csv
docs/research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv
```

Research is input for decisions, not automatic requirements.

## 6. Development process

Canonical:

```text
docs/process/DEVELOPMENT_WORKFLOW.md
docs/process/DEVELOPMENT_ACCELERATION.md
```

Active model:

```text
factual preflight
→ one issue/branch/PR
→ proportional checks
→ hot refresh or candidate deploy
→ user acceptance
→ repairs
→ one final exact-head gate
→ explicit merge
```

User manual technical actions target: `0`.

### Existing accelerators

- trusted exact-SHA development controller;
- templates/static hot refresh;
- failure-only diagnostics;
- same-PR repair cycle;
- no full suite after every micro-repair.

### Planned after OPJ-UX-001

1. `CI-OPT-001`;
2. `DEV-EVIDENCE-001`;
3. `UI-CONTRACT-001`;
4. `WORKITEM-BOOTSTRAP-001`.

Do not start them during active OPJ acceptance unless user changes priority.

## 7. Product sequence after OPJ-UX-001

Product sequence is controlled by demonstration needs and factual readiness.

Current candidate order:

```text
OPJ-LIFECYCLE-001
→ OPJ-ASSISTANCE-001
→ SHIFT-HANDOVER-001
→ PRODUCT-D2 applications
→ PRODUCT-D3 dispositions
→ PERMIT-AUTHORING-001
→ SWITCHING-DOCUMENTS-001
```

`CI-OPT-001` is a short process slice after OPJ acceptance, not a large infrastructure detour.

Separate later items:

- `PERMIT-LIFECYCLE-001`;
- `CROSS-DOCUMENT-ACTIONS-001`;
- `ROUNDS-001`;
- `RZA-TM-RESEARCH`;
- `OFFLINE-001`;
- `SCADA-INTEGRATION`;
- `HOST-MOVE-001`.

## 8. Hosting

Current VPS has repeated availability incidents. Migration is planned after the paid period.

Until `HOST-MOVE-001`:

- current server remains development/preview runtime;
- no emergency migration during active product acceptance unless outage makes work impossible;
- GitHub remains source of truth;
- backup/restore and controller contracts must make migration reproducible.

## 9. Non-negotiable rules

- no automatic merge;
- no product PR writes to preview;
- no development on `main`;
- no real enterprise data;
- no separate UI system per journal;
- no false lifecycle buttons;
- no full-gate repetition without risk reason;
- no user programming/manual orchestration;
- exact head and evidence before success claim.

## 10. Immediate next action

1. Finish user acceptance of PR #25.
2. Keep all OPJ UX repairs in the same PR.
3. On accepted final head run one final gate if current evidence became stale.
4. Return to Chat 0 for Ready/Merge verdict.
5. After merge start the short `CI-OPT-001` factual audit and implementation.
