# Runbook — AUTO-001A trusted controller bootstrap

## 1. Назначение

Этот runbook применяется только к AUTO-001A — GitHub trusted controller foundation.

Он не создаёт VPS account, forced command, SSH route, deploy secret или runtime deployment. Любые такие действия относятся к отдельному Stage B.

## 2. Исходные baseline

Перед работой подтвердить:

```text
repository: genrudko/electronic-operational-docs
base branch: main
main at branch creation: e0ee946f5591ac9d42c4e3e4bcdc10169ea74cad
accepted application baseline: 937d2cd2b187c17fac3088ccfc52079fc4608306
Stage A application impact: none
```

Также проверить:

- open PR inventory;
- отсутствие конфликтующей Stage A branch;
- PLAN-001 / PR #7 не изменяется;
- Stage A PR остаётся Draft;
- merge не выполняется без отдельной команды пользователя.

## 3. Review gate Draft PR

### 3.1 Exact branch and SHA

В PR открыть `Commits` и `Files changed`, затем зафиксировать:

```text
branch: automation/001a-trusted-controller-foundation
exact current head SHA: <40-hex>
base: main
```

Все CI/evidence должны относиться к этому exact head. После нового commit прежние результаты не являются acceptance evidence.

### 3.2 Diff scope

Допустимы только:

```text
.github/auto001a-foundation.json
.github/workflows/auto-001a-foundation-ci.yml
.github/workflows/vps-development.yml
scripts/automation/auto_001a_foundation.py
tests/automation/test_auto_001a_foundation.py
docs/automation/AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md
docs/adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md
docs/runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md
релевантные documentation index/status updates
```

Не допускаются:

- application code;
- models/migrations;
- Compose/runtime changes;
- VPS files;
- secrets;
- private keys;
- `.env`;
- Base64 payload;
- temporary part-files;
- PLAN-001 files;
- automatic merge configuration.

### 3.3 Workflow provenance

Проверить `.github/workflows/vps-development.yml`:

```text
trigger: pull_request_target / labeled
trusted checkout ref: ${{ github.sha }}
persist-credentials: false
PR checkout: absent
PR artifact download: absent
PR code execution: absent
```

`github.sha` в `pull_request_target` используется как exact trusted base/default-branch event SHA. Workflow дополнительно сравнивает checkout HEAD с `GITHUB_SHA`.

### 3.4 Effective permissions

Разрешены только:

```yaml
contents: read
pull-requests: read
actions: read
```

`checks: read` и `statuses: read` отсутствуют, потому что controller использует Actions API для списка workflow runs и не обращается к Checks API или commit Statuses API.

Проверить отсутствие любого `write`, `id-token`, environment deployment, approval и merge surface.

### 3.5 Trigger and authorization

Разрешены только labels:

```text
vps-development-refresh
vps-development-rebuild
```

Actor обязан иметь GitHub repository permission:

```text
admin
maintain
write
```

Неавторизованный actor, fork, закрытый PR, base не `main`, stale SHA или неизвестный label должны блокироваться.

### 3.6 Required exact-SHA workflows

Для live current PR head требуются successful pull-request runs:

```text
EOD CI
EOD Development Stack
EOD Documentation Contract
AUTO-001A Foundation CI
```

Проверяется latest run/attempt для каждого имени. Старый successful run не перекрывает более поздний failed rerun.

### 3.7 Automation/security path block

Для каждого changed file controller получает:

```text
filename
previous_filename — только когда GitHub возвращает его для rename
```

Оба имени проверяются по защищённым путям:

```text
.github/workflows/**
.github/auto001a-foundation.json
scripts/automation/**
deploy/automation/**
allowlisted security documents
```

Проверить negative tests:

```text
protected → unprotected
unprotected → protected
protected → protected
```

Любой из этих случаев обязан получить `BLOCKED` до Stage B.

## 4. Exact-head CI gate

Обязательные checks Draft PR:

```text
AUTO-001A Foundation CI — success
EOD CI — success
EOD Development Stack — success
EOD Documentation Contract — success
```

В AUTO-001A Foundation CI проверить шаги:

- compile;
- Ruff;
- unit/negative tests;
- workflow policy check;
- permission/deploy-surface audit;
- clean repository.

При любом новом commit повторить gate для нового exact head.

## 5. VPS side-effect proof

Stage A считается корректным только если diff и workflow подтверждают:

```text
VPS secret: absent
SSH command: absent
SSH action: absent
restricted VPS account: not created
forced command: not created
VPS API/host call: absent
real deployment: absent
VPS job state: BLOCKED
```

Наличие будущего skeleton допустимо только как job summary с детерминированным состоянием `BLOCKED`.

## 6. Merge gate

До команды пользователя PR остаётся Draft/open.

Разрешение merge должно быть отдельным и однозначным. Ни успешный CI, ни review, ни текст «готово» не являются разрешением merge.

Stage A merge означает только:

- controller foundation присутствует в default branch;
- он может считаться trusted source для следующего этапа;
- application baseline не изменился;
- полный AUTO-001 ещё не принят;
- VPS Stage B остаётся запрещённым.

## 7. Accepted automation foundation baseline

После явной приёмки и merge отдельно записать:

```text
accepted AUTO-001A exact PR head: <sha>
AUTO-001A merge commit: <sha>
accepted automation foundation baseline: <accepted exact PR head / merge record>
accepted application baseline: 937d2cd2b187c17fac3088ccfc52079fc4608306
application baseline changed: no
```

Baseline automation foundation не подменяет application baseline.

## 8. Post-merge canary before Stage B

После merge, но до разрешения Stage B, выполнить отдельный безопасный canary на обычном same-repository PR, который не меняет automation/security paths:

1. дождаться всех exact-SHA required checks;
2. добавить один allowlisted label авторизованным actor;
3. подтвердить trusted workflow SHA из `main`;
4. подтвердить immutable manifest;
5. подтвердить `vps_phase = BLOCKED`;
6. подтвердить отсутствие VPS/SSH side effects;
7. снять label при необходимости.

Canary не разрешает Stage B автоматически.

## 9. Rollback

### До merge

```text
close Draft PR
remove branch
```

VPS rollback отсутствует.

### После merge

Создать отдельный reviewed revert, который удаляет Stage A workflow/policy/code/tests/docs. До merge revert PR controller можно административно не запускать посредством удаления allowlisted labels с PR.

Не выполнять rollback через self-applying workflow или изменение VPS.
