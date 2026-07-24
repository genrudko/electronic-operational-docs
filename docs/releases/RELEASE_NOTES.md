# ЭОД — release notes

## Unreleased — DOCS-001 Project operating system

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
- documentation contract script and GitHub Actions workflow.

### Миграция

Устаревший `docs/project_state/` удаляется из active tree после переноса значимой информации. История остаётся в Git.

Старые документы, ориентированные на локальные autonomous Python patches, SQLite и запрет automatic push, заменяются GitHub-first/VPS-first моделью.

### Текущий принятый baseline

```text
main / abd6066885b060e3e3d2c39098fcaf640bb70416
```

DOCS-001 branch не станет accepted baseline до merge и post-merge preview verification.

### Следующий этап

PLAN-001:

- evidence audit реализации;
- матрица `requirement → code → tests → data → acceptance`;
- master plan v3.0;
- возможная корректировка направления;
- выбор ближайшего vertical slice.

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
- current architecture and full test gates.

## 2026-07-24 — Patch 011.7 Repair 2

- source-bound forms;
- arbitrary user form construction disabled;
- technical schemas separated from working forms;
- visual acceptance;
- tag `eod-baseline-011.7-repair2`.