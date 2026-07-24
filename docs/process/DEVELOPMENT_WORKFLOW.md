# ЭОД — workflow разработки

## 1. Нормальный цикл

```text
Пользователь формулирует цель
→ AI анализирует репозиторий и документы
→ AI создаёт branch/commits/PR
→ GitHub Actions выполняет gates
→ VPS development получает branch
→ checks/tests/status
→ пользователь проверяет через SSH tunnel
→ AI выполняет repair при необходимости
→ пользователь разрешает merge
→ AI merges exact head
→ preview синхронизируется и проверяется
```

## 2. Что пользователь больше не делает

- не редактирует Python, HTML, CSS, JavaScript или migrations;
- не собирает файлы из фрагментов;
- не исправляет syntax/lint errors;
- не применяет автономные patch scripts как нормальный процесс;
- не выполняет commits, push, PR или merge вручную;
- не настраивает локальное Python/Django окружение для каждого изменения;
- не переносит базы между контурами вручную.

## 3. Что остаётся пользователю

- цель и приоритет;
- предметные правила;
- оценка реального рабочего процесса;
- функциональная и визуальная приёмка;
- решение принять, отправить на repair или изменить направление;
- явное разрешение merge.

## 4. Подготовка work item

AI-разработчик:

1. читает current state, handoff and domain invariants;
2. проверяет accepted main SHA;
3. определяет затрагиваемые models/services/UI/tests/data/docs;
4. формулирует acceptance criteria;
5. создаёт branch от accepted main;
6. открывает draft PR до или вскоре после первых commits для прозрачной истории.

## 5. Реализация в GitHub

- commits создаются только в active branch;
- один commit должен иметь законченную цель, но PR может содержать несколько repair commits;
- large work item делится на reviewable slices без нарушения vertical behavior;
- secrets and real data не попадают в branch;
- documentation changes выполняются вместе с code change.

## 6. CI

Перед VPS deployment должен быть green актуальный head. Для documentation-only change допускается профильный documentation gate, но основной CI не обходится, если workflow запускает его по PR.

AI фиксирует run IDs/conclusions в PR evidence.

## 7. Синхронизация VPS development

```bash
cd /srv/eod/development

git status --short --branch
git fetch --prune origin
git pull --ff-only
```

Worktree должен быть clean. При переключении ветки используется runbook `../runbooks/BRANCH_SWITCHING.md`.

## 8. Refresh или rebuild

### Refresh

Для:

- Python source;
- templates;
- CSS/JavaScript;
- documentation без container dependency changes.

```bash
sudo bash scripts/development_stack.sh refresh
```

### Rebuild

Для:

- dependencies;
- Dockerfile;
- entrypoint;
- Compose startup contract.

```bash
sudo bash scripts/development_stack.sh rebuild
```

## 9. Проверки на VPS

Минимум:

```bash
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

Дополнительно по риску:

- migrations;
- reset development database;
- exact database identity;
- demo authentication;
- logs;
- parallel preview health;
- data counts or integrity checks.

## 10. Browser acceptance

Пользователь открывает development через local port forwarding и проходит заданный маршрут. Ветка, exact head and data state должны быть известны до проверки.

Принимаются не отдельные screenshots, а сценарий с ожидаемым результатом.

## 11. Repair

AI анализирует фактический лог/видео/описание. Repair commit создаётся в той же branch. Пользователь не должен предлагать code-level fix, хотя его предметное объяснение является основным источником для корректировки.

## 12. Merge

Merge не выполняется из фразы вроде «вроде нормально», если контекст неоднозначен. Нужна явная команда принять и слить изменение.

AI перед merge проверяет:

- PR state;
- exact head SHA;
- latest CI;
- acceptance evidence;
- absence of unresolved blocking issues.

## 13. После merge

- синхронизировать preview checkout;
- выполнить необходимый deployment action;
- проверить health and HTTP;
- зафиксировать merge commit;
- обновить baseline docs;
- переключить development на следующий active branch.

## 14. Emergency fallback

Patch-file workflow используется только при недоступности normal GitHub writes. Он не отменяет необходимость committed source of truth и повторной проверки через CI.