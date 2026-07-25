# AUTO-001 — GitHub/VPS Development Orchestrator

## 1. Назначение

AUTO-001 автоматически развёртывает и проверяет exact head открытого PR на изолированном development-контуре VPS.

Он является детерминированным deployment/test orchestrator, а не coding agent.

## 2. Scope MVP

AUTO-001 обязан:

1. Получить доверенный запрос для открытого PR.
2. Проверить repository, base branch, PR state и exact head SHA.
3. Убедиться, что required GitHub checks для этого SHA успешны.
4. Не допустить параллельный development deployment.
5. Вызвать restricted VPS gateway.
6. Проверить clean worktree и запрет `main`.
7. Получить requested commit из read-only Git remote.
8. Переключить development checkout на exact SHA.
9. Выполнить явно заданный профиль `refresh` или `rebuild`.
10. Выполнить:
    - `development_stack.sh check`;
    - `development_stack.sh test`;
    - `development_stack.sh status`.
11. Проверить database identity `eod_development`.
12. Проверить, что preview state не изменился.
13. Опубликовать краткий result в PR/check summary.
14. Сохранить полный sanitised log как private workflow artifact.

## 3. Out of scope MVP

- автоматический выбор deployment profile;
- автоматический reset development database;
- browser acceptance;
- visual regression;
- автоматический preview deployment;
- автоматический repair;
- автоматический merge;
- изменение application code;
- запись на VPS обратно в GitHub.

## 4. Trigger

Предлагаемый управляющий сигнал:

```text
label: vps-development-requested
```

Условия:

- PR принадлежит `genrudko/electronic-operational-docs`;
- PR открыт;
- base — `main`;
- head находится в том же private repository;
- required checks относятся к текущему head SHA;
- automation workflow берётся из trusted `main`;
- PR не менял automation/security files без отдельного разрешения.

Фактический GitHub event выбирается при реализации так, чтобы недоверенный PR не подменял исполняемый workflow.

## 5. Run manifest

Каждый запуск создаёт immutable manifest:

```json
{
  "schema_version": 1,
  "repository": "genrudko/electronic-operational-docs",
  "pr_number": 0,
  "base_ref": "main",
  "head_ref": "feature/example",
  "head_sha": "40-hex",
  "deployment_profile": "refresh",
  "requested_by": "github-actor",
  "workflow_run_id": "numeric-string"
}
```

Gateway не принимает shell fragments, произвольные paths, URLs или environment variables.

## 6. VPS sequence

```text
acquire lock
→ validate manifest
→ record preview baseline
→ verify development database identity
→ verify clean non-main development checkout
→ git fetch --prune origin
→ resolve requested SHA
→ switch development to exact SHA
→ verify HEAD
→ refresh/rebuild
→ check
→ test apps
→ status
→ record preview state again
→ render evidence
→ release lock
```

Использование detached HEAD или временной локальной branch определяется в реализации после проверки существующего branch switching contract. В обоих случаях итоговый HEAD обязан совпасть с manifest SHA.

## 7. Test command

После QUALITY-001 полный suite:

```text
python manage.py test apps --verbosity 2
```

`development_stack.sh test` обязан вызывать этот label. Result содержит фактическое число выполненных tests; нулевой suite не может считаться success.

## 8. Concurrency

Одновременно разрешён один development deployment:

- GitHub Actions concurrency group;
- VPS filesystem lock;
- run ID, PID и timestamp;
- явная процедура recovery stale lock;
- запрет silent lock stealing.

## 9. Result states

- `PASSED`
- `FAILED`
- `BLOCKED`
- `SUPERSEDED`
- `CANCELLED`
- `SECURITY_INCIDENT`

Новый head SHA делает result старого SHA неактуальным, даже если он был успешным.

## 10. Evidence

Краткий report:

```text
AUTO-001 VPS DEVELOPMENT

PR:
Branch:
Requested SHA:
Deployed SHA:
Profile:
Database:
Tests executed:
Result:

GitHub checks:
Development preflight:
Deployment:
Django check:
Migration drift:
PostgreSQL suite:
HTTP health:
Preview isolation:
```

Automation обновляет один собственный PR comment/check, а не создаёт новый комментарий на каждый retry.

## 11. Failure policy

- failed GitHub checks: VPS не вызывается;
- dirty worktree: `BLOCKED`;
- database mismatch: `SECURITY_INCIDENT`;
- failed migration/profile command: stop;
- failed tests: `FAILED`, лог сохраняется;
- changed PR head: `SUPERSEDED`;
- changed preview state: немедленная остановка и incident report;
- unknown recovery state: automation не пытается импровизировать.

## 12. User-facing result

После `PASSED` пользователь получает только:

- ссылку/маршрут к development;
- exact PR/SHA;
- автоматические gate;
- список предметных и визуальных пунктов приёмки;
- известные ограничения work item.
