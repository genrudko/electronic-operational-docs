# ЭОД — incident и rollback

## 1. Incident criteria

Incident считается любое событие, при котором:

- preview unavailable or unhealthy;
- database identity unexpectedly changed;
- migration/data transform failed;
- demo authentication or critical route broke after merge;
- development action affected preview;
- secret or sensitive data exposed;
- branch/head on VPS differs from expected accepted state;
- backup/restore integrity cannot be confirmed.

## 2. First response

1. остановить дальнейшие изменения;
2. не выполнять повторные destructive commands вслепую;
3. зафиксировать время, contour, branch, HEAD and commands;
4. сохранить container status/logs;
5. определить, затронуты code, schema, data, secrets or availability;
6. сохранить существующие backups;
7. не объявлять change accepted.

## 3. Diagnostics

### Git

```bash
git status --short --branch
git rev-parse HEAD
git log -5 --oneline --decorate
```

### Containers

```bash
sudo docker compose <args> ps --all
sudo docker compose <args> logs --tail=300 --no-color
```

### Ports/health

```bash
sudo ss -ltnp | grep -E '127\.0\.0\.1:(8765|8766)'
curl --fail --silent --show-error http://127.0.0.1:<port>/_health/
```

### Database

Проверить container health, database name/user, migration state and affected object counts.

## 4. Rollback hierarchy

Выбирать минимально разрушительный способ:

1. restart/recreate same accepted image/config;
2. revert faulty configuration commit;
3. revert application merge commit;
4. restore database from verified backup;
5. combined code revert and database restore, если schema/data несовместимы.

`git reset --hard` и force-push не являются normal rollback accepted history.

## 5. Development incident

Development можно восстановить из accepted preview через:

```bash
cd /srv/eod/development
sudo bash scripts/reset_development_database.sh
```

Это не применяется к preview incident.

## 6. Preview incident

Перед restore:

- подтвердить exact backup source;
- определить schema version;
- выбрать code commit compatible with backup;
- остановить application writes;
- сохранить текущую повреждённую/сомнительную database как forensic backup, если возможно;
- выполнить restore under explicit incident plan;
- применить only compatible migrations;
- выполнить full post-restore gate.

## 7. Secret incident

- не цитировать secret повторно;
- отозвать/заменить credential;
- проверить logs/history/artifacts;
- удалить secret from branch/history по отдельному плану;
- обновить deployment;
- добавить preventive gate;
- зафиксировать факт без раскрытия значения.

## 8. Verification after rollback

- branch/head expected;
- clean worktree;
- app/db healthy;
- database identity correct;
- health and main HTTP success;
- demo authentication;
- affected scenario;
- preview/development isolation;
- no pending migrations;
- backup paths and restore result recorded.

## 9. Documentation

Incident обновляет:

- `project/DECISION_LOG.md`;
- `project/ACCEPTANCE_HISTORY.md`;
- `project/BASELINE_HISTORY.md`, если baseline changed;
- `project/OPEN_ITEMS.md`;
- release notes;
- profile ADR/runbook, если причина системная.

## 10. Blameless rule

Цель анализа — устранить механизм отказа. Root cause описывается технически: отсутствующий guard, неверная migration assumption, недостаточный test, stale document, wrong environment selection и т.п.

## 11. Запрещено

- скрывать incident переписыванием истории;
- удалять единственный backup;
- смешивать env files;
- повторять failed destructive command без root cause;
- восстанавливать preview из development dump без отдельного доказательного решения;
- считать service recovered до verification gate.