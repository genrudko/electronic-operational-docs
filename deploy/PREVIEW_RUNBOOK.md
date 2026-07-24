# ЭОД — закрытый preview на VPS

Preview предназначен для внутренней демонстрации и приёмки. Приложение доступно только через
loopback VPS и SSH-туннель. PostgreSQL не публикует host port.

## 1. Постоянные параметры

```text
GitHub:        genrudko/electronic-operational-docs
VPS:           5.181.177.72
SSH user:      eodadmin
SSH key:       C:\Users\Gennadiy\.ssh\eod_contabo_ed25519
Repository:    /srv/eod/repository
Secrets:       /srv/eod/secrets/preview.env
Imports:       /srv/eod/imports
Backups:       /srv/eod/backups
Preview URL:   http://127.0.0.1:8765
Health URL:    http://127.0.0.1:8765/_health/
```

Разработка, commit и исправление файлов непосредственно на VPS запрещены. VPS является
read-only checkout для сборки и проверки принятого GitHub-кода.

## 2. Вход на VPS

Из Windows PowerShell:

```powershell
ssh `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  eodadmin@5.181.177.72
```

Команды этого runbook не содержат `exit`, поэтому не должны завершать интерактивную SSH-сессию.

## 3. Синхронизация checkout

До merge INFRA-002:

```bash
cd /srv/eod/repository
git fetch --prune origin
git switch infra/002-container-preview
git pull --ff-only
git status --short --branch
```

После принятия и merge:

```bash
cd /srv/eod/repository
git fetch --prune origin
git switch main
git pull --ff-only
git status --short --branch
```

Ожидается чистое рабочее дерево.

## 4. Secret environment

Файл создаётся один раз:

```bash
sudo install -d -m 700 -o root -g root /srv/eod/secrets
sudo install -m 600 -o root -g root /dev/null /srv/eod/secrets/preview.env
sudo micro /srv/eod/secrets/preview.env
```

Структура берётся из `deploy/preview.env.example`. Реальные значения не коммитятся и не
копируются в логи.

Генерация случайных значений:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

## 5. Проверка Compose

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  config --quiet
```

## 6. Сборка и запуск

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  up --detach --build
```

Первичный запуск выполняет:

1. `manage.py check`;
2. миграции;
3. сборку staticfiles;
4. запуск Gunicorn.

## 7. Статус и health-check

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  ps

curl --fail --silent --show-error http://127.0.0.1:8765/_health/
```

Ожидается:

```json
{"status": "ok"}
```

Логи:

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f /srv/eod/repository/compose.preview.yaml \
  logs --tail 250 --no-color app db
```

## 8. Доступ с Windows через SSH-туннель

В отдельном окне PowerShell:

```powershell
ssh `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  -N `
  -o ExitOnForwardFailure=yes `
  -o ServerAliveInterval=30 `
  -L 8765:127.0.0.1:8765 `
  eodadmin@5.181.177.72
```

Окно остаётся занятым до ручной остановки туннеля через `Ctrl+C`.

Открыть:

```text
http://127.0.0.1:8765
```

Демонстрационные учётные записи:

```text
operator.demo   / EodDemo!2026
supervisor.demo / EodDemo!2026
```

## 9. Перезапуск только приложения

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  restart app
```

Перезапуск PostgreSQL для обычного обновления интерфейса не требуется.

## 10. Создание полного presentation snapshot на Windows

Перед snapshot остановить локальный сервер ЭОД и не изменять данные до завершения команды.

```powershell
Set-Location "G:\electronic-operational-docs"

powershell.exe `
  -NoProfile `
  -ExecutionPolicy Bypass `
  -File ".\scripts\snapshot_presentation_database.ps1"
```

По умолчанию результат создаётся в `G:\EOD_BACKUPS`:

```text
presentation_YYYYMMDD_HHMMSS\
presentation_YYYYMMDD_HHMMSS.zip
presentation_YYYYMMDD_HHMMSS.zip.sha256.txt
```

Snapshot содержит:

- согласованную физическую копию `presentation.sqlite3`;
- переносимый Django fixture;
- `manifest.json` с количеством записей и SHA-256;
- `media`, если каталог содержит файлы.

Исходная локальная база не изменяется.

## 11. Передача snapshot на VPS

Подставить фактическое имя созданного архива:

```powershell
scp `
  -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
  "G:\EOD_BACKUPS\presentation_YYYYMMDD_HHMMSS.zip" `
  eodadmin@5.181.177.72:/home/eodadmin/
```

## 12. Импорт snapshot в PostgreSQL

На VPS:

```bash
cd /srv/eod/repository
sudo bash scripts/import_presentation_snapshot.sh \
  /home/eodadmin/presentation_YYYYMMDD_HHMMSS.zip
```

Импортёр автоматически:

1. проверяет формат, размеры и SHA-256 архива;
2. останавливает приложение;
3. создаёт PostgreSQL backup в `/srv/eod/backups`;
4. очищает прикладные данные preview;
5. загружает fixture;
6. сверяет все модели с `manifest.json`;
7. проверяет оба demo-логина;
8. запускает приложение и выполняет HTTP health-check;
9. при ошибке пытается автоматически восстановить PostgreSQL backup.

Успешный итог:

```text
All model counts match the snapshot manifest.
Demo authentication: ok
===== PRESENTATION SNAPSHOT IMPORTED =====
```

Служебные `docker compose run` используют `EOD_SKIP_STARTUP_TASKS=1`, поэтому не повторяют
миграции и `collectstatic`.

## 13. Ручной PostgreSQL backup

```bash
cd /srv/eod/repository
sudo install -d -m 750 -o root -g root /srv/eod/backups

set -a
sudo -E bash -c 'source /srv/eod/secrets/preview.env; \
  docker compose --env-file /srv/eod/secrets/preview.env -f compose.preview.yaml \
  exec -T db pg_dump \
  --username "$POSTGRES_USER" \
  --dbname "$POSTGRES_DB" \
  --format custom' \
  > /srv/eod/backups/eod_preview_manual_$(date +%Y%m%d_%H%M%S).dump
set +a
```

Для штатного переноса presentation-базы предпочтителен встроенный импортёр, который создаёт
backup сам.

## 14. Остановка без удаления данных

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  down
```

Named volume PostgreSQL сохраняется.

## 15. Необратимый полный сброс

Команда удаляет preview database volume. Применяется только после отдельного явного решения:

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  down --volumes
```

## 16. Минимальная приёмка после обновления

```text
[ ] app и db имеют статус healthy
[ ] /_health/ возвращает {"status": "ok"}
[ ] приложение доступно только через 127.0.0.1:8765
[ ] PostgreSQL port не опубликован
[ ] supervisor.demo выполняет вход
[ ] открываются оперативный журнал, оборудование, персонал и нормативный реестр
[ ] существующие записи и связи присутствуют
[ ] в логах отсутствуют traceback и HTTP 500
```
