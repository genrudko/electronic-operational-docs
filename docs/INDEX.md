# Индекс документации ЭОД

**Актуализировано:** 26.07.2026

Этот индекс определяет канонические документы проекта и порядок их использования.
При противоречии применяется иерархия источников истины из
`project/CURRENT_STATE.md` и `process/PROJECT_OPERATING_SYSTEM.md`.

## Текущая контрольная точка

```text
current main:
b75db8bc073e4b02a3254512e9b99d00f3e6e0e2

accepted application baseline:
937d2cd2b187c17fac3088ccfc52079fc4608306

AUTO-001A/B:
ACCEPTED AND PRACTICALLY VERIFIED

PLAN-001 / PR #7:
MERGED / ACCEPTED

active product vertical slice:
DEFECT-001 — SOURCE-BOUND EQUIPMENT DEFECT JOURNAL

active branch:
feature/defect-001-equipment-defect-journal

active Draft PR:
#16 / OPEN / NOT MERGED
```

DEFECT-001 реализуется в dedicated source-bound слое поверх
`apps.operational_documents`. Green CI или наличие кода не равны предметной и
визуальной приёмке. Preview остаётся нетронутым; merge требует отдельной явной
команды пользователя.

## Начать здесь

1. [`../README.md`](../README.md) — назначение и входные точки.
2. [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md) — проверенные факты.
3. [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md) — текущий handoff.
4. [`project/DEFECT_001_IMPLEMENTATION.md`](project/DEFECT_001_IMPLEMENTATION.md) — source-bound контракт активного vertical slice.
5. [`project/DOMAIN_INVARIANTS.md`](project/DOMAIN_INVARIANTS.md) — предметные правила.
6. [`process/DEVELOPMENT_WORKFLOW.md`](process/DEVELOPMENT_WORKFLOW.md) — рабочий цикл.
7. [`../AGENTS.md`](../AGENTS.md) — контракт AI-разработчика.

## Проект

| Документ | Назначение |
|---|---|
| [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md) | Фактический baseline, runtime, accepted work и ближайший gate |
| [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md) | Продолжение работы без восстановления по памяти |
| [`project/DEFECT_001_IMPLEMENTATION.md`](project/DEFECT_001_IMPLEMENTATION.md) | Точный source-bound контракт журнала дефектов и текущие gates |
| [`project/MASTER_PLAN.md`](project/MASTER_PLAN.md) | Актуальный продуктовый план после PLAN-001 |
| [`project/ROADMAP.md`](project/ROADMAP.md) | Очередность этапов и decision gates |
| [`project/OPEN_ITEMS.md`](project/OPEN_ITEMS.md) | Открытые блокеры и отложенные задачи |
| [`project/DOMAIN_INVARIANTS.md`](project/DOMAIN_INVARIANTS.md) | Неизменяемые предметные правила |
| [`project/SCOPE_AND_BOUNDARIES.md`](project/SCOPE_AND_BOUNDARIES.md) | Цели и границы независимого прототипа |
| [`project/SYSTEM_ARCHITECTURE.md`](project/SYSTEM_ARCHITECTURE.md) | Архитектура приложения и контуров |
| [`project/MODULE_MAP.md`](project/MODULE_MAP.md) | Карта функциональных модулей |
| [`project/DATA_AND_PRIVACY_POLICY.md`](project/DATA_AND_PRIVACY_POLICY.md) | Данные, secrets и privacy |
| [`project/DECISION_LOG.md`](project/DECISION_LOG.md) | Хронология решений |
| [`project/PATCH_HISTORY.md`](project/PATCH_HISTORY.md) | История технических этапов |
| [`project/BASELINE_HISTORY.md`](project/BASELINE_HISTORY.md) | Принятые baseline и main history |
| [`project/ACCEPTANCE_HISTORY.md`](project/ACCEPTANCE_HISTORY.md) | Технические и пользовательские приёмки |
| [`project/NEW_CHAT_STARTER.md`](project/NEW_CHAT_STARTER.md) | Старт нового интеграционного чата |

## Автоматизация разработки

| Документ | Назначение |
|---|---|
| [`automation/README.md`](automation/README.md) | Навигация по AUTO-000/AUTO-001 |
| [`automation/AUTO_001_GITHUB_VPS_ORCHESTRATOR.md`](automation/AUTO_001_GITHUB_VPS_ORCHESTRATOR.md) | Контракт orchestrator |
| [`automation/AUTO_001_SECURITY_MODEL.md`](automation/AUTO_001_SECURITY_MODEL.md) | Trust boundaries и угрозы |
| [`automation/AUTO_001_ACCEPTANCE_CONTRACT.md`](automation/AUTO_001_ACCEPTANCE_CONTRACT.md) | Acceptance criteria |
| [`automation/AUTO_001_IMPLEMENTATION_ROADMAP.md`](automation/AUTO_001_IMPLEMENTATION_ROADMAP.md) | Этапы implementation |
| [`automation/AUTO_001_DECISION_REGISTER.md`](automation/AUTO_001_DECISION_REGISTER.md) | Решения AUTO-001 |
| [`automation/AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md`](automation/AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md) | Trusted-controller foundation |
| [`adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md`](adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md) | Staged bootstrap ADR |
| [`runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md`](runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md) | Bootstrap, status и rollback |

AUTO-001A/B приняты и практически проверены. Штатный путь:
trusted label → пять exact-head CI → restricted controller → exact-SHA image →
host-owned Compose → development. Automatic merge и preview write отсутствуют.

## UX/UI

| Документ | Назначение |
|---|---|
| [`ux/README.md`](ux/README.md) | Статус UX-001 |
| [`ux/UX-001_v0.3/UX_001_INDEX.md`](ux/UX-001_v0.3/UX_001_INDEX.md) | Индекс provisional v0.3 |
| [`ux/UX-001_v0.3/VISUAL_DIRECTION.md`](ux/UX-001_v0.3/VISUAL_DIRECTION.md) | Визуальное направление |
| [`ux/UX-001_v0.3/UI_AUDIT.md`](ux/UX-001_v0.3/UI_AUDIT.md) | UI-аудит |
| [`ux/UX-001_v0.3/REFERENCE_SCREENS.md`](ux/UX-001_v0.3/REFERENCE_SCREENS.md) | Reference contracts |
| [`ux/UX-001_v0.3/DESIGN_TOKENS.md`](ux/UX-001_v0.3/DESIGN_TOKENS.md) | Candidate tokens |

UX-001 остаётся provisional до runtime visual acceptance.

## Процесс разработки

| Документ | Назначение |
|---|---|
| [`process/PROJECT_OPERATING_SYSTEM.md`](process/PROJECT_OPERATING_SYSTEM.md) | Операционная система проекта |
| [`process/DEVELOPMENT_WORKFLOW.md`](process/DEVELOPMENT_WORKFLOW.md) | GitHub-first/VPS-first цикл |
| [`process/GIT_WORKFLOW.md`](process/GIT_WORKFLOW.md) | Branches и commits |
| [`process/BRANCH_AND_PR_POLICY.md`](process/BRANCH_AND_PR_POLICY.md) | Контракт branch/PR |
| [`process/CI_AND_QUALITY_GATES.md`](process/CI_AND_QUALITY_GATES.md) | CI и ручные gates |
| [`process/DEFINITION_OF_DONE.md`](process/DEFINITION_OF_DONE.md) | Definition of Done |
| [`process/RELEASE_PROCESS.md`](process/RELEASE_PROCESS.md) | Merge, deployment и baseline |
| [`process/DOCUMENTATION_MAINTENANCE.md`](process/DOCUMENTATION_MAINTENANCE.md) | Поддержание документации |
| [`process/PARALLEL_CHAT_WORKFLOW.md`](process/PARALLEL_CHAT_WORKFLOW.md) | Разделение чатов |

## Runbook

| Документ | Назначение |
|---|---|
| [`runbooks/PREVIEW_RUNBOOK.md`](runbooks/PREVIEW_RUNBOOK.md) | Accepted preview |
| [`runbooks/DEVELOPMENT_RUNBOOK.md`](runbooks/DEVELOPMENT_RUNBOOK.md) | Active development |
| [`runbooks/DATABASE_BACKUP_AND_RESTORE.md`](runbooks/DATABASE_BACKUP_AND_RESTORE.md) | Backup/restore |
| [`runbooks/PRESENTATION_DATA_RESET.md`](runbooks/PRESENTATION_DATA_RESET.md) | Presentation reset |
| [`runbooks/SSH_TUNNEL_ACCESS.md`](runbooks/SSH_TUNNEL_ACCESS.md) | SSH tunnel |
| [`runbooks/POST_MERGE_DEPLOYMENT.md`](runbooks/POST_MERGE_DEPLOYMENT.md) | Preview после merge |
| [`runbooks/INCIDENT_AND_ROLLBACK.md`](runbooks/INCIDENT_AND_ROLLBACK.md) | Incident/rollback |

## Приёмка

| Документ | Назначение |
|---|---|
| [`acceptance/INTERNAL_PROTOTYPE_ACCEPTANCE.md`](acceptance/INTERNAL_PROTOTYPE_ACCEPTANCE.md) | Контракт внутреннего прототипа |
| [`acceptance/DEMONSTRATION_SCENARIOS.md`](acceptance/DEMONSTRATION_SCENARIOS.md) | Сквозные сценарии |
| [`acceptance/REGRESSION_CHECKLIST.md`](acceptance/REGRESSION_CHECKLIST.md) | Ручная регрессия |
| [`acceptance/KNOWN_LIMITATIONS.md`](acceptance/KNOWN_LIMITATIONS.md) | Известные ограничения |

## Правило актуальности

Фактический документ содержит дату и проверяемые SHA. Статусы `готово`,
`частично`, `не реализовано`, `unknown` и `not applicable` не подменяют друг
друга. Принятый evidence package не означает автоматическую предметную
приёмку, а Draft PR не считается baseline до отдельной команды merge и
post-merge проверки.
