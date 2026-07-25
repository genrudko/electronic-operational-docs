# ЭОД — автоматизация разработки

## Статус

Каталог фиксирует принятый архитектурный контракт автоматизации GitHub-first/VPS-first процесса и candidate implementation Stage A.

```text
AUTO-000 contract: accepted
AUTO-000 merge: 937d2cd2b187c17fac3088ccfc52079fc4608306
AUTO-001A: candidate Draft PR, not accepted, not merged
AUTO-001B/VPS implementation: not authorised
current VPS workflow: manual
automatic merge: forbidden
```

AUTO-000 принят пользователем, squash-merged в `main` и post-merge проверен на preview. AUTO-001A создаёт только trusted GitHub controller foundation. До отдельной приёмки и merge Stage A, а затем отдельного разрешения Stage B продолжает действовать ручной процесс из `docs/process/DEVELOPMENT_WORKFLOW.md`.

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
| AUTO-001A | trusted default-branch controller foundation | candidate, отдельный Draft PR, VPS side effects запрещены |
| AUTO-001B | restricted VPS gateway/orchestrator | заблокирован до отдельного разрешения после Stage A |
| AUTO-002+ | классификация, browser acceptance, structured evidence и preview deployment | только по подтверждённой необходимости |

## Документы

- [`AUTO_000_SCOPE.md`](AUTO_000_SCOPE.md)
- [`AUTOMATION_MASTER_PLAN.md`](AUTOMATION_MASTER_PLAN.md)
- [`AUTO_001_GITHUB_VPS_ORCHESTRATOR.md`](AUTO_001_GITHUB_VPS_ORCHESTRATOR.md)
- [`AUTO_001_SECURITY_MODEL.md`](AUTO_001_SECURITY_MODEL.md)
- [`AUTO_001_ACCEPTANCE_CONTRACT.md`](AUTO_001_ACCEPTANCE_CONTRACT.md)
- [`AUTO_001_IMPLEMENTATION_ROADMAP.md`](AUTO_001_IMPLEMENTATION_ROADMAP.md)
- [`AUTO_001_DECISION_REGISTER.md`](AUTO_001_DECISION_REGISTER.md)
- [`AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md`](AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md)
- [`../adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md`](../adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md)
- [`../runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md`](../runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md)

## Непереговорные границы

- GitHub остаётся единственным источником кода.
- VPS не создаёт commits и не пишет в GitHub.
- Accepted preview и active development изолированы.
- AUTO-001 не получает право автоматического merge.
- Запуск выполняется только для exact PR head SHA.
- Обычный self-hosted runner с `sudo` и Docker socket не используется.
- Secrets, private keys и `.env` не попадают в Git.
- PR code не исполняется trusted workflow на GitHub host boundary.
- Automation/security changes не имеют права развёртывать сами себя.
- AUTO-001A не изменяет VPS и фиксирует будущую VPS-фазу только как `BLOCKED`.
- До отдельного официального решения автоматизация обслуживает только независимый демонстрационный прототип.
