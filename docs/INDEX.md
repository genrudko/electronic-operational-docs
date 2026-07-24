# Индекс документации ЭОД

Этот индекс определяет канонические документы проекта и порядок их использования. При противоречии применяется иерархия источников истины из `project/CURRENT_STATE.md` и `process/PROJECT_OPERATING_SYSTEM.md`.

## Начать здесь

1. [`../README.md`](../README.md) — назначение, состояние и входные точки.
2. [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md) — подтверждённое фактическое состояние.
3. [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md) — продолжение работы без восстановления по памяти.
4. [`project/DOMAIN_INVARIANTS.md`](project/DOMAIN_INVARIANTS.md) — обязательные предметные правила.
5. [`process/DEVELOPMENT_WORKFLOW.md`](process/DEVELOPMENT_WORKFLOW.md) — рабочий цикл.
6. [`../AGENTS.md`](../AGENTS.md) — контракт AI-разработчика.

## Проект

| Документ | Назначение |
|---|---|
| [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md) | Проверенные факты о baseline, инфраструктуре, модулях и ближайшем шаге |
| [`project/MASTER_PLAN.md`](project/MASTER_PLAN.md) | Утверждённая база плана и граница предстоящей ревизии |
| [`project/ROADMAP.md`](project/ROADMAP.md) | Очередность этапов и decision gates |
| [`project/SCOPE_AND_BOUNDARIES.md`](project/SCOPE_AND_BOUNDARIES.md) | Цели, ограничения и то, чем проект не является |
| [`project/DOMAIN_INVARIANTS.md`](project/DOMAIN_INVARIANTS.md) | Неизменяемые предметные правила |
| [`project/SYSTEM_ARCHITECTURE.md`](project/SYSTEM_ARCHITECTURE.md) | Архитектура приложения и контуров |
| [`project/MODULE_MAP.md`](project/MODULE_MAP.md) | Статус функциональных модулей |
| [`project/DATA_AND_PRIVACY_POLICY.md`](project/DATA_AND_PRIVACY_POLICY.md) | Политика данных, секретов и репозитория |
| [`project/DECISION_LOG.md`](project/DECISION_LOG.md) | Хронологический журнал решений |
| [`project/OPEN_ITEMS.md`](project/OPEN_ITEMS.md) | Открытые вопросы, блокеры и отложенные задачи |
| [`project/UX_001_UI_DESIGN_SYSTEM_CHAT_BRIEF.md`](project/UX_001_UI_DESIGN_SYSTEM_CHAT_BRIEF.md) | Задание параллельному UI/UX-чату и контракт UX-001 |
| [`project/PATCH_HISTORY.md`](project/PATCH_HISTORY.md) | История технических этапов и repair |
| [`project/BASELINE_HISTORY.md`](project/BASELINE_HISTORY.md) | Принятые Git baseline и tags |
| [`project/ACCEPTANCE_HISTORY.md`](project/ACCEPTANCE_HISTORY.md) | Технические и пользовательские приёмки |
| [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md) | Текущая передача контекста |
| [`project/NEW_CHAT_STARTER.md`](project/NEW_CHAT_STARTER.md) | Стартовый контракт нового интеграционного чата |

## Процесс разработки

| Документ | Назначение |
|---|---|
| [`process/PROJECT_OPERATING_SYSTEM.md`](process/PROJECT_OPERATING_SYSTEM.md) | Полная операционная система проекта |
| [`process/DEVELOPMENT_WORKFLOW.md`](process/DEVELOPMENT_WORKFLOW.md) | GitHub-first/VPS-first цикл |
| [`process/GIT_WORKFLOW.md`](process/GIT_WORKFLOW.md) | Ветки, commits и защита истории |
| [`process/BRANCH_AND_PR_POLICY.md`](process/BRANCH_AND_PR_POLICY.md) | Контракт ветки и PR |
| [`process/CI_AND_QUALITY_GATES.md`](process/CI_AND_QUALITY_GATES.md) | Автоматические и ручные gates |
| [`process/DEFINITION_OF_DONE.md`](process/DEFINITION_OF_DONE.md) | Условия готовности изменения |
| [`process/RELEASE_PROCESS.md`](process/RELEASE_PROCESS.md) | Принятие, merge, deployment и baseline |
| [`process/DOCUMENTATION_MAINTENANCE.md`](process/DOCUMENTATION_MAINTENANCE.md) | Обновление документов без расхождения истины |
| [`process/PARALLEL_CHAT_WORKFLOW.md`](process/PARALLEL_CHAT_WORKFLOW.md) | Разделение исследовательских и интеграционных чатов |

## Runbook

| Документ | Назначение |
|---|---|
| [`runbooks/PREVIEW_RUNBOOK.md`](runbooks/PREVIEW_RUNBOOK.md) | Accepted preview |
| [`runbooks/DEVELOPMENT_RUNBOOK.md`](runbooks/DEVELOPMENT_RUNBOOK.md) | Active development |
| [`runbooks/DATABASE_BACKUP_AND_RESTORE.md`](runbooks/DATABASE_BACKUP_AND_RESTORE.md) | Dump, restore и проверка |
| [`runbooks/PRESENTATION_DATA_RESET.md`](runbooks/PRESENTATION_DATA_RESET.md) | Сброс development из preview |
| [`runbooks/SSH_TUNNEL_ACCESS.md`](runbooks/SSH_TUNNEL_ACCESS.md) | Доступ с ПК и Termux |
| [`runbooks/BRANCH_SWITCHING.md`](runbooks/BRANCH_SWITCHING.md) | Безопасное переключение active branch |
| [`runbooks/POST_MERGE_DEPLOYMENT.md`](runbooks/POST_MERGE_DEPLOYMENT.md) | Синхронизация preview после merge |
| [`runbooks/INCIDENT_AND_ROLLBACK.md`](runbooks/INCIDENT_AND_ROLLBACK.md) | Отказ, диагностика и откат |

Технически подробный исходный runbook INFRA-003 сохраняется в [`../deploy/DEVELOPMENT_RUNBOOK.md`](../deploy/DEVELOPMENT_RUNBOOK.md); канонический пользовательский маршрут расположен в `docs/runbooks/`.

## Приёмка

| Документ | Назначение |
|---|---|
| [`acceptance/INTERNAL_PROTOTYPE_ACCEPTANCE.md`](acceptance/INTERNAL_PROTOTYPE_ACCEPTANCE.md) | Контракт внутреннего прототипа |
| [`acceptance/DEMONSTRATION_SCENARIOS.md`](acceptance/DEMONSTRATION_SCENARIOS.md) | Сквозные сценарии показа |
| [`acceptance/REGRESSION_CHECKLIST.md`](acceptance/REGRESSION_CHECKLIST.md) | Повторяемая ручная проверка |
| [`acceptance/KNOWN_LIMITATIONS.md`](acceptance/KNOWN_LIMITATIONS.md) | Честные ограничения прототипа |

## Релизы и архитектурные решения

- [`releases/RELEASE_NOTES.md`](releases/RELEASE_NOTES.md) — сводные release notes.
- [`adr/`](adr/) — принятые архитектурные решения; старые ADR не переписываются молча.
- [`../CHANGELOG.md`](../CHANGELOG.md) — хронология значимых изменений.

## Исторические пути

Каталог `docs/project_state/` был ранним механизмом непрерывности контекста. Его содержимое мигрируется в `docs/project/`; старые пути не являются каноническими после DOCS-001.

## Правило актуальности

Документ с фактическим состоянием обязан содержать дату обновления и проверяемый baseline. Плановые документы должны явно отличать `сделано`, `частично`, `план`, `решение отложено` и `требует ревизии`.
