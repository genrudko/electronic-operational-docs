# ЭОД — active development runbook

## Контракт

```text
checkout: /srv/eod/development
branch: active non-main only
compose project: eod-development
compose file: /srv/eod/development/compose.development.yaml
env: /srv/eod/secrets/development.env
app: 127.0.0.1:8766
database/user: eod_development
```

Подробный инфраструктурный документ INFRA-003: `../../deploy/DEVELOPMENT_RUNBOOK.md`.

## Начало сессии

```bash
cd /srv/eod/development

git status --short --branch
git rev-parse HEAD
sudo bash scripts/development_stack.sh status
```

Branch не должна быть `main`.

## Получение commits из GitHub

```bash
cd /srv/eod/development

git status --short --branch
git fetch --prune origin
git pull --ff-only
```

Рабочее дерево должно быть clean.

## Обычное обновление

```bash
sudo bash scripts/development_stack.sh refresh
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

## Rebuild

Для dependencies, Dockerfile, Compose или startup scripts:

```bash
sudo bash scripts/development_stack.sh rebuild
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

## Migrations

```bash
sudo bash scripts/development_stack.sh migrate
```

Для data-impact change предварительно создать backup или выполнить reset procedure по профильному плану.

## Reset from accepted preview

```bash
cd /srv/eod/development
sudo bash scripts/reset_development_database.sh
```

Скрипт проверяет роли checkout, создаёт development backup, dump preview, восстанавливает только development database, применяет active migrations и проверяет demo authentication.

## Logs

```bash
sudo bash scripts/development_stack.sh logs
```

Live:

```bash
sudo bash scripts/development_stack.sh follow
```

## Shell

```bash
sudo bash scripts/development_stack.sh shell
sudo bash scripts/development_stack.sh django-shell
```

## Остановка

```bash
sudo bash scripts/development_stack.sh stop
```

Preview не должен останавливаться этой командой.

## Проверка isolation

```bash
curl --fail --silent --show-error http://127.0.0.1:8765/_health/
echo
curl --fail --silent --show-error http://127.0.0.1:8766/_health/
echo
sudo ss -ltnp | grep -E '127\.0\.0\.1:(8765|8766)'
```

## Запрещено

- запуск stack из `main`;
- использование preview.env;
- ручное редактирование tracked code на VPS;
- commit/push с VPS;
- общий database volume с preview;
- host-published PostgreSQL;
- принятие результата на неизвестном head.