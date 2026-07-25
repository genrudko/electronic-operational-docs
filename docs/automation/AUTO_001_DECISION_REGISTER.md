# AUTO-001 — реестр решений

## Статус документа

До пользовательской приёмки и merge AUTO-000 решения раздела D являются `PROPOSED`. Merge AUTO-000 переводит их в `ACCEPTED` и разрешает отдельную реализацию AUTO-001, но не означает, что AUTO-001 уже работает.

## Принятые проектные основания

| ID | Решение |
|---|---|
| A-001 | GitHub — единственный источник кода |
| A-002 | VPS — место фактического runtime/PostgreSQL acceptance |
| A-003 | Пользователь не выполняет программирование и Git write operations |
| A-004 | Merge только по явной команде пользователя |
| A-005 | Preview и development изолированы |
| A-006 | VPS deploy key для получения кода из GitHub остаётся read-only |
| A-007 | AUTO-001 является deployment/test orchestrator, а не Codex или автономным coding agent |

## Решения, принимаемые merge AUTO-000

| ID | Решение | Статус до merge | Статус после merge |
|---|---|---|---|
| D-001 | AUTO-000 является documentation-only | PROPOSED | ACCEPTED |
| D-002 | AUTO-001 реализуется отдельным PR после AUTO-000 | PROPOSED | ACCEPTED |
| D-003 | ordinary self-hosted runner с Docker socket и sudo запрещён | PROPOSED | ACCEPTED |
| D-004 | exact-SHA invariant обязателен | PROPOSED | ACCEPTED |
| D-005 | одновременно разрешён один development deployment | PROPOSED | ACCEPTED |
| D-006 | automatic merge запрещён | PROPOSED | ACCEPTED |
| D-007 | основная продуктовая работа приостанавливается только до принятого AUTO-001 MVP | PROPOSED | ACCEPTED |
| D-008 | AUTO-002+ не блокируют продолжение PLAN-001 | PROPOSED | ACCEPTED |
| D-009 | initial deployment profile задаётся явно | PROPOSED FOR MVP | ACCEPTED FOR MVP |
| D-010 | краткий result публикуется в GitHub, полный sanitised log хранится private artifact | PROPOSED | ACCEPTED |
| D-011 | automation credential технически не должен иметь merge/repository-write capability | PROPOSED | ACCEPTED |
| D-012 | код текущего PR считается недоверенным относительно VPS host и accepted preview | PROPOSED | ACCEPTED |

## Решения, подтверждаемые реализацией

| ID | Вопрос |
|---|---|
| O-001 | конкретный trusted GitHub event для управляющего trigger |
| O-002 | SSH forced command или иной restricted transport |
| O-003 | detached HEAD или временная local branch на VPS |
| O-004 | GitHub Environment и необходимость approval |
| O-005 | artifact retention |
| O-006 | политика сохранения failed development runtime |
| O-007 | сетевой маршрут GitHub-hosted runner → VPS |
| O-008 | точный OS account, sudoers и filesystem ownership |
| O-009 | update одного PR comment или отдельный check run |
| O-010 | допустимость automation для PR, меняющих automation/security files |
| O-011 | точный GitHub permission set для reporting без merge capability |
| O-012 | необходимость и способ ограничения outbound network для development containers |
| O-013 | фактическое поведение `refresh`/`rebuild` относительно migrations и rollback |

Открытые вопросы не могут молча решаться расширением полномочий. Выбранный вариант фиксируется в implementation PR и соответствующем ADR/runbook.

## Отклонено

| ID | Решение | Причина |
|---|---|---|
| R-001 | автоматический merge после green CI | не заменяет пользовательскую приёмку |
| R-002 | root SSH из произвольного PR job | чрезмерные полномочия |
| R-003 | Docker socket у PR runner или application container | root-equivalent capability |
| R-004 | исполнение изменённого PR workflow с secrets | workflow tampering |
| R-005 | commits/push с VPS | нарушает source of truth |
| R-006 | параллельные branches в одном development | race и смешение состояния |
| R-007 | secrets в repository/docs/chat | недопустимо |
| R-008 | Base64/self-applying payload | непрозрачный bootstrap и плохой rollback |
| R-009 | `pull-requests: write` только ради comment/labels без проверки меньших permissions | может дать избыточные PR mutation capabilities |
