# ЭОД — запуск закрытого preview на VPS

Preview доступен только через loopback VPS и SSH-туннель. Публичные порты приложения и базы
не открываются.

## 1. Синхронизация read-only checkout

```bash
cd /srv/eod/repository
git fetch --prune origin
git switch infra/002-container-preview
git pull --ff-only
git status --short --branch
```

Разработка и commit на VPS запрещены.

## 2. Создание файла секретов

Сгенерировать значения:

```bash
python3 -c "import secrets; print(secrets.token_urlsafe(64))"
python3 -c "import secrets; print(secrets.token_urlsafe(48))"
```

Создать файл:

```bash
sudo install -m 600 -o root -g root /dev/null /srv/eod/secrets/preview.env
sudo micro /srv/eod/secrets/preview.env
```

Содержимое формируется по `deploy/preview.env.example`. Реальные значения не копируются в чат,
логи, GitHub или репозиторий.

## 3. Проверка конфигурации

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  config --quiet
```

## 4. Сборка и запуск

```bash
cd /srv/eod/repository
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f compose.preview.yaml \
  up --detach --build
```

## 5. Диагностика

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f /srv/eod/repository/compose.preview.yaml \
  ps

curl --fail --silent --show-error http://127.0.0.1:8765/_health/

sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f /srv/eod/repository/compose.preview.yaml \
  logs --tail 200 --no-color
```

Ожидаемый health response:

```json
{"status": "ok"}
```

## 6. Доступ с Windows

В отдельном окне PowerShell:

```powershell
ssh -i "C:\Users\Gennadiy\.ssh\eod_contabo_ed25519" `
    -L 8765:127.0.0.1:8765 `
    eodadmin@<VPS_IP>
```

После установления SSH-соединения открыть:

```text
http://127.0.0.1:8765
```

## 7. Остановка без удаления данных

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f /srv/eod/repository/compose.preview.yaml \
  down
```

## 8. Полный сброс preview-базы

Команда ниже необратимо удаляет preview database volume и используется только после отдельного
решения:

```bash
sudo docker compose \
  --env-file /srv/eod/secrets/preview.env \
  -f /srv/eod/repository/compose.preview.yaml \
  down --volumes
```
