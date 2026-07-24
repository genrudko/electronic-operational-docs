# ЭОД — карта модулей

Статусы являются предварительными до PLAN-001. `Готово` означает подтверждённый функциональный слой текущего прототипа, а не промышленную готовность.

| Область | Статус | Что подтверждено | Основной дефицит |
|---|---|---|---|
| Django foundation | Готово | настройки, приложения, migrations, UI foundation | дальнейшая эксплуатационная упаковка |
| Organizations | Готово | организация, история наименований, подразделения, workplaces | ревизия admin/config UX |
| Personnel and authentication | Готово | сотрудники, должности, accounts, roles, substitutions | полный lifecycle временных прав |
| Document core | Готово | drafts, versions, registration, numbering, relations, audit | печатные формы и расширенный архив |
| Integrity confirmation | Готово для прототипа | re-auth, canonical snapshot, SHA-256, VALID/INVALID/LEGACY/MISSING | не является юридической ЭП |
| Normative registry | Готово как ядро | documents, editions, requirements, traceability | наполнение и актуализация исследований |
| Equipment registry | Готово как ядро | sites, hierarchy, types, aliases, dispatch names, snapshots | предметная ревизия полноты импорта |
| Dispatching relations | Готово как ядро | управление, ведение, уровни, субъекты, editions | расширение реальными safe demo cases |
| Imports | Готово для текущих источников | staging, normalization, conflicts, publication | унификация повторных импортов и UX |
| Workplace documentation | Готово как реестр | categories, editions, applicability, review dates | шесть неоднозначных строк staging |
| Operational log | Реализовано, требует отдельной ревизии | chronology, editor, records, links, shift concepts | assistance, keyboard UX, final scenarios |
| Operational documentation core | Готово как механизм | source-bound schemas, records, fields, participants, equipment, transitions, search | профильные формы и rules |
| Applications journal | Частично | ядро и источник формы определены | точные графы, lifecycle, acceptance |
| Dispositions journal | Частично | ядро и источник формы определены | точные графы, transitions, links |
| Defects journal | Частично | ядро и источник формы определены | специализированная карточка, lifecycle, relations and acceptance |
| Equipment commissioning journal | Частично | ядро и источник формы определены | предметные rules и scenario |
| RPA/telemechanics journal | Частично | ядро и источник формы определены | точная форма и domain actions |
| Keys journal | Paper-first / optional electronic aid | бумажный оригинал выбран текущим рабочим режимом | отдельное решение о справочном/контрольном electronic contour; полный lifecycle не обязателен |
| Work by permits/dispositions journal | План | направление определено | разделение нормативных режимов и формы |
| Work permit registry | План/исследование | требования собраны как направление | полный lifecycle и нормативное основание |
| Disposition registry | План/исследование | требования собраны как направление | точная модель выдачи и учёта |
| Switching documents registry | План | минимальный scope определён | модели, UI и links |
| Switching generator/safety engine | Вне текущего vertical slice | отдельная граница признана | топология, rules, interlocks, validation |
| Cross-document timeline | Частично | базовые relations существуют | единый event timeline и UX после реальных journal slices |
| UI design system | В работе / UX-001 | задание и границы workstream зафиксированы | audit, tokens, components, interaction contract, reference screens |
| Automated application tests | Дефицит | Django checks and historical gates существуют | текущая test command обнаруживает 0 tests; нужен smoke/integration suite |
| Print and export | Частично/план | document rendering foundation может существовать | подтверждённые формы и acceptance |
| Presentation data | Готово для текущего baseline | PostgreSQL profile, demo users, reset path | расширение под новые scenarios |
| CI | Готово как pipeline | Linux, Python 3.13, PostgreSQL 18.4, checks and profile gates | нулевое число Django tests не считать regressions evidence |
| Preview VPS | Готово | isolated stable contour on 8765 | formal post-merge runbook |
| Development VPS | Готово | isolated branch contour on 8766 | routine use in all next changes |
| Documentation system | В работе | branch DOCS-001, canonical tree and gate | final acceptance, merge and post-merge baseline update |

## Статусы

- `Готово` — существует подтверждённая реализация и тестовый/приёмочный след.
- `Реализовано, требует ревизии` — код существует, но его соответствие текущей цели нужно проверить.
- `Частично` — есть foundation или часть формы, но vertical slice не принят.
- `План/исследование` — реализация не должна начинаться без уточнения источников.
- `Paper-first / optional electronic aid` — бумажный документ остаётся основным, электронный контур не обязателен и требует отдельного решения.
- `Вне текущего vertical slice` — сознательно отложенная сложная область.

## Правило обновления

При изменении статуса указываются:

1. commit/PR;
2. migrations;
3. профильные tests/gates;
4. presentation data;
5. результат пользовательской приёмки;
6. оставшийся дефицит;
7. применимые canonical docs.
