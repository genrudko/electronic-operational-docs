# Codex task — `PROJECT-BASELINE-001` / Stage 1 factual audit

## WORK ITEM

```text
ID: PROJECT-BASELINE-001
ISSUE: #26
BRANCH: docs/project-baseline-001
BASELINE: 50d96842e8700540832210990993e64fc2e3636d
TYPE: DOCUMENTATION / PRODUCT ARCHITECTURE / REPOSITORY HYGIENE
STAGE: 1 — FACTUAL AUDIT ONLY
```

## Роль

Ты выполняешь первый доказательный этап `PROJECT-BASELINE-001` в репозитории `genrudko/electronic-operational-docs`.

Не проектируй новый продукт по памяти. Не объявляй предлагаемый roadmap каноническим. Сначала докажи фактическое состояние репозитория, покрытие источников и существующие пробелы.

## Обязательный preflight

1. Подтверди, что текущая ветка основана на exact baseline:

```text
50d96842e8700540832210990993e64fc2e3636d
```

2. Прочитай полностью:

- `AGENTS.md`;
- `README.md`;
- `docs/INDEX.md`;
- `docs/project/CURRENT_STATE.md`;
- `docs/project/CURRENT_HANDOFF.md`;
- `docs/project/DOMAIN_INVARIANTS.md`;
- `docs/project/PRODUCT_UX_PRINCIPLES.md`;
- `docs/process/PROJECT_OPERATING_SYSTEM.md`;
- `docs/process/DEVELOPMENT_WORKFLOW.md`;
- `docs/process/DEVELOPMENT_ACCELERATION.md`;
- `docs/project/ROADMAP.md`;
- `docs/project/OPEN_ITEMS.md`;
- `docs/project/DECISION_LOG.md`;
- `docs/research/SPECIALIZED_WORKFLOW_BENCHMARK_20260729_v1_2.md`;
- `docs/research/SPECIALIZED_WORKFLOW_NORMATIVE_EVIDENCE_20260729_v1_2.csv`;
- `docs/research/SPECIALIZED_WORKFLOW_PRODUCT_EVIDENCE_20260729_v1_2.csv`;
- `docs/research/VERTICAL_PRODUCTS_RESEARCH_20260729.md`;
- `docs/research/VERTICAL_PRODUCTS_SOURCE_CATALOG_20260729.csv`;
- `docs/research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv`;
- `docs/work-items/active/PROJECT_BASELINE_001_SOURCE_INPUT.md`.

3. Проверь фактические models, migrations, services, URLs/views, templates, static assets, tests, presentation fixtures и management commands. Старые roadmap и handoff не считаются доказательством реализации.

## Источники и статусы

Строго различай:

- `FACT` — доказано кодом или canonical source;
- `USER-ACCEPTED-DOMAIN-DECISION` — принято владельцем продукта;
- `EXTERNAL-EVIDENCE` — подтверждено внешним источником;
- `INFERENCE` — аналитический вывод;
- `VERIFY` — данных недостаточно;
- `CONFLICT` — источники или код расходятся.

Референсный перечень оперативной документации является coverage-source, а не обязательной конфигурацией одного объекта и не нормативным доказательством электронной формы.

## Обязательный метод

```text
FACT
→ COVERAGE MATRICES
→ CONFLICTS / GAPS
→ OPEN DECISIONS
→ PROPOSED MODULE MAP
→ PROPOSED DEMO / POST-DEMO DEPTH
```

На этом этапе не переходи к `FINAL BASELINE`.

## Задача 1 — documentation inventory

Построй inventory всей документации репозитория и классифицируй каждый значимый файл:

```text
CANONICAL
CURRENT-DYNAMIC
EVIDENCE
WORK-ITEM
HISTORICAL
SUPERSEDED-CANDIDATE
DUPLICATE/CONFLICT
```

Отдельно выяви:

- дублирование текущего SHA и активного статуса;
- устаревшие baseline/head SHA;
- конкурирующие roadmap/module map/open items;
- документы, которые нельзя удалять, но нужно архивировать;
- проверки, завязанные на устаревшие текстовые маркеры.

## Задача 2 — current code coverage

Инвентаризируй фактически существующие продуктовые и инфраструктурные контуры.

Для каждой capability укажи:

- module/capability ID;
- models;
- migrations;
- services;
- routes/views;
- templates/static;
- tests;
- presentation/demo data;
- runtime evidence, если оно находится в canonical docs;
- фактический статус:
  - `IMPLEMENTED-ACCEPTED`;
  - `IMPLEMENTED-PARTIAL`;
  - `FOUNDATION-ONLY`;
  - `PRESENTATION-ONLY`;
  - `PLANNED-ONLY`;
  - `ABSENT`;
  - `VERIFY`.

Не считать generic structured core готовым предметным журналом без доказанного lifecycle и пользовательского workflow.

## Задача 3 — reference documentation coverage

На основе source input и доступных repository evidence подготовь реестр классов оперативной документации.

Каждая строка должна иметь:

- reference ID;
- исходный класс документа;
- нормализованный класс;
- functional contour;
- candidate module;
- source locator;
- нормативный статус;
- текущий code coverage;
- proposed Demo-depth;
- gap/open decision.

Если точная построчная транскрипция исходного перечня отсутствует в репозитории, не выдумывай её. Отметь это как `SOURCE-IMPORT-REQUIRED` и используй только подтверждённые source-input классы.

## Задача 4 — process coverage

Проверь как минимум следующие процессы:

- начало смены;
- ведение и регистрация записи ОЖ;
- оперативные переговоры;
- дефект оборудования;
- заявка;
- журнал распоряжений;
- наряд-допуск;
- журнал работ по нарядам;
- работа и журнал по распоряжению;
- работы в порядке текущей эксплуатации;
- установка и снятие заземлений;
- ручной документальный контур переключений;
- осмотр/обход;
- ввод оборудования в работу;
- РЗА/ТМ;
- токи КЗ выключателей;
- осмотр аккумуляторной батареи;
- документация рабочего места;
- схемы как документы;
- передача смены;
- dashboard/reporting;
- междокументные связи.

Для каждого процесса укажи primary facts, derived views, роли, документы, связи и отсутствующие контракты.

## Задача 5 — personnel authority coverage

Проверь фактическое состояние:

- организаций и подразделений;
- должностей и персонала;
- смен;
- квалификаций и групп;
- предметных прав;
- срока и области действия права;
- подрядных/командированных работников;
- проверки полномочия на момент действия;
- snapshot права в историческом документе;
- связи с ПЭП и аудитом.

Не смешивай application role и предметное оперативное право.

## Задача 6 — competitor/evidence reconciliation

Используя только repository research:

- сопоставь принятые решения D-01…D-16 с candidate modules;
- выдели ADOPT/ADAPT/REJECT/DEFER/VERIFY;
- не превращай vendor claims в requirements;
- перечисли модули, которым перед implementation нужен точечный benchmark 2–4 источников;
- не запускай новый широкий web research.

## Задача 7 — legal-mode gaps

Не проводи новое юридическое исследование и не делай юридических заключений.

Составь gap matrix для режимов:

```text
ELECTRONIC-ORIGINAL
HYBRID
PAPER-WITH-ELECTRONIC-MIRROR
REFERENCE-ONLY
POST-DEMO
VERIFY
```

Обязательно сохрани принятые решения:

- нормативная модель и ПЭП входят в Demo;
- наряд-допуск гибридный;
- журнал работ по нарядам электронный;
- журнал распоряжений и журнал работ по распоряжениям — бумажный оригинал + электронное дублирование;
- подпись, ознакомление, инструктаж, проверка знаний и подтверждение действия — разные evidence events.

## Обязательные выходные файлы Stage 1

Создай или полностью замени только:

1. `docs/work-items/active/PROJECT_BASELINE_001_AUDIT.md`;
2. `docs/work-items/active/PROJECT_BASELINE_001_DOCUMENTATION_INVENTORY.csv`;
3. `docs/work-items/active/PROJECT_BASELINE_001_CURRENT_CODE_COVERAGE.csv`;
4. `docs/work-items/active/PROJECT_BASELINE_001_REFERENCE_COVERAGE.csv`;
5. `docs/work-items/active/PROJECT_BASELINE_001_PROCESS_COVERAGE.csv`;
6. `docs/work-items/active/PROJECT_BASELINE_001_PERSONNEL_AUTHORITY_GAPS.csv`;
7. `docs/work-items/active/PROJECT_BASELINE_001_COMPETITOR_RECONCILIATION.csv`;
8. `docs/work-items/active/PROJECT_BASELINE_001_LEGAL_MODE_GAPS.csv`.

## Формат `PROJECT_BASELINE_001_AUDIT.md`

Строго:

```text
# FACT

# COVERAGE SUMMARY

# DOCUMENTATION CONFLICTS

# CODE COVERAGE GAPS

# SOURCE GAPS

# OPEN DECISIONS

# PROPOSED MODULE MAP

# PROPOSED DEMO / POST-DEMO DEPTH

# STOP CONDITIONS / BLOCKERS

# RECOMMENDED STAGE 2 INPUT

# VERDICT
```

Допустимые verdict:

```text
READY FOR CHAT 0 DECISION REVIEW
BLOCKED — SOURCE IMPORT REQUIRED
BLOCKED — FACTUAL AUDIT INCOMPLETE
```

## Allowed files

Stage 1 может изменять только:

```text
docs/work-items/active/PROJECT_BASELINE_001_*.md
docs/work-items/active/PROJECT_BASELINE_001_*.csv
```

Исходный `PROJECT_BASELINE_001_SOURCE_INPUT.md` не переписывать.

## Protected files

Не изменять:

- application code;
- models/migrations/services/routes;
- templates/static/tests;
- workflows, Compose, scripts и infrastructure;
- canonical project/product/UX documents;
- research evidence;
- preview/runtime/data.

## Проверки

Выполни:

```text
git diff --check
python scripts/check_documentation_contract.py
```

Если documentation contract падает из-за того, что Stage 1 файлы ещё не включены в canonical index, зафиксируй точную причину, но не меняй checker на этом этапе.

## Commit

Один commit:

```text
PROJECT-BASELINE-001: complete factual coverage audit
```

Не создавать новый issue, branch или PR. Не выполнять merge. Не переводить Draft PR в Ready for Review.

## Итоговый отчёт

```text
BASELINE
BRANCH
FILES READ
FILES CREATED
FACT SUMMARY
CONFLICTS
GAPS
OPEN DECISIONS
CHECKS
COMMIT SHA
VERDICT
```
