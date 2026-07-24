# ЭОД — backup и restore PostgreSQL

## 1. Правило

Любая разрушительная migration, import, data transform или preview update с data impact начинается с verified backup.

Backups хранятся вне Git:

```text
/srv/eod/backups
```

## 2. Что фиксируется

- contour: preview/development;
- database name;
- source branch and HEAD;
- timestamp;
- dump path;
- file size;
- checksum при значимом release;
- restore verification result.

## 3. Preview dump

```bash
cd /srv/eod/repository
STAMP="$(date +%Y%m%d_%H%M%S)"
DUMP="/srv/eod/backups/eod_preview_${STAMP}.dump"

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  exec -T db \
  pg_dump --format=custom --no-owner --no-acl \
  --username eod_preview eod_preview \
  | sudo tee "$DUMP" >/dev/null

sudo test -s "$DUMP"
sudo stat -c '%s %n' "$DUMP"
```

Не выводить password; container получает его из environment.

## 4. Development dump

Предпочтительно использовать automation внутри `reset_development_database.sh`. Для отдельного dump применяются development env/compose и exact database/user `eod_development`.

## 5. Checksum

```bash
sudo sha256sum /srv/eod/backups/<dump>.dump
```

Checksum сохраняется в release/incident evidence, но сам dump не коммитится.

## 6. Restore principles

- restore только в явно выбранную target database;
- preview dump не восстанавливается поверх preview без отдельного incident decision;
- normal preview-to-development restore выполняется только safe reset script;
- `--no-owner` используется для разделения PostgreSQL users;
- после restore применяются migrations target branch;
- database identity проверяется из Django;
- demo authentication and key counts проверяются.

## 7. Restore development from dump

Предпочтительный путь:

```bash
cd /srv/eod/development
sudo bash scripts/reset_development_database.sh
```

Для ручного incident restore сначала остановить development app, затем использовать target development db container. Точная команда зависит от dump and schema state и должна быть сформирована в incident work item, а не копироваться вслепую.

## 8. Verification

Обязательно:

- `pg_restore --list` читает dump;
- file size non-zero;
- migrations success;
- `python manage.py check`;
- database identity;
- demo user authentication;
- health endpoint;
- main page HTTP 200;
- профильные object counts/integrity checks;
- preview remains healthy, если восстанавливался development.

## 9. Retention

Пока официальная retention policy не утверждена:

- не удалять backup, созданный перед текущим accepted release;
- не накапливать неограниченное число временных development backups;
- удаление выполнять только после проверки более нового restore point;
- список significant backups фиксировать в acceptance/release evidence.

## 10. Запрещено

- хранить dump в repository;
- восстанавливать на основании только похожего имени файла;
- смешивать preview/development env;
- использовать restore без target identity check;
- удалять единственный подтверждённый backup до завершения post-merge gate;
- объявлять backup рабочим без restore verification.