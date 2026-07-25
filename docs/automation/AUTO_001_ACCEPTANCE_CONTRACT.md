# AUTO-001 — контракт приёмки

## 1. Definition of Done

AUTO-001 MVP готов, когда:

1. Развёртывает exact current PR head на development.
2. Не предоставляет произвольный shell.
3. Не меняет preview.
4. Выполняет check, полный `test apps` и status.
5. Публикует structured evidence.
6. Безопасно обрабатывает failure.
7. Не считает старый SHA актуальным после нового commit.
8. Не требует от пользователя VPS-команд и копирования полного лога.
9. Технически не имеет права merge или repository write.
10. Исполняет PR-код только в изолированном development runtime без host/preview capabilities.
11. Прошёл положительные и отрицательные acceptance cases.

## 2. Functional cases

### AC-F-001 — successful refresh

Обычный Python/template/documentation work item:

- green required checks;
- exact SHA;
- `refresh`;
- check success;
- test suite success;
- status/HTTP success;
- PR evidence published.

### AC-F-002 — successful rebuild

Изменение container/dependency contract выполняет `rebuild` по явно выбранному profile.

### AC-F-003 — failed test

Намеренно падающий test приводит к `FAILED`, не маскируется retry и сохраняет sanitised log.

### AC-F-004 — superseded SHA

После нового commit старый `PASSED` не считается result текущего PR.

### AC-F-005 — repeated SHA

Повторный запуск того же SHA идемпотентен и не повреждает development.

## 3. Security cases

### AC-S-001 — input rejection

Unknown option, shell separator, arbitrary path/URL/environment value или malformed SHA отклоняются до изменения VPS.

### AC-S-002 — main protection

Попытка deploy `main` в development блокируется.

### AC-S-003 — dirty worktree

Dirty development worktree блокирует switch.

### AC-S-004 — no interactive shell

Automation credential не открывает interactive SSH shell.

### AC-S-005 — no repository write or merge

Workflow credential не может писать repository contents, отправлять approval или выполнять merge. Проверка должна быть технической, а не только декларативной.

### AC-S-006 — secret redaction

Test secret marker отсутствует в summary и artifact.

### AC-S-007 — preview isolation

Preview HEAD, health, container state и database identity не изменяются.

### AC-S-008 — PR runtime isolation

Development container, выполняющий текущий PR-код:

- не получает Docker socket;
- не запускается privileged;
- не получает host SSH keys или GitHub write credentials;
- не получает preview credentials;
- не получает writable preview/host-configuration mounts;
- использует только development network, volumes and database.

### AC-S-009 — reporting permissions

Фактический GitHub permission set соответствует выбранному reporting mechanism и не содержит избыточного `pull-requests: write`, если достаточно `issues: write`/`checks: write`.

## 4. Concurrency cases

- два запуска не меняют checkout параллельно;
- второй run получает queued/cancelled state;
- stale lock не снимается молча;
- recovery procedure документирована.

## 5. Минимальная практическая приёмка

До возврата к основной продуктовой разработке обязательны:

1. два последовательных успешных deployment;
2. один намеренно отрицательный сценарий;
3. один случай проверки актуальности exact SHA;
4. доказательство preview isolation;
5. доказательство no-shell/no-host-capabilities;
6. ноль ручных VPS-команд пользователя в штатном run.

## 6. Gate возврата к PLAN-001

PLAN-001 и product vertical slices продолжаются, когда:

```text
AUTO-001 MVP accepted
manual VPS commands per normal PR = 0
exact-SHA evidence = confirmed
preview isolation = confirmed
PR runtime isolation = confirmed
automatic merge = technically unavailable
```

AUTO-002 и последующие automation stages не блокируют возврат к продукту.
