# ЭОД — текущий handoff

**Обновлено:** 26.07.2026

```text
repository:
genrudko/electronic-operational-docs

accepted application baseline:
main / 937d2cd2b187c17fac3088ccfc52079fc4608306

current main history HEAD:
37a2390a2a45e2abb73e60318d5429ed326efb53

current work:
PLAN-001 narrow classifier repair

branch:
plan/001-evidence-audit

PR:
#7 / OPEN / DRAFT / NOT MERGED
```

## 1. Что уже принято

- AUTO-001A/B accepted and practically verified.
- Trusted controller развёртывает exact PR SHA только в development.
- Preview изолирован.
- PLAN-001 evidence package принят независимо.
- Evidence exact head:
  `fb313f270254720b0f7d7815fffc2cb05d577901`.
- Evidence ZIP SHA-256:
  `58df47f83d1758d2e6aa8b32e1d5a70efb8c453454d8759e25d913e7f031619a`.
- Первый product vertical slice выбран:
  **Журнал дефектов оборудования**.

## 2. Текущая задача

Завершить существующий PR #7 без нового branch/PR:

1. заменить broad keyword readiness на explicit ownership;
2. разделить `absent`, `unknown`, `not applicable`;
3. разделить runtime data provenance;
4. доказать ownership `apps.operational_documents` и `apps.operational_log`;
5. исключить AUTO-001 false positives;
6. различать source catalog, published type и records;
7. встроить manual Chat 0 decision в REPORT;
8. синхронизировать canonical docs;
9. прогнать финальный exact-head gate и один последний evidence run.

Функциональную реализацию Defect Journal пока не начинать.

## 3. Обязательный рабочий процесс

```text
GitHub exact head
→ пять CI
→ label vps-development-refresh
→ trusted AUTO-001B deployment
→ controller status
→ explicit non-root container audit
→ manifest/checksum verification
→ Chat 0 review
→ отдельная команда merge
```

Пользователь не редактирует код, не создаёт commits и не собирает patch-файлы.
VPS не является источником кода.

## 4. Runtime facts

```text
preview:
eod-preview / 127.0.0.1:8765 / eod_preview

development:
eod-development / 127.0.0.1:8766 / eod_development

controller:
usr/local/sbin/eod-development-controller

release root:
srv/eod/automation/releases

state:
srv/eod/automation/state
```

Controller state перед финальным evidence должен показать:

```text
current_sha=<new exact PR head>
transaction=NONE
pending_run_id=NONE
preview=UNTOUCHED
```

## 5. Ручное решение PLAN-001

```text
generic structured-journal core:
SUBSTANTIALLY IMPLEMENTED

structured journals pack:
NOT COMPLETE

operational journal:
ADVANCED BUT LIFECYCLE INCOMPLETE

work permits/orders:
NOT IMPLEMENTED AS VERTICAL SLICE

switching documents:
NOT IMPLEMENTED AS VERTICAL SLICE

repeatable presentation dataset:
BLOCKING GAP

recommended first vertical slice:
DEFECT JOURNAL
```

Automatic audit не подтверждает предметную приёмку самостоятельно.

## 6. Что вернуть в Чат 0 после repair

- новый exact head;
- final diff scope;
- пять CI;
- checksum нового evidence ZIP;
- краткую исправленную FACT MATRIX;
- список обновлённых canonical docs;
- VPS status;
- development/preview health;
- Draft/not merged.

## 7. Что запрещено

- новый branch или PR;
- merge без отдельной команды пользователя;
- product implementation до принятия repair;
- domain models/migrations/UX в repair;
- broad architecture expansion;
- automatic merge;
- preview write;
- реальные enterprise data или secrets.

## 8. Сохранённый процессный контракт

Работа продолжается по модели **GitHub-first/VPS-first**. PLAN-001 —
доказательная ревизия плана и реализации — закрепила правило: **журналы
доводятся по одному** до automated and user acceptance.
