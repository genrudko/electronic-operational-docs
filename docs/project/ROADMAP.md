# ЭОД — roadmap

## Принцип

Roadmap управляется доказательствами, а не только исторической нумерацией патчей. Каждый этап начинается после проверки текущего baseline и заканчивается технической и пользовательской приёмкой.

## Последние завершённые этапы

### DOCS-001 — Project operating system

**Статус:** принят, squash-merged PR #4, post-merge verified.

**Accepted application baseline:** `e18872face7f27f489056b72fed31e5586121b0c`.

Выходы:

- новое дерево документации;
- актуальные README and AGENTS;
- current state, handoff, master plan, roadmap and domain invariants;
- preview/development runbooks;
- PR template;
- documentation CI gate;
- migration legacy `docs/project_state/`;
- последовательная журнальная стратегия;
- paper-first режим журнала ключей;
- UX-001 parallel workstream.

DOCS-002 зафиксировал accepted baseline и PLAN-001 transition как metadata-only follow-up. DOCS-003 сохранил UX-001 v0.3 как provisional contract.

### QUALITY-001 — PostgreSQL test execution repair

**Статус:** принят, squash-merged PR #8.

```text
current main history HEAD: 4237aadc2cfdee518567024c2b45b653f49c16e7
full PostgreSQL suite: 497/497 OK
test command: python manage.py test apps --verbosity 2
```

Закрыт долг нулевого test discovery. Следующие product slices сохраняют полный suite и добавляют профильные tests/gates.

## Текущий короткий инфраструктурный спринт

### AUTO-000 — Development automation contract

**Тип:** documentation-only.

Выходы:

- automation master plan;
- GitHub/VPS orchestrator contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- синхронизация canonical state после QUALITY-001.

AUTO-000 не меняет runtime, workflows, VPS или secrets.

### AUTO-001 — Development orchestrator MVP

Начинается после принятия AUTO-000.

Минимальный infrastructure vertical slice:

```text
trusted PR trigger
→ green current-head CI
→ exact-SHA development deployment
→ explicit refresh/rebuild
→ check
→ test apps
→ status
→ evidence in GitHub
```

Gate завершения:

- два успешных deployment;
- один negative/failure case;
- exact-SHA proof;
- preview isolation proof;
- штатный цикл без ручных VPS-команд пользователя;
- automatic merge отсутствует.

После AUTO-001 MVP продуктовая работа возвращается к PLAN-001. AUTO-002+ не являются блокерами.

## Текущая продуктовая фаза

### PLAN-001 — ревизия фактической реализации

PR #7 остаётся Draft и продолжается после AUTO-001 MVP.

Цель: установить, что сделано, не сделано, сделано частично или иначе, чем планировалось.

Обязательная матрица по каждому модулю:

| Область | Проверяется |
|---|---|
| Требования | исходный master plan и предметные решения |
| Данные | models, migrations, fixtures and importers |
| Backend | services, constraints, transitions and audit |
| UI | реальные пользовательские маршруты |
| Тесты | unit, integration, gates and CI |
| Demo | presentation data and end-to-end scenarios |
| Приёмка | подтверждённые видео/логи и открытые дефекты |

PLAN-001 обязан определить минимальный обязательный smoke/integration suite поверх действующего полного PostgreSQL test baseline.

Выход:

- master plan v3.0;
- подтверждённый ближайший журнальный vertical slice;
- реалистичная последовательность следующих работ;
- обновлённые acceptance criteria;
- список технического долга, который действительно блокирует продуктовую разработку.

## Параллельная UX-фаза

### UX-001 — UI design system and interaction contract

**Текущий статус:** provisional project contract; visual acceptance pending; implementation authorization not granted.

UX-001 v0.3 подготовил:

- evidence-based UI audit;
- runtime video evidence audit;
- самостоятельное visual direction;
- UI principles;
- candidate design tokens;
- component contract;
- interaction/keyboard/focus/overlay contract;
- page archetypes;
- three textual reference-screen contracts;
- staged implementation roadmap.

Пакет сохраняется в `docs/ux/UX-001_v0.3/`, а каноническая граница статуса — в `docs/ux/README.md`.

### Следующий visual gate

```text
два компактных визуальных направления
на application shell + один structured-journal screen
→ решение пользователя
→ ограниченный runtime prototype
→ визуальная корректировка и acceptance
→ accepted tokens
```

До этого не являются стандартом concrete palette, typography scale, density, radii, shadows, shell composition и внешний вид reference screens. Массовое внедрение по всем routes не разрешено.

UX-001 не блокирует PLAN-001. UI/UX-решения проверяются на реальном выбранном journal slice и operational journal, а интеграционные и доменные решения остаются в основном чате.

## Принцип продуктовой очереди после PLAN-001

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Полноценная cross-document timeline строится после накопления подтверждённых типов отношений, но минимальные связи с оперативным журналом, оборудованием, участниками и основанием появляются в каждом vertical slice.

## Предварительные продуктовые фазы

Порядок ниже является гипотезой до завершения PLAN-001.

### PRODUCT-A1 — Defect journal vertical slice

Предварительный первый кандидат:

- source-bound форма дефекта;
- оборудование;
- инициатор и ответственный;
- статусы и история;
- связь с оперативной записью;
- presentation data;
- automated gates;
- пользовательская приёмка.

UX-001 использует defect family как reference contract, но это не является окончательным выбором продукта.

### PRODUCT-A2 — Application journal vertical slice

- заявка и её основание;
- оборудование, сроки и участники;
- минимальные статусы;
- связь с дефектом и оперативным журналом;
- acceptance scenario.

### PRODUCT-A3 — Disposition journal vertical slice

- распоряжение;
- issuer/recipient/content;
- минимальные переходы;
- связь `заявка → распоряжение`;
- связь с оперативным журналом;
- acceptance scenario.

### PRODUCT-A4+ — Remaining structured journals

Очередность уточняется PLAN-001:

- журнал ввода оборудования;
- журнал РЗА и телемеханики;
- журнал работ по нарядам;
- журнал работ по распоряжениям;
- иные source-bound журналы.

Журнал выдачи и возврата ключей не входит в обязательный электронный lifecycle. Основной режим — paper-first; электронный справочный/контрольный контур рассматривается отдельно.

### PRODUCT-B — Work permit and switching minimum slice

- базовый реестр нарядов и распоряжений;
- участники и роли;
- работа, место, оборудование и меры безопасности;
- минимальные статусы и переходы;
- paper/hybrid/electronic mode оригинала;
- минимальный реестр документов переключений;
- связи с заявками, распоряжениями и оперативным журналом.

### PRODUCT-C — Operational journal assistance and stabilization

- шаблоны;
- параметры;
- словарь сокращений;
- оборудование, сотрудники и документы в подсказках;
- клавиатурная работа;
- стабильность редактора и семантических ссылок;
- устранение marker duplication;
- stable focus/overlay/drawer geometry.

Blocking editor repairs не откладываются автоматически до полного редизайна.

### RELEASE-A — Internal prototype

- 6–8 сквозных сценариев;
- presentation reset;
- regression checklist;
- блокирующие дефекты устранены;
- демонстрационный маршрут от начала до сдачи смены;
- paper-first ограничения журнала ключей отражены честно.

### PRODUCT-D — Cross-document lifecycle

- заявка → распоряжение → работа;
- дефект → оборудование → работа;
- наряд → допуски → окончание → закрытие;
- переключение → заявка → распоряжение → запись;
- единая timeline.

### PRODUCT-E — Electronic work permit lifecycle

Только после нормативного исследования:

- целевые инструктажи;
- первичный и ежедневный допуск;
- изменения бригады;
- переводы;
- приостановка и возобновление;
- полное окончание и закрытие;
- подписи и доказательства действий;
- хранение и архив.

### RELEASE-B — Full demonstration

- роли и полномочия;
- полный аудит;
- печатные формы и экспорт;
- руководство пользователя и администратора;
- программа и методика испытаний;
- итоговая функциональная приёмка.

## Automation после MVP

Только по подтверждённой необходимости:

- AUTO-002 change classification;
- AUTO-003 structured evidence;
- AUTO-004 Playwright browser acceptance;
- visual regression после принятия design tokens;
- automatic development DB reset;
- trusted preview deployment.

## Дальняя очередь

Только после отдельного решения предприятия:

- AD/LDAP;
- кадровые системы и СЭД;
- юридически значимая электронная подпись;
- криптопровайдер и сертификаты;
- read-only SCADA/CIM integrations;
- mobile offline mode;
- отказоустойчивость, репликация и промышленный ввод;
- отмена бумажного дублирования.

## Правила изменения roadmap

- новый этап не добавляется только потому, что он звучит полезно;
- изменение направления оформляется записью в `DECISION_LOG.md`;
- статус `готово` требует Definition of Done and acceptance evidence;
- provisional UX contract не считается visual acceptance;
- частично реализованная функция не считается завершённым этапом;
- infrastructure tasks могут закрывать части поздних этапов досрочно;
- применимые canonical docs обновляются вместе с каждым принятым изменением.
