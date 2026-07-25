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
| [`project/UX_001_UI_DESIGN_SYSTEM_CHAT_BRIEF.md`](project/UX_001_UI_DESIGN_SYSTEM_CHAT_BRIEF.md) | Исходное задание параллельному UI/UX-чату |
| [`ux/README.md`](ux/README.md) | Статус provisional UX-001 v0.3, навигация и visual acceptance gate |
| [`project/PATCH_HISTORY.md`](project/PATCH_HISTORY.md) | История технических этапов и repair |
| [`project/BASELINE_HISTORY.md`](project/BASELINE_HISTORY.md) | Принятые Git baseline и tags |
| [`project/ACCEPTANCE_HISTORY.md`](project/ACCEPTANCE_HISTORY.md) | Технические и пользовательские приёмки |
| [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md) | Текущая передача контекста |
| [`project/NEW_CHAT_STARTER.md`](project/NEW_CHAT_STARTER.md) | Стартовый контракт нового интеграционного чата |

## Автоматизация разработки

| Документ | Назначение |
|---|---|
| [`automation/README.md`](automation/README.md) | Статус AUTO-000/AUTO-001A, границы и навигация по пакету автоматизации |
| [`automation/AUTO_000_SCOPE.md`](automation/AUTO_000_SCOPE.md) | Scope документационного этапа и граница отсутствующей реализации |
| [`automation/AUTO_000_REVIEW_CHECKLIST.md`](automation/AUTO_000_REVIEW_CHECKLIST.md) | Проверка архитектуры, безопасности и готовности AUTO-000 |
| [`automation/AUTO_000_IMPLEMENTATION_HANDOFF.md`](automation/AUTO_000_IMPLEMENTATION_HANDOFF.md) | Контракт перехода к отдельной реализации AUTO-001 |
| [`automation/AUTOMATION_MASTER_PLAN.md`](automation/AUTOMATION_MASTER_PLAN.md) | Программа AUTO-000…AUTO-010 и приоритет минимального MVP |
| [`automation/AUTO_001_GITHUB_VPS_ORCHESTRATOR.md`](automation/AUTO_001_GITHUB_VPS_ORCHESTRATOR.md) | Функциональный контракт GitHub → development VPS orchestrator |
| [`automation/AUTO_001_SECURITY_MODEL.md`](automation/AUTO_001_SECURITY_MODEL.md) | Trust boundaries, угрозы и минимальные полномочия |
| [`automation/AUTO_001_ACCEPTANCE_CONTRACT.md`](automation/AUTO_001_ACCEPTANCE_CONTRACT.md) | Проверяемые functional, security и operational criteria |
| [`automation/AUTO_001_IMPLEMENTATION_ROADMAP.md`](automation/AUTO_001_IMPLEMENTATION_ROADMAP.md) | Разбиение реализации, тесты и rollback |
| [`automation/AUTO_001_DECISION_REGISTER.md`](automation/AUTO_001_DECISION_REGISTER.md) | Принятые, предлагаемые, открытые и отклонённые решения |
| [`automation/AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md`](automation/AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md) | Candidate Stage A implementation, permissions, manifest и VPS boundary |
| [`adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md`](adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md) | Решение staged bootstrap доверенного controller |

## UX/UI

| Документ | Назначение |
|---|---|
| [`ux/README.md`](ux/README.md) | Канонический статус UX-001 и граница между provisional contract и visual acceptance |
| [`ux/UX-001_v0.3/UX_001_INDEX.md`](ux/UX-001_v0.3/UX_001_INDEX.md) | Индекс консолидированного пакета v0.3 |
| [`ux/UX-001_v0.3/VISUAL_DIRECTION.md`](ux/UX-001_v0.3/VISUAL_DIRECTION.md) | Самостоятельное визуальное направление ЭОД |
| [`ux/UX-001_v0.3/UI_AUDIT.md`](ux/UX-001_v0.3/UI_AUDIT.md) | Консолидированный evidence-based аудит |
| [`ux/UX-001_v0.3/REFERENCE_SCREENS.md`](ux/UX-001_v0.3/REFERENCE_SCREENS.md) | Textual contracts трёх reference families |
| [`ux/UX-001_v0.3/DESIGN_TOKENS.md`](ux/UX-001_v0.3/DESIGN_TOKENS.md) | Candidate tokens; не визуально принятый стандарт |

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
| [`runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md`](runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md) | Review, acceptance baseline и rollback trusted controller Stage A |

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

Каталог `docs/project_state/` был ранним механизмом непрерывности контекста. Его содержимое мигрировано в `docs/project/`; старые пути не являются каноническими после DOCS-001.

## Правило актуальности

Документ с фактическим состоянием обязан содержать дату обновления и проверяемый baseline. Плановые документы должны явно отличать `сделано`, `частично`, `план`, `решение отложено` и `требует ревизии`.
