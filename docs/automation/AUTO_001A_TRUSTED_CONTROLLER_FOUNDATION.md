# AUTO-001A — Trusted Controller Foundation

## 1. Статус

```text
work item: AUTO-001A
stage: trusted controller foundation only
branch: automation/001a-trusted-controller-foundation
Draft PR title: AUTO-001A: Trusted controller foundation
implementation status: candidate, not accepted, not merged
VPS implementation: forbidden in Stage A
```

AUTO-001A является первой частью staged-реализации AUTO-001. Он создаёт только доверенную GitHub control-plane основу, которая после отдельной пользовательской приёмки и merge сможет исполняться из default branch.

AUTO-001A не является acceptance всего AUTO-001 и не доказывает работоспособность GitHub → VPS deployment.

## 2. Baseline

```text
main at branch creation: e0ee946f5591ac9d42c4e3e4bcdc10169ea74cad
accepted application baseline: 937d2cd2b187c17fac3088ccfc52079fc4608306
application baseline impact: none
accepted automation foundation baseline: pending explicit acceptance and merge
```

AUTO-001A не изменяет application behavior, models, migrations, runtime data, preview, development database или VPS configuration.

После принятия Stage A отдельно фиксируются:

```text
accepted AUTO-001A exact PR head
AUTO-001A merge commit in main history
accepted automation foundation baseline status
```

Эта запись выполняется только после явной пользовательской команды merge. Она не повышает accepted application baseline.

## 3. Trusted workflow provenance

Управляющий workflow:

```text
.github/workflows/vps-development.yml
```

Trigger:

```text
pull_request_target: labeled
```

Разрешены только labels:

```text
vps-development-refresh
vps-development-rebuild
```

После merge workflow берётся из trusted default branch. Он checkout только exact base/default-branch event SHA:

```yaml
ref: ${{ github.sha }}
persist-credentials: false
```

PR head, PR merge ref, PR artifacts и PR-controlled scripts не checkout и не исполняются.

## 4. Effective permissions

```yaml
contents: read
pull-requests: read
actions: read
checks: read
statuses: read
```

Отсутствуют:

- `contents: write`;
- `workflows: write`;
- `pull-requests: write`;
- `issues: write`;
- `checks: write`;
- `deployments: write`;
- `id-token: write`;
- approval/review submission;
- merge capability;
- repository administration;
- secrets management.

Stage A публикует только sanitised GitHub job summary и trusted workflow-generated manifest artifact.

## 5. Request validation

Workflow повторно получает live GitHub state и fail-closed проверяет:

1. exact repository `genrudko/electronic-operational-docs`;
2. event `pull_request_target:labeled`;
3. allowlisted label;
4. actor repository permission `admin`, `maintain` или `write`;
5. PR всё ещё открыт;
6. base остаётся `main`;
7. head принадлежит тому же repository;
8. event PR number совпадает с live PR number;
9. event head SHA совпадает с exact current live PR SHA;
10. все required workflows завершены `success` именно для текущего SHA;
11. более поздний failed rerun не перекрывается старым success;
12. PR не изменяет automation/security paths.

Allowlisted required workflows:

```text
EOD CI
EOD Development Stack
EOD Documentation Contract
AUTO-001A Foundation CI
```

## 6. Blocked automation/security paths

Обычный deployment request блокируется, если PR меняет:

```text
.github/workflows/**
.github/auto001a-foundation.json
scripts/automation/**
deploy/automation/**
docs/automation/AUTO_001_SECURITY_MODEL.md
docs/automation/AUTO_001A_TRUSTED_CONTROLLER_FOUNDATION.md
docs/adr/ADR-AUTO-001A-TRUSTED-CONTROLLER-BOOTSTRAP.md
docs/runbooks/DEVELOPMENT_AUTOMATION_TRUST_BOOTSTRAP.md
```

Такие изменения требуют отдельного staged infrastructure review и не могут развёртывать сами себя.

## 7. Immutable manifest

При успешной GitHub validation создаётся canonical JSON manifest со следующими доказательствами:

- repository;
- PR number;
- base/head refs;
- exact current head SHA;
- requested profile;
- actor and effective repository permission;
- trusted workflow SHA;
- workflow run ID/attempt;
- exact-SHA required workflow run IDs;
- changed-file count and SHA-256 digest;
- state `VALIDATED_STAGE_A`;
- VPS state `BLOCKED`;
- VPS side effects `NONE_STAGE_A`.

Manifest получает SHA-256 и хранится 14 дней как artifact, созданный самим trusted workflow. PR artifacts не загружаются.

## 8. Deterministic Stage A boundary

До отдельного разрешения Stage B:

```text
VPS phase: BLOCKED
VPS access: NONE
SSH: absent
VPS deploy secret: absent
restricted account: absent
forced command: absent
real deployment: absent
```

Workflow не содержит реального SSH/deployment path. Его VPS skeleton только детерминированно фиксирует `BLOCKED` в job summary.

## 9. Tests

`.github/workflows/auto-001a-foundation-ci.yml` выполняет без secrets:

- Python compile;
- Ruff;
- unit tests;
- negative request tests;
- exact-SHA workflow tests;
- stale SHA test;
- failed rerun test;
- fork/cross-repository rejection;
- actor authorization rejection;
- blocked-path rejection;
- static permission audit;
- запрет PR artifact download;
- запрет SSH/deploy surface;
- trusted workflow policy check.

Этот PR CI является unprivileged verification контуром и не использует VPS.

## 10. Acceptance boundary

Merge AUTO-001A разрешается только отдельной явной командой пользователя после:

- exact-head CI;
- review diff;
- provenance review;
- effective permission review;
- negative-test evidence;
- подтверждения отсутствия VPS side effects;
- проверки rollback.

После merge Stage A foundation получает отдельный accepted automation foundation baseline. Stage B остаётся заблокированным до нового разрешения.
