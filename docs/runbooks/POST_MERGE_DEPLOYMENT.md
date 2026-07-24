# ЭОД — post-merge deployment

## Назначение

Синхронизировать accepted preview с принятым `main` после явного merge и доказать новый baseline.

## Preconditions

- PR merged;
- merge commit SHA известен;
- expected head при merge совпадал с принятым head;
- required CI/acceptance evidence зафиксировано;
- data/migration impact определён;
- backup создан, если требуется.

## 1. Синхронизация checkout

```bash
cd /srv/eod/repository

git status --short --branch
git fetch --prune origin
git pull --ff-only origin main
git rev-parse HEAD
```

HEAD должен совпасть с merge commit.

## 2. Выбор deployment action

### Documentation-only

Container restart не требуется. Выполнить status and health.

### Source/template/static change

Preview image содержит source, поэтому выполнить build/recreate:

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  up --detach --build
```

### Migrations/data change

1. backup preview;
2. build/recreate по плану;
3. migrate;
4. data transform/import;
5. verification;
6. rollback при failure.

Точные команды формируются в work item с учётом migrations.

## 3. Post-merge gate

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  ps

curl --fail --silent --show-error \
  http://127.0.0.1:8765/_health/
echo

curl --fail --silent --show-error \
  --output /dev/null \
  --write-out 'HTTP %{http_code}\n' \
  http://127.0.0.1:8765/
```

## 4. Database identity

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  exec -T app \
  python manage.py shell -c \
  'from django.db import connection; assert connection.settings_dict["NAME"] == "eod_preview"; print("Preview database identity: ok")'
```

## 5. Profile smoke

По риску:

- demo authentication;
- expected object counts;
- critical document integrity;
- affected route and scenario;
- no pending migrations;
- collectstatic/static asset revision.

## 6. Фиксация baseline

Обновить:

- `project/CURRENT_STATE.md`;
- `project/CURRENT_HANDOFF.md`;
- `project/BASELINE_HISTORY.md`;
- `project/ACCEPTANCE_HISTORY.md`;
- `releases/RELEASE_NOTES.md`;
- PR comment/evidence.

## 7. Development after merge

Не переключать development на `main`. Подготовить следующую branch от нового main и переключить по `BRANCH_SWITCHING.md`.

## 8. Failure

При failure:

- не объявлять merge commit accepted baseline;
- сохранить logs;
- остановить дальнейшие data actions;
- применить incident/rollback plan;
- при необходимости revert code and restore backup;
- повторно проверить preview;
- зафиксировать incident and decision.

## 9. Запрещено

- выполнять до merge;
- обходить backup при destructive change;
- описывать PR CI как post-merge gate;
- считать `git pull` достаточной проверкой;
- менять preview branch;
- оставлять preview на частично применённой migration.