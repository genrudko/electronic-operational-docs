# ЭОД — сброс development presentation data

## Назначение

Восстановить active development database из текущего accepted preview без записи в preview и без смешивания контуров.

## Preconditions

- preview checkout существует и находится на `main`;
- development checkout существует и находится не на `main`;
- оба env files существуют с правильными database names/users;
- preview and development database containers healthy;
- development worktree clean;
- текущий development code уже получен из GitHub.

## Команда

```bash
cd /srv/eod/development
sudo bash scripts/reset_development_database.sh
```

## Скрипт обязан

1. проверить repository roles;
2. проверить exact database/user/port guards;
3. запустить только необходимые database containers;
4. создать backup текущей development database;
5. создать fresh preview seed dump;
6. остановить development application;
7. восстановить dump только в `eod_development`;
8. применить migrations active branch;
9. проверить database identity;
10. проверить обе demo accounts;
11. запустить development application;
12. дождаться health endpoint;
13. вывести paths backups/dump.

## Ожидаемые признаки успеха

```text
Development database and demo authentication: ok
DEVELOPMENT DATABASE RESET COMPLETE
{"status": "ok"}
```

Database identity:

```text
Development database: eod_development / eod_development
```

## После сброса

```bash
cd /srv/eod/development
sudo bash scripts/development_stack.sh status
```

Затем проверить одновременно preview and development:

```bash
curl --fail --silent --show-error http://127.0.0.1:8765/_health/
echo
curl --fail --silent --show-error http://127.0.0.1:8766/_health/
echo
```

## Что не является ошибкой

Несколько `connection reset by peer` во время старта app могут быть нормальны, если retry loop в итоге получает successful health и script завершается с exit code 0.

## Что является failure

- preview branch не `main`;
- development branch `main`;
- неправильная database identity;
- backup/dump empty;
- restore error;
- migration failure;
- demo authentication failure;
- health timeout;
- изменение или остановка preview.

## Ограничение

Reset development data не является deployment preview и не делает active branch принятой.