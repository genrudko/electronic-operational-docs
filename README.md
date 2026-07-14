# Электронная оперативная документация

Независимый демонстрационный прототип модульной системы для оперативного персонала.

## Локальный запуск без Docker

```powershell
Set-Location "G:\electronic-operational-docs"
.\scripts\run_dev.ps1
```

Скрипт автоматически выбирает свободный локальный порт и выводит точные адреса:

```text
Главная страница: http://127.0.0.1:<порт>/
Проверка состояния: http://127.0.0.1:<порт>/health/
```

При необходимости порт можно задать явно:

```powershell
.\scripts\run_dev.ps1 -Port 8765
```

Проверить только выбор свободного порта, не запуская Django:

```powershell
.\scripts\run_dev.ps1 -CheckOnly
```

## Ручные проверки

```powershell
$env:DB_ENGINE = "sqlite"
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test
.\.venv\Scripts\python.exe -m ruff check manage.py src scripts
```

## PostgreSQL-профиль

PostgreSQL остаётся целевой базой проекта. При наличии Docker:

```powershell
.\scripts\run_postgres.ps1
```

SQLite используется только для локального интерфейсного прототипирования. До реализации
конкурентной нумерации, неизменяемых документов, подписей и промышленного пилота все
критические gate-проверки должны выполняться на PostgreSQL.

## Ограничение

Прототип не предназначен для производственной эксплуатации и не заменяет официальную документацию.

## Git

Private repository:

```text
genrudko/electronic-operational-docs
```

Every successful patch is finalized through:

```powershell
.\.venv\Scripts\python.exe scripts\git_finalize_patch.py `
  --root "G:\electronic-operational-docs" `
  --patch-id "patch_xxx" `
  --message "Describe the change"
```

See `docs/GIT_WORKFLOW.md`.
