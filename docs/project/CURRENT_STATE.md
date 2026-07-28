# ЭОД — текущее состояние

**Дата проверки:** 28.07.2026

```text
repository:
genrudko/electronic-operational-docs

accepted application baseline:
main / 937d2cd2b187c17fac3088ccfc52079fc4608306

current main at DEV-FAST-001 start:
54990c386c40dd7bd854330e61ed7285649ef120

last accepted work item:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

active work item:
DEV-FAST-001 — Trusted hot refresh from PR comment

active branch:
infra/dev-fast-001-hot-refresh

active PR:
#19 / OPEN / DRAFT / NOT MERGED
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
- PLAN-001 evidence audit and classifier repair;
- DEFECT-001 source-bound equipment defect journal.

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
PARTIALLY PRESENT THROUGH DEFECT-001

accepted first vertical slice:
DEFECT JOURNAL
```

This was a manual integration decision, not an automatic product-acceptance verdict.

## 5. DEFECT-001 accepted status

```text
source head:
79f3db7e5c47e1ac8ab2568028d06e4043c2c70e

merge commit:
883a108c8be2a8cd075846fdd175916917911ef6

five exact-head workflows:
GREEN

full PostgreSQL/Django suite:
SUCCESS

trusted development deployment:
SUCCESS

user acceptance:
CONFIRMED

preview:
UNTOUCHED
```

Accepted implementation:

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
- desktop/mobile presentation and final row-click repair.

The current visual style remains a legacy interface and is not the accepted target UX/UI.

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
- PostgreSQL CI/runtime foundation;
- source-bound equipment defect journal.

### Accepted reference vertical slice

- equipment defect journal: accepted and merged through PR #16;
- source-bound UI and print form: accepted;
- operational-log link: accepted;
- repeatable defect presentation data: accepted;
- technical, functional and visual acceptance: confirmed for the agreed DEFECT-001 scope.

### Not implemented as a vertical slice

- work permits/orders lifecycle;
- work-permit work journals;
- switching documents minimum contour;
- automatic БП/ТБП/ТПП generation;
- legally significant electronic signature.

The key journal remains paper-first. The defect journal is explicitly a
reference/control and demonstration contour with a printable approved form.

## 7. DEV-FAST-001 implementation status

The active Draft PR implements the approved presentation-only V1:

```text
trigger:
main-controlled issue_comment:created

command:
/eod-hot-refresh <exact-head-sha>

gateway:
hot-refresh <pr> <sha> <run_id>

allowlist:
src/templates/**
src/static/**

allowed Git entries:
added/modified regular 100644 blobs only
```

The workflow and controller independently validate actor/PR/exact SHA and path/blob policy. The controller applies exact Git blobs only to the writable layer of the current `eod-development` app container, restarts only app, relies on the host-owned check/collectstatic entrypoint and requires local health.

On any runtime error the app is force-recreated from the current full image. The separate overlay marker is container-local and does not change deployment `current_sha`.

Explicitly unchanged:

- existing release transactions;
- database and migrations;
- image build;
- host-owned Compose/Dockerfile/entrypoint;
- presentation seed;
- preview;
- automatic merge.

Runtime activation cannot occur before trusted code is merged to `main`. After explicit merge authorization, one controlled root activation installs only the reviewed controller file; then a separate presentation-only canary PR proves success, idempotency and rollback.

## 8. Current gate

1. Obtain one final exact head for PR #19.
2. Pass focused validator/controller contracts.
3. Pass one full security/code gate.
4. Keep PR Draft/not merged until a separate user merge command.
5. After merge, install only the exact accepted controller file on VPS.
6. Run a separate canary PR for `SUCCESS`, `ALREADY_APPLIED` and rollback evidence.
7. Verify development health and preview `UNTOUCHED`.

## 9. Non-negotiable rules

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
- User manual VPS commands for functional PR acceptance are zero.
- Merge requires a separate explicit user command.

## 10. Detailed work-item sources

- `docs/project/DEFECT_001_IMPLEMENTATION.md` — accepted product slice contract.
- GitHub issue `#18` and Draft PR `#19` — active DEV-FAST-001 contract and evidence.
