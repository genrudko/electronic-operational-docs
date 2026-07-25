# ЭОД — открытые вопросы и отложенные задачи

## 1. Текущий обязательный этап

### AUTO-000

- принять automation architecture;
- принять security boundaries;
- принять acceptance contract;
- зафиксировать scope AUTO-001 MVP;
- не менять runtime.

### AUTO-001

- проверить сетевой маршрут GitHub-hosted runner → VPS;
- выбрать restricted transport;
- реализовать exact-SHA orchestrator;
- реализовать lock;
- реализовать sanitised evidence;
- выполнить два success и один failure acceptance case;
- не предоставить automatic merge.

После AUTO-001 продолжается PLAN-001.

## 2. PLAN-001

PR #7 остаётся Draft. Нужно определить:

- фактический статус каждого модуля;
- первый journal vertical slice;
- master plan v3.0;
- актуальный smoke/integration suite поверх уже работающих 497 tests;
- реальные blockers продукта.

## 3. Структурированные журналы

Требуют проверки/завершения:

- applications;
- dispositions;
- equipment defects;
- equipment commissioning;
- relay protection and telemechanics;
- work under permits;
- work under dispositions.

Каждый journal получает source-bound form, rules, UI, реальные связи, presentation data, tests and acceptance.

## 4. Operational journal

Открыты:

- caret placement;
- keyboard navigation;
- PgUp/PgDown;
- editable semantic link;
- marker copy/paste duplication;
- page jump;
- templates, abbreviations and context assistance.

## 5. Work permits and dispositions

Открыты:

- paper/hybrid/electronic original;
- target briefings;
- initial/daily admission;
- crew changes;
- transfers;
- suspension/resumption;
- completion/closure/storage;
- evidence and signatures.

Решение после актуального нормативного исследования.

## 6. Switching

Нужен minimum registry and lifecycle. Automatic БП/ТБП/ТПП generation and safety engine remain separate.

## 7. UX-001

Открыты:

- two visual directions;
- target desktop viewport;
- density;
- typography;
- palette;
- radii/shadows;
- shell composition;
- limited runtime prototype;
- accepted tokens.

## 8. Data and imports

- шесть неоднозначных workplace-document rows в staging;
- проверить equipment import completeness;
- сохранить common DC equipment family ЩПТ/ШОТ;
- controlled RU→EN lexicon;
- no sensitive production data.

## 9. Tests and quality

Закрыто QUALITY-001:

```text
test discovery: fixed
full suite: 497/497 OK
command: python manage.py test apps --verbosity 2
```

Открыто:

- structured machine-readable test evidence;
- profile tests для каждого product slice;
- semantic-marker regression;
- automation negative/security tests.

## 10. Infrastructure

- AUTO-001 restricted gateway;
- artifact retention;
- deploy credential rotation/revoke;
- stale-lock recovery;
- backup policy для future automatic migrations;
- reverse proxy/HTTPS/domain не являются текущим blocker;
- production hardening — отдельный официальный этап.

## 11. Documentation continuity

- current state/handoff обновляются в каждом принятом significant change;
- новый application baseline фиксируется после post-merge verification;
- metadata-only follow-up не создаёт рекурсивный baseline;
- automation docs не должны изображать AUTO-001 реализованным до фактической acceptance.
