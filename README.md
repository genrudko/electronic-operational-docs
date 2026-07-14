# Электронная оперативная документация

Независимый демонстрационный прототип модульной системы для оперативного персонала.

## Локальный запуск без Docker

```powershell
Set-Location "G:\electronic-operational-docs"
.\scriptsun_dev.ps1
```

Скрипт автоматически выбирает свободный локальный порт и выводит точные адреса главной страницы и `/health/`.

## Демонстрационные персональные записи

Patch 002 создаёт вымышленные локальные записи:

```text
operator.demo   / EodDemo!2026
supervisor.demo / EodDemo!2026
```

Они предназначены только для локального прототипа. Каждая учётная запись связана ровно с одним сотрудником.

Повторное заполнение справочника:

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo_organization --reset-passwords
```

## Ручные проверки

```powershell
$env:DB_ENGINE = "sqlite"
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts\gate_test_discovery.py
.\.venv\Scripts\python.exe scripts\gate_patch_002.py
.\.venv\Scripts\python.exe -m ruff check manage.py src scripts
```

## PostgreSQL-профиль

PostgreSQL остаётся целевой базой проекта. При наличии Docker:

```powershell
.\scriptsun_postgres.ps1
```

SQLite используется только для локального интерфейсного прототипирования. До реализации конкурентной нумерации, неизменяемых документов, подписей и промышленного пилота критические gate-проверки должны выполняться на PostgreSQL.

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
