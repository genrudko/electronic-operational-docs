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
9. Не имеет права merge.
10. Прошёл положительные и отрицательные acceptance cases.

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

### AC-S-001

Unknown option, shell separator, path или malformed SHA отклоняются до изменения VPS.

### AC-S-002

Попытка deploy `main` в development блокируется.

### AC-S-003

Dirty development worktree блокирует switch.

### AC-S-004

Automation credential не открывает interactive SSH shell.

### AC-S-005

Workflow token не может писать repository contents и выполнять merge.

### AC-S-006

Test secret marker отсутствует в summary и artifact.

### AC-S-007

Preview HEAD, health и database identity не изменяются.

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
5. ноль ручных VPS-команд пользователя в штатном run.

## 6. Gate возврата к PLAN-001

PLAN-001 и product vertical slices продолжаются, когда:

```text
AUTO-001 MVP accepted
manual VPS commands per normal PR = 0
exact-SHA evidence = confirmed
preview isolation = confirmed
automatic merge = absent
```

AUTO-002 и последующие automation stages не блокируют возврат к продукту.
