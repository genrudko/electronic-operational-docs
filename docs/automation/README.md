# ЭОД — автоматизация разработки

## Статус

Каталог фиксирует принятый архитектурный контракт автоматизации GitHub-first/VPS-first процесса.

После принятия AUTO-000:

```text
contract: accepted
AUTO-000 merge: 937d2cd2b187c17fac3088ccfc52079fc4608306
AUTO-001 implementation: not started
current VPS workflow: manual
automatic merge: forbidden
```

AUTO-000 принят пользователем, squash-merged в `main` и post-merge проверен на preview. Он не менял runtime, GitHub Actions, VPS, secrets или способ фактического deployment. До принятия и реализации AUTO-001 продолжает действовать ручной процесс из `docs/process/DEVELOPMENT_WORKFLOW.md`.

## Цель

Сократить техническое участие владельца продукта до:

1. постановки задачи и предметных ограничений;
2. предметной и визуальной приёмки;
3. явного разрешения merge.

Пользователь не должен на каждом PR:

- переключать ветку на VPS;
- выбирать и запускать `refresh`/`rebuild`;
- запускать `check`, `test` и `status`;
- копировать полные терминальные логи в чат;
- выполнять post-merge технические действия.

## Этапы

| Этап | Назначение | Статус |
|---|---|---|
| AUTO-000 | архитектура, безопасность, acceptance contract и roadmap | принят, merged и post-merge verified |
| AUTO-001 | минимальный GitHub/VPS development orchestrator | следующий implementation work item |
| AUTO-002+ | классификация, browser acceptance, structured evidence и preview deployment | только по подтверждённой необходимости |

## Документы

- [`AUTO_000_SCOPE.md`](AUTO_000_SCOPE.md)
- [`AUTOMATION_MASTER_PLAN.md`](AUTOMATION_MASTER_PLAN.md)
- [`AUTO_001_GITHUB_VPS_ORCHESTRATOR.md`](AUTO_001_GITHUB_VPS_ORCHESTRATOR.md)
- [`AUTO_001_SECURITY_MODEL.md`](AUTO_001_SECURITY_MODEL.md)
- [`AUTO_001_ACCEPTANCE_CONTRACT.md`](AUTO_001_ACCEPTANCE_CONTRACT.md)
- [`AUTO_001_IMPLEMENTATION_ROADMAP.md`](AUTO_001_IMPLEMENTATION_ROADMAP.md)
- [`AUTO_001_DECISION_REGISTER.md`](AUTO_001_DECISION_REGISTER.md)

## Непереговорные границы

- GitHub остаётся единственным источником кода.
- VPS не создаёт commits и не пишет в GitHub.
- Accepted preview и active development изолированы.
- AUTO-001 не получает право автоматического merge.
- Запуск выполняется только для exact PR head SHA.
- Обычный self-hosted runner с `sudo` и Docker socket не используется.
- Secrets, private keys и `.env` не попадают в Git.
- До отдельного официального решения автоматизация обслуживает только независимый демонстрационный прототип.
