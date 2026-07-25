# ЭОД — release notes

## 2026-07-25 — QUALITY-001 PostgreSQL test execution repair

### Статус

Принят пользователем и squash-merged PR #8.

```text
accepted PR head: 4bf055d681ef35a881c8bf5dc28e8945c1948e0d
main merge commit: 4237aadc2cfdee518567024c2b45b653f49c16e7
full PostgreSQL suite: 497/497 OK
```

### Исправлено

- CI и development runner используют реальный Django label `apps`;
- test discovery gate включает `EOD_TESTING=1`;
- PostgreSQL `select_for_update` ограничен основной таблицей;
- test connections и staticfiles storage корректны;
- concurrency workers закрывают thread-local connections;
- synthetic ZIP fixtures детерминированы;
- удалены устаревшие static test contracts.

Accepted application baseline остаётся `e18872f…` до отдельной фиксации post-merge preview evidence для application merge commit.

## 2026-07-25 — AUTO-000 Development automation contract

### Статус

Documentation-only Draft PR. Runtime, workflows, VPS и secrets не меняются.

### Добавлено

- automation master plan;
- AUTO-001 functional contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- актуализация current state, handoff, roadmap and open items.

Следующий этап после принятия — AUTO-001 MVP. Полный набор AUTO-002+ не блокирует возврат к PLAN-001.

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

- новый `README.md`;
- `AGENTS.md`;
- canonical `docs/INDEX.md`;
- project state, master plan, roadmap, scope, domain invariants, architecture and module map;
- data/privacy policy;
- decision/open items/patch/baseline/acceptance histories;
- current handoff and new chat starter;
- project operating system and GitHub-first/VPS-first workflow;
- Git, PR, CI, DoD, release and documentation policies;
- preview/development/database/reset/tunnel/branch/post-merge/incident runbooks;
- internal prototype acceptance, demonstration scenarios, regression checklist and known limitations;
- PR template;
- documentation contract script and GitHub Actions workflow;
- UX-001 UI design system chat brief.

### Принятые продуктовые решения

- журнальный контур развивается последовательными vertical slices;
- каждый журнал получает минимальные реальные связи до перехода к следующему;
- универсальная timeline не проектируется преждевременно;
- журнал ключей считается paper-first;
- полный электронный lifecycle ключей исключён из обязательного prototype scope;
- UX-001 работает параллельно, не становясь вторым интеграционным центром;
- применимые canonical docs обновляются после каждого принятого feature/repair/patch.

### Миграция документации

Устаревший `docs/project_state/` удалён из active tree после переноса значимой информации. История остаётся в Git.

Старые инструкции, ориентированные на локальные autonomous Python patches, SQLite и запрет automatic push, заменены GitHub-first/VPS-first моделью.

### CI и проверки

Для exact accepted head прошли:

- EOD Documentation Contract;
- EOD Development Stack;
- EOD CI.

На момент DOCS-001 Django test command обнаруживал `0 test(s)`. Этот долг позднее закрыт QUALITY-001; текущий suite выполняет 497 tests.

### Post-merge preview

Подтверждено:

- `/srv/eod/repository` на `main / e18872face7f27f489056b72fed31e5586121b0c`;
- clean worktree;
- documentation contract OK, 43 required files;
- preview app and database healthy;
- health endpoint OK;
- main page HTTP 200;
- database identity `eod_preview`;
- pending migrations отсутствуют.

### Следующий этап

PLAN-001 выполняется после короткого AUTO-000/AUTO-001 infrastructure sprint.

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
