# AUTO-000 — Draft PR body source

## Цель

Зафиксировать architecture/security/acceptance contract минимальной автоматизации GitHub → development VPS до появления исполняемого AUTO-001.

## Baseline

```text
base: main / 4237aadc2cfdee518567024c2b45b653f49c16e7
head: docs/004-auto-000-development-automation-contract
change type: documentation-only
```

## Основные решения

- AUTO-001 устраняет только ручной PR→VPS разрыв;
- exact PR head SHA обязателен;
- один development deployment одновременно;
- GitHub-hosted runner вызывает restricted gateway;
- root-capable self-hosted PR runner запрещён;
- preview and development remain isolated;
- automatic merge запрещён;
- AUTO-002+ не блокируют возврат к PLAN-001.

## Runtime impact

```text
application code: unchanged
models/migrations: none
runtime data: unchanged
workflows: unchanged
VPS configuration: unchanged
secrets: unchanged
```

## Acceptance

AUTO-000 принимает только документационный контракт. AUTO-001 реализуется отдельным PR и должен пройти два success, один failure, exact-SHA and preview-isolation cases.
