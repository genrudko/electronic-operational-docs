# ADR-AUTO-001A — staged bootstrap доверенного controller

## Статус

```text
proposed in Draft PR
acceptance: pending
application baseline impact: none
VPS impact: none in Stage A
```

## Контекст

AUTO-001 должен запускать exact head открытого PR на изолированном development-контуре VPS. При этом PR code до пользовательской приёмки считается недоверенным относительно VPS host и accepted preview.

Evidence-based gap analysis подтвердил два критических дефекта прямого использования текущего manual controller:

1. `scripts/development_stack.sh` находится в target PR checkout и запускается от root;
2. `compose.development.yaml` также находится в target PR checkout и может запросить host capabilities.

Следовательно, непосредственный вызов текущих PR-controlled files из privileged automation создаёт root-equivalent boundary violation.

Одновременно новый trusted workflow не может доказательно использоваться для собственной pre-merge acceptance: `pull_request_target` и `workflow_dispatch` получают trusted workflow только после его появления в default branch.

## Решение

AUTO-001 реализуется staged:

```text
AUTO-001A — Trusted Controller Foundation
→ explicit user acceptance and merge
→ accepted automation foundation baseline
→ отдельное разрешение Stage B
→ AUTO-001B — restricted VPS gateway/orchestrator
```

AUTO-001A содержит только:

- default-branch trusted event controller;
- live GitHub API validation;
- same-repository/open/base-main/exact-SHA checks;
- actor authorization;
- allowlisted labels;
- exact-SHA required workflow verification;
- rename-aware automation/security path block;
- GitHub concurrency;
- immutable manifest;
- read-only permissions;
- sanitised summary;
- tests and documentation.

## Trust boundary Stage A

```text
trusted workflow from default branch
→ checkout exact trusted base SHA only
→ GitHub API read operations
→ local trusted validator
→ immutable manifest
→ sanitised summary
→ deterministic VPS state BLOCKED
```

Недоверенный PR code, PR checkout и PR artifacts не входят в эту цепочку.

## Permissions

Stage A использует только:

```yaml
contents: read
pull-requests: read
actions: read
```

`checks: read` и `statuses: read` не нужны: workflow получает required workflow runs через Actions API и не обращается к Checks API или commit Statuses API.

GitHub token не получает repository write, workflow write, PR write, approval или merge capability.

## Последствия

### Положительные

- устраняется self-bootstrap через недоверенный workflow;
- PR не может изменить controller и сразу использовать его с privileged boundary;
- Stage B получает проверяемый trusted entry point из `main`;
- required checks и exact SHA проверяются по live state;
- rename не позволяет вынести защищённый файл в незащищённый путь или занести файл в защищённый путь;
- scope Stage A не требует VPS secrets или сетевого доступа;
- application baseline остаётся неизменным.

### Ограничения

- Stage A сам по себе не выполняет deployment;
- до merge trusted controller не может быть проверен как default-branch runtime;
- после merge требуется отдельный canary/evidence gate перед Stage B;
- изменение automation/security files всегда требует отдельного staged review;
- Stage A merge не является acceptance всего AUTO-001.

## Отклонённые варианты

### Один implementation PR для workflow и VPS

Отклонён: новый workflow не является trusted default-branch workflow до собственного merge.

### `pull_request` workflow с VPS secret

Отклонён: workflow и исполняемый код контролируются PR head.

### Ordinary self-hosted runner на VPS

Отклонён: сочетание PR code, Docker socket, secrets и privilege создаёт root-equivalent доступ.

### Root execution текущего `scripts/development_stack.sh`

Отклонён: file принадлежит недоверенному target checkout.

### Target-controlled Compose как host control plane

Отклонён: PR может запросить Docker socket, privileged mode, host paths или preview access.

### Self-applying workflow/bootstrap payload

Отклонён: нарушает review/merge boundary и прямой запрет проекта.

## Rollback

До merge rollback — закрыть Draft PR и удалить branch.

После merge rollback — отдельным reviewed revert удалить:

- trusted controller workflow;
- foundation CI;
- policy/validator/tests;
- Stage A documentation.

VPS rollback не требуется, поскольку Stage A не изменяет VPS.
