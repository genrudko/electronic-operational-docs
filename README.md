# Электронная оперативная документация

Независимый демонстрационный прототип модульной системы электронной оперативной документации для оперативного персонала электроэнергетики.

> Проект не является системой предприятия, не заменяет обязательную бумажную документацию и не предназначен для промышленной эксплуатации без отдельного официального решения, проверки нормативного соответствия, информационной безопасности и эксплуатационной готовности.

## Текущее состояние

- принятый baseline: `main / abd6066885b060e3e3d2c39098fcaf640bb70416`;
- стабильный preview: PostgreSQL, `/srv/eod/repository`, `127.0.0.1:8765`;
- изолированный development: PostgreSQL, `/srv/eod/development`, `127.0.0.1:8766`;
- основной рабочий процесс: GitHub-first и VPS-first;
- пользователь не редактирует код и выполняет предметную, функциональную и визуальную приёмку;
- merge в `main` выполняется только после явного разрешения пользователя.

Актуальная сводка: [`docs/project/CURRENT_STATE.md`](docs/project/CURRENT_STATE.md).

## Что уже реализовано

- организация, персонал, учётные записи, роли и замещения;
- документарное ядро, версии, регистрация, нумерация, аудит и контроль целостности;
- нормативный реестр и версионируемая организационная конфигурация;
- реестр энергообъектов, оборудования, диспетчерских наименований, управления и ведения;
- импорт оборудования, персонала, оперативных прав и документации рабочего места;
- специализированный оперативный журнал;
- общее ядро структурированной оперативной документации;
- source-bound каталог форм из утверждённых источников;
- PostgreSQL CI, безопасный preview-контур и отдельный development-контур на VPS.

Точный статус модулей и ограничений приведён в [`docs/project/MODULE_MAP.md`](docs/project/MODULE_MAP.md) и [`docs/acceptance/KNOWN_LIMITATIONS.md`](docs/acceptance/KNOWN_LIMITATIONS.md).

## Архитектура работы

```text
Пользователь: цель, предметная логика, приёмка, разрешение merge
                            ↓
Ассистент: анализ, проектирование, код, тесты, commits и PR
                            ↓
GitHub: ветки, история, CI и контроль изменений
                            ↓
VPS development: PostgreSQL, миграции, проверки и визуальная проверка
                            ↓
main + preview: только после явного принятия
```

Стабильный preview и активный development используют разные checkout, Compose projects, базы, пользователей PostgreSQL, volumes, networks и loopback-порты. PostgreSQL наружу не публикуется.

## Документация

Главный индекс: [`docs/INDEX.md`](docs/INDEX.md).

Основные документы:

- [`docs/project/CURRENT_STATE.md`](docs/project/CURRENT_STATE.md) — что фактически существует сейчас;
- [`docs/project/MASTER_PLAN.md`](docs/project/MASTER_PLAN.md) — утверждённая база плана и границы предстоящего пересмотра;
- [`docs/project/ROADMAP.md`](docs/project/ROADMAP.md) — последовательность ближайших этапов;
- [`docs/project/DOMAIN_INVARIANTS.md`](docs/project/DOMAIN_INVARIANTS.md) — обязательные предметные правила;
- [`docs/process/PROJECT_OPERATING_SYSTEM.md`](docs/process/PROJECT_OPERATING_SYSTEM.md) — единая операционная система разработки;
- [`docs/process/DEVELOPMENT_WORKFLOW.md`](docs/process/DEVELOPMENT_WORKFLOW.md) — GitHub-first/VPS-first цикл;
- [`docs/project/CURRENT_HANDOFF.md`](docs/project/CURRENT_HANDOFF.md) — продолжение работы в новом чате;
- [`AGENTS.md`](AGENTS.md) — обязательный порядок работы AI-разработчика.

## Доступ к контурам

Оба приложения доступны только через SSH tunnel.

```text
preview:     http://127.0.0.1:8765
development: http://127.0.0.1:8766
```

Практические команды:

- [`docs/runbooks/SSH_TUNNEL_ACCESS.md`](docs/runbooks/SSH_TUNNEL_ACCESS.md);
- [`docs/runbooks/DEVELOPMENT_RUNBOOK.md`](docs/runbooks/DEVELOPMENT_RUNBOOK.md);
- [`docs/runbooks/PREVIEW_RUNBOOK.md`](docs/runbooks/PREVIEW_RUNBOOK.md).

Демонстрационные учётные записи:

```text
operator.demo   / EodDemo!2026
supervisor.demo / EodDemo!2026
```

Они предназначены только для безопасного демонстрационного профиля.

## Репозиторий и данные

Репозиторий закрытый: `genrudko/electronic-operational-docs`.

Допускаются код, миграции, тесты, архитектурные решения, технические адреса, пути и runbook. Не допускаются действующие секреты, `.env`, ключи, реальные персональные данные, производственные журналы, рабочие инструкции, резервные копии БД и иные чувствительные материалы.

Политика: [`docs/project/DATA_AND_PRIVACY_POLICY.md`](docs/project/DATA_AND_PRIVACY_POLICY.md).

## Ближайшая работа

После завершения DOCS-001 проводится отдельная ревизия плана разработки:

1. фактически сделано;
2. сделано частично или иначе, чем планировалось;
3. не сделано;
4. утратило актуальность;
5. требует изменения направления.

До этой ревизии исторический план не трактуется как автоматически подтверждённая очередность новых реализаций.