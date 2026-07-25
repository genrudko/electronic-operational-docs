# ЭОД — release notes

## 2026-07-25 — DOCS-005 AUTO-000 baseline finalization

### Статус

Draft PR #10, documentation-only metadata follow-up.

### Цель

- зафиксировать accepted application baseline `main / 937d2cd2b187c17fac3088ccfc52079fc4608306`;
- записать AUTO-000 acceptance and post-merge evidence;
- синхронизировать current state, handoff, baseline/acceptance history, roadmap and open items;
- подготовить новый постоянный Chat 0.

Application code, schema, migrations, runtime data, workflows, VPS configuration и secrets не меняются. Собственный будущий merge SHA DOCS-005 не создаёт новый application baseline.

## 2026-07-25 — AUTO-000 Development automation contract

### Статус

Принят пользователем, squash-merged PR #9 и post-merge verified.

```text
accepted PR head: 3a4b4770e1fce41405813efa1e931288bf1a26b8
main merge commit: 937d2cd2b187c17fac3088ccfc52079fc4608306
change type: documentation-only operating-system milestone
```

### Добавлено

- automation master plan;
- AUTO-001 functional contract;
- exact-SHA and fail-closed invariants;
- restricted security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- explicit ban on automatic merge;
- explicit preview isolation and no-preview-write boundary;
- rejection of ordinary self-hosted runner with sudo/Docker socket;
- rule that AUTO-002+ do not block product development.

### Exact-head evidence

- EOD Documentation Contract — success;
- EOD Development Stack — success;
- EOD CI — success;
- container preview smoke — success;
- development VPS full PostgreSQL suite: `497/497 OK`;
- development database identity: `eod_development`;
- exact SHA and clean worktree;
- preview isolation preserved.

### Post-merge preview

Подтверждено:

- `/srv/eod/repository` on `main / 937d2cd2b187c17fac3088ccfc52079fc4608306`;
- clean worktree;
- preview app image rebuilt from current checkout;
- app container recreated and healthy;
- DB container preserved and healthy;
- health endpoint OK;
- main page HTTP 200 on `127.0.0.1:8765`;
- database identity `eod_preview`;
- migration state clean;
- host/container source match after excluding generated `electronic_operational_docs.egg-info/*`;
- final marker `FINAL PREVIEW GATE PASSED`.

Accepted application baseline: `937d2cd2b187c17fac3088ccfc52079fc4608306`.

### Следующий этап

AUTO-001 MVP в отдельном implementation chat/branch/PR. До executable workflow/gateway обязателен actual infrastructure gap analysis. Automatic merge остаётся запрещён.

## 2026-07-25 — QUALITY-001 PostgreSQL test execution repair

### Статус

Принят пользователем и squash-merged PR #8.

```text
accepted PR head: 4bf055d681ef35a881c8bf5dc28e8945c1948e0d
main merge commit: 4237aadc2cfdee518567024c2b45b653f49c16e7
full PostgreSQL suite: 497/497 OK
```

### Исправлено

- CI and development runner use real Django label `apps`;
- test discovery gate includes `EOD_TESTING=1`;
- PostgreSQL `select_for_update` is limited to the main table;
- test connections and staticfiles storage corrected;
- concurrency workers close thread-local connections;
- synthetic ZIP fixtures made deterministic;
- obsolete static test contracts removed.

Нулевой test discovery закрыт. Следующие product slices сохраняют full suite и добавляют профильные gates.

## 2026-07-25 — DOCS-003 Provisional UX-001 v0.3 contract

### Статус

Принят и squash-merged PR #6.

```text
main merge commit: 62ce0a611b0d36a4c0f1f28ac6083cac5d305fb5
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

UX package сохранён как обратимая проектная основа. Runtime, domain lifecycle and data не менялись.

## 2026-07-25 — DOCS-002 DOCS-001 baseline finalization

### Статус

Принят и squash-merged PR #5.

```text
main merge commit: a2d686b0061fac513c02540a2176850640496884
change type: documentation-only metadata follow-up
```

Зафиксированы DOCS-001 post-merge evidence, baseline history и PLAN-001 transition. Собственный SHA не создавал новый application baseline.

## 2026-07-25 — DOCS-001 Project operating system

### Статус

Принят пользователем, squash-merged PR #4 и проверен на accepted preview.

```text
accepted PR head: 1f0b71b927fbee0ef08957eac157b2480d2e9a8c
accepted application baseline: e18872face7f27f489056b72fed31e5586121b0c
```

### Цель

Сделать закрытый GitHub-репозиторий главным онлайн-источником истины и закрепить AI-driven development, где пользователь выполняет постановку задачи и приёмку, но не программирует.

### Добавлено

- README and AGENTS;
- canonical `docs/INDEX.md`;
- project state, master plan, roadmap, scope, domain invariants, architecture and module map;
- data/privacy policy;
- decision/open items/patch/baseline/acceptance histories;
- current handoff and new-chat starter;
- GitHub-first/VPS-first operating system;
- Git, PR, CI, DoD, release and documentation policies;
- preview/development/database/reset/tunnel/branch/post-merge/incident runbooks;
- internal prototype acceptance, demonstration scenarios, regression checklist and known limitations;
- PR template;
- documentation contract script and workflow;
- UX-001 UI design-system chat brief.

### Принятые продуктовые решения

- journals are developed as sequential vertical slices;
- each journal receives minimal real links before the next one;
- universal timeline is not designed prematurely;
- keys journal is paper-first;
- full electronic keys lifecycle excluded from mandatory prototype scope;
- UX-001 works in parallel without becoming an integration center;
- applicable canonical docs are updated after accepted changes.

### Post-merge preview

Подтверждено:

- `/srv/eod/repository` on `main / e18872face7f27f489056b72fed31e5586121b0c`;
- clean worktree;
- documentation contract OK;
- preview app/db healthy;
- health OK;
- main page HTTP 200;
- database identity `eod_preview`;
- pending migrations absent.

## 2026-07-24 — INFRA-003

- isolated development on VPS;
- separate checkout/Compose/PostgreSQL/volume/network/secrets;
- application `127.0.0.1:8766`;
- safe reset from accepted preview;
- simultaneous contour health;
- SSH tunnel browser acceptance;
- merge commit `abd6066885b060e3e3d2c39098fcaf640bb70416`.

## 2026-07-24 — INFRA-002

- accepted preview on VPS;
- application `127.0.0.1:8765`;
- PostgreSQL `eod_preview`;
- presentation data migration;
- demo authentication;
- merge commit `ded4571dcacd973184d3121b19c8db8c70e7b08a`;
- tag `eod-baseline-infra-002`.

## 2026-07-24 — INFRA-001

- GitHub Actions CI on Linux/Python/PostgreSQL;
- current architecture and profile gates.

## 2026-07-24 — Patch 011.7 Repair 2

- source-bound forms;
- arbitrary user form construction disabled;
- technical schemas separated from working forms;
- visual acceptance;
- tag `eod-baseline-011.7-repair2`.
