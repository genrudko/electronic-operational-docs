# Электронная оперативная документация

Независимый демонстрационный прототип модульной системы для оперативного персонала.

## Локальный запуск без Docker

```powershell
Set-Location "G:\electronic-operational-docs"
.\scripts\run_dev.ps1
```

Скрипт автоматически выбирает свободный локальный порт и выводит точные адреса главной страницы и `/health/`.

## Демонстрационные персональные записи

Вымышленные локальные записи:

```text
operator.demo   / EodDemo!2026
supervisor.demo / EodDemo!2026
```

Они предназначены только для локального прототипа. Каждая учётная запись связана ровно с одним сотрудником.

Повторное заполнение организационного справочника:

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo_organization --reset-passwords
```

## Демонстрационное документарное ядро

Patch 003 добавляет:

- типы документов;
- черновики и версии;
- транзакционную серверную регистрацию;
- нумераторы по организации, типу и году;
- запрет изменения зарегистрированных документов;
- запрет физического удаления документов, версий, связей и аудита;
- типизированные связи документов;
- базовые append-only события аудита.

Повторное заполнение вымышленных документов:

```powershell
.\.venv\Scripts\python.exe manage.py seed_demo_documents
```

## Ручные проверки

```powershell
$env:DB_ENGINE = "sqlite"
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
.\.venv\Scripts\python.exe manage.py migrate --noinput
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe scripts\gate_test_discovery.py
.\.venv\Scripts\python.exe scripts\gate_patch_003.py
.\.venv\Scripts\python.exe -m ruff check manage.py src scripts
```

## PostgreSQL-профиль

PostgreSQL остаётся целевой базой проекта. При наличии Docker:

```powershell
.\scripts\run_postgres.ps1
```

SQLite используется для локального интерфейсного прототипирования и проверки доменных инвариантов.
Полноценная проверка параллельной регистрации и блокировки серверного нумератора выполняется
на PostgreSQL отдельным `TransactionTestCase`.

## Ограничение

Прототип не предназначен для производственной эксплуатации и не заменяет официальную документацию.

## Git

Private repository:

```text
genrudko/electronic-operational-docs
```

Каждый успешный патч завершается через:

```powershell
.\.venv\Scripts\python.exe scripts\git_finalize_patch.py `
  --root "G:\electronic-operational-docs" `
  --patch-id "patch_xxx" `
  --message "Describe the change"
```

См. `docs/GIT_WORKFLOW.md`.
