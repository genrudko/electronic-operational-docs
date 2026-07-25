# AUTO-001 — реестр решений

## Принятые проектные основания

| ID | Решение |
|---|---|
| A-001 | GitHub — единственный источник кода |
| A-002 | VPS — место фактического runtime/PostgreSQL acceptance |
| A-003 | Пользователь не выполняет программирование и Git write operations |
| A-004 | Merge только по явной команде пользователя |
| A-005 | Preview и development изолированы |
| A-006 | VPS deploy key для Git остаётся read-only |
| A-007 | AUTO-001 не является Codex/автономным coding agent |
| A-008 | Продуктовая работа приостанавливается только до AUTO-001 MVP |

## Решения AUTO-000

| ID | Решение | Статус |
|---|---|---|
| D-001 | AUTO-000 является documentation-only | принято в рамках текущего PR |
| D-002 | AUTO-001 реализуется отдельным PR после AUTO-000 | принято |
| D-003 | ordinary self-hosted runner с Docker socket и sudo запрещён | принято |
| D-004 | exact-SHA invariant обязателен | принято |
| D-005 | одновременно один development deployment | принято |
| D-006 | automatic merge запрещён | принято |
| D-007 | AUTO-002+ не блокирует продолжение PLAN-001 | принято |
| D-008 | initial deployment profile задаётся явно | принято для MVP |
| D-009 | result публикуется в GitHub, полный log хранится artifact | принято |

## Решения, подтверждаемые реализацией

| ID | Вопрос |
|---|---|
| O-001 | конкретный trusted GitHub event для label trigger |
| O-002 | SSH forced command или иной restricted transport |
| O-003 | detached HEAD или временная local branch на VPS |
| O-004 | GitHub Environment и необходимость approval |
| O-005 | artifact retention |
| O-006 | политика сохранения failed development runtime |
| O-007 | сетевой маршрут GitHub-hosted runner → VPS |
| O-008 | точный OS account, sudoers и filesystem ownership |
| O-009 | update одного PR comment или отдельный check run |
| O-010 | допустимость automation для PR, меняющих automation/security files |

Открытые вопросы не могут молча решаться расширением полномочий. Выбранный вариант фиксируется в implementation PR и соответствующем ADR/runbook.

## Отклонено

| ID | Решение | Причина |
|---|---|---|
| R-001 | автоматический merge после green CI | не заменяет пользовательскую приёмку |
| R-002 | root SSH из произвольного PR job | чрезмерные полномочия |
| R-003 | Docker socket у PR runner | root-equivalent |
| R-004 | исполнение workflow из PR с secrets | workflow tampering |
| R-005 | commits/push с VPS | нарушает source of truth |
| R-006 | параллельные branches в одном development | race и смешение состояния |
| R-007 | secrets в repository/docs | недопустимо |
| R-008 | Base64/self-applying payload | непрозрачный bootstrap и плохой rollback |
