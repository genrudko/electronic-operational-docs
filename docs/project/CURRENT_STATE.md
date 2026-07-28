# ЭОД — текущее состояние

**Дата проверки:** 26.07.2026

```text
repository:
genrudko/electronic-operational-docs

accepted application baseline:
main / 937d2cd2b187c17fac3088ccfc52079fc4608306

current main history HEAD:
b75db8bc073e4b02a3254512e9b99d00f3e6e0e2

last accepted work item:
PLAN-001 / PR #7 / MERGED / ACCEPTED

active work item:
DEFECT-001 — Source-bound Equipment Defect Journal Vertical Slice

active branch:
feature/defect-001-equipment-defect-journal

active PR:
#16 / OPEN / DRAFT / NOT MERGED
```

## 1. Project boundary

ЭОД — независимый демонстрационный прототип электронной оперативной
документации для энергетики. Он не является официальной системой работодателя.
Production servers, real operational records, real personal data and enterprise
secrets are not used.

GitHub is the only source of code and canonical documentation. VPS is the only
runtime/test contour. Accepted preview and active development remain isolated.

## 2. Accepted foundation

Accepted and practically verified:

- INFRA-001–003;
- DOCS-001–003;
- QUALITY-001;
- AUTO-000;
- AUTO-001A trusted-controller foundation;
- AUTO-001B restricted VPS development controller;
- trusted request validator repair;
- PLAN-001 evidence audit and classifier repair.

Current `main` is `b75db8bc073e4b02a3254512e9b99d00f3e6e0e2`.

The accepted AUTO-001B route is:

```text
trusted PR label
→ five green exact-head workflows
→ trusted request validation from main
→ restricted forced SSH gateway
→ exact PR SHA fetch
→ exact-SHA image
→ isolated PostgreSQL checks and full tests
→ development backup/migrations/health
→ confirm or rollback
```

Automatic merge is absent. The controller does not write to preview.

## 3. Runtime contours

### Accepted preview

```text
checkout: /srv/eod/repository
branch: main only
compose project: eod-preview
application: 127.0.0.1:8765
database: eod_preview
secrets: /srv/eod/secrets/preview.env
```

### Active development

```text
controller releases: /srv/eod/automation/releases/<exact-sha>
compose project: eod-development
application: 127.0.0.1:8766
database/user: eod_development
secrets: /srv/eod/secrets/development.env
controller: /usr/local/sbin/eod-development-controller
state: /srv/eod/automation/state
```

Development does not depend on a PR-controlled host checkout or a PR-controlled
root script.

## 4. PLAN-001 accepted decision

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

This was a manual integration decision, not an automatic product-acceptance verdict.

## 5. DEFECT-001 implementation status

Implemented in Draft PR #16:

- exact type `journal-equipment-defects`;
- source reference `И-00-007-ОР-2025 версия 2`, section 11, appendix 8;
- exact six-column working and print presentation;
- dedicated registry, card and separate actions;
- mandatory structured equipment link and dispatcher-name snapshot;
- participant roles `DISCOVERED_BY`, `OPERATIONS_RESPONSIBLE`,
  `RESOLUTION_RESPONSIBLE`, `OPERATIONAL_ACKNOWLEDGER`;
- lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
- versioned deadline extension with old/new deadlines and exact wording
  `Срок устранения продлен`;
- authenticated action evidence tied to employee, position, time, record version,
  canonical snapshot and SHA-256;
- explicit immutable link to a registered operational-log entry;
- minimum non-cloning volume contract;
- deterministic five-state presentation dataset;
- focused subject tests;
- guard redirecting generic create/edit/transition routes to the specialized journal.

Not yet proven on the final exact head:

- focused test success;
- full PostgreSQL suite;
- five green exact-head workflows;
- exact-SHA development deployment;
- development health;
- user product/visual acceptance.

Therefore DEFECT-001 is `IN IMPLEMENTATION`, not accepted.

## 6. Functional readiness

### Substantially implemented

- organization, personnel, positions and workplaces;
- equipment/dispatching/import foundation;
- documentation core;
- workplace-documentation registry;
- specialized operational journal;
- generic `apps.operational_documents` core;
- source-bound catalog;
- immutable revisions, snapshots, audit and links;
- PostgreSQL CI/runtime foundation.

### Current vertical slice

- equipment defect journal: implementation in Draft PR #16;
- source-bound UI and print form: present in branch;
- operational-log link: present in branch;
- repeatable defect presentation data: present in branch;
- technical and visual acceptance: pending.

### Not implemented as a vertical slice

- work permits/orders lifecycle;
- work-permit work journals;
- switching documents minimum contour;
- automatic БП/ТБП/ТПП generation;
- legally significant electronic signature.

The key journal remains paper-first. The defect journal is explicitly a
reference/control and demonstration contour with a printable approved form.

## 7. Current gate

1. Complete focused repairs in PR #16.
2. Obtain one green focused/full PostgreSQL result on the final exact head.
3. Obtain five green exact-head workflows.
4. Apply `vps-development-refresh` only after the exact-head gate.
5. Verify exact SHA and development health through trusted controller evidence.
6. Keep preview untouched.
7. Give the user only the development UI acceptance scenario.
8. Keep PR Draft/not merged until a separate user merge command.

## 8. Non-negotiable rules

- End-user UI is Russian only.
- Internals use professional technical English.
- Operational journal remains specialized.
- Other journals reuse the generic core through specialized source-bound layers.
- The operator does not construct arbitrary working forms.
- ЩПТ and ШОТ are one technical equipment family with source notation preserved.
- Electronic confirmation is not called УКЭП or a legally significant signature.
- Paper/hybrid/electronic modes are not declared legally equivalent without a
  separate normative and organizational decision.
- Real enterprise data and secrets are not committed.
- User manual VPS commands for DEFECT-001 are zero.
- Merge requires a separate explicit user command.

## 9. Detailed work-item document

See `docs/project/DEFECT_001_IMPLEMENTATION.md`.
