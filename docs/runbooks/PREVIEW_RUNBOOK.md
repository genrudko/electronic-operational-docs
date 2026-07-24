# ЭОД — accepted preview runbook

## Контракт

```text
checkout: /srv/eod/repository
branch: main only
compose project: eod-preview
compose file: /srv/eod/repository/compose.preview.yaml
env: /srv/eod/secrets/preview.env
app: 127.0.0.1:8765
database: eod_preview
```

Preview содержит только принятый baseline и не используется для разработки.

## Status

```bash
cd /srv/eod/repository

git status --short --branch
git rev-parse HEAD

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  ps

curl --fail --silent --show-error \
  http://127.0.0.1:8765/_health/
echo
```

## Database identity

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  exec -T app \
  python manage.py shell -c \
  'from django.db import connection; print(connection.settings_dict["NAME"], connection.settings_dict["USER"])'
```

Ожидается `eod_preview eod_preview`.

## Logs

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  logs --tail=200 --no-color app db
```

## Update after accepted merge

Не выполнять до явного разрешения merge и успешного merge в GitHub.

```bash
cd /srv/eod/repository

git status --short --branch
git fetch --prune origin
git pull --ff-only origin main
git rev-parse HEAD
```

Дальнейшее действие зависит от diff:

- docs only — container restart обычно не требуется;
- bind-mounted source отсутствует в preview, поэтому code change требует rebuild/recreate;
- migrations/data change требует backup до migrate.

## Rebuild/recreate

```bash
cd /srv/eod/repository

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  up --detach --build
```

После этого обязательно status/health/HTTP/database identity.

## Запрещено

- checkout feature branch;
- ручное редактирование code;
- использование development.env;
- reset preview из development;
- публикация PostgreSQL port;
- миграция без backup при data impact;
- объявление нового baseline до post-merge gate.