# AUTO-001 — roadmap реализации

## 1. Условие старта

- AUTO-000 принят и merged.
- `main` и canonical docs актуальны.
- QUALITY-001 test command подтверждён.
- Текущий manual workflow остаётся рабочим rollback.

## 2. Аудит перед кодом

Отдельный implementation chat обязан прочитать:

- `AGENTS.md`;
- `docs/INDEX.md`;
- current state/handoff;
- development workflow;
- INFRA-003 ADR/runbooks;
- `compose.development.yaml`;
- `scripts/development_stack.sh`;
- `scripts/reset_development_database.sh`;
- current workflows;
- backup/restore runbooks.

Дополнительно проверить фактическую сетевую доступность VPS для GitHub-hosted runner, effective GitHub permissions, container capabilities and mounts и не переносить адреса, ключи или secrets в Git или чат.

## 3. Разбиение

### AUTO-001A — VPS-local orchestrator

- manifest validator;
- strict CLI;
- exact-SHA checks;
- development-only lock;
- dry-run;
- evidence JSON;
- unit/static tests.

На этом этапе orchestrator запускается непосредственно на VPS одним контролируемым bootstrap command. Локальный репозиторий пользователя не используется; GitHub остаётся единственным источником кода.

### AUTO-001B — restricted gateway

- отдельный OS account;
- forced command;
- credential installation;
- allowlist;
- negative tests;
- rotation/revoke runbook.

### AUTO-001C — trusted GitHub workflow

- trusted trigger;
- minimal permissions;
- required-check verification;
- concurrency;
- gateway invocation;
- private artifact;
- PR/check summary без repository-write or merge capability.

### AUTO-001D — acceptance hardening

- superseded handling;
- preview before/after evidence;
- redaction test;
- GitHub permission audit;
- PR runtime isolation proof;
- два success и один failure case;
- final documentation.

При малом фактическом объёме A+B и C+D можно объединить, но rollback boundaries должны сохраниться.

## 4. Предлагаемые пути

Окончательно проверяются по repository conventions:

```text
scripts/automation/
  validate_development_run.py
  render_development_evidence.py

deploy/automation/
  development_gateway.sh
  development_orchestrator.sh
  eod-development-automation.example

.github/workflows/
  vps-development.yml

docs/runbooks/
  DEVELOPMENT_AUTOMATION_BOOTSTRAP.md
  DEVELOPMENT_AUTOMATION_RECOVERY.md
```

## 5. Один неизбежный ручной bootstrap

Первичная установка на VPS требует:

- создать restricted OS account;
- установить root-owned gateway/orchestrator;
- установить отдельный public key/credential;
- закрепить forced command;
- проверить no-shell behavior;
- добавить GitHub secret через защищённый интерфейс GitHub;
- выполнить dry-run.

Bootstrap должен быть одним последовательным проверяемым блоком с rollback. Запрещены Base64 payload, временные part-файлы, self-applying workflow и передача private key/secret в чат.

## 6. Tests

### Static

- Ruff для Python;
- ShellCheck;
- YAML validation;
- dangerous shell construct scan;
- permissions assertions.

### Unit

- manifest schema;
- SHA/profile validators;
- argument rejection;
- state rendering;
- redaction;
- lock metadata.

### Integration

- fake git checkout;
- fake Compose commands;
- failed health/test;
- lock contention;
- superseded run;
- reporting without merge/repository-write permission.

### Security negative

- interactive SSH attempt rejected;
- malformed SHA/path/URL/environment rejected;
- Docker socket absent;
- privileged mode absent;
- host keys and preview credentials absent;
- writable preview mounts absent;
- secret marker absent from summary/artifact.

### VPS

- dry-run;
- real refresh;
- real rebuild;
- failed test;
- preview isolation;
- repeated same SHA;
- exact-SHA and superseded proof.

## 7. Rollback

- disable workflow;
- remove/revoke deploy credential;
- disable forced-command account;
- restore manual `development_stack.sh` workflow;
- не удалять development database или volumes;
- preview не затрагивается.

## 8. Завершение

После acceptance:

- current manual workflow помечается fallback;
- AUTO-001 становится штатным PR→VPS route;
- PLAN-001 продолжается;
- первый product vertical slice служит эксплуатационной проверкой orchestrator.
