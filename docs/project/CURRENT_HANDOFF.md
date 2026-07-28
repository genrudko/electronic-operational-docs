# CHAT 0 — CURRENT HANDOFF

**Проект:** Электронная оперативная документация (ЭОД)  
**Репозиторий:** `genrudko/electronic-operational-docs`  
**Дата handoff:** 28.07.2026  
**Назначение:** восстановление основного интеграционного контекста без опоры на память чата.

---

## 1. Роль основного интеграционного чата

Основной чат отвечает за:

- архитектурные и процессные решения;
- проверку фактического состояния GitHub;
- baseline и accepted state;
- выбор и запуск новых work item;
- анализ межмодульных и инфраструктурных рисков;
- итоговую пользовательскую приёмку;
- отдельное разрешение на merge.

Implementation chats являются расходуемыми рабочими сессиями. Один work item может продолжаться в нескольких чатах, но сохраняет одну ветку и один PR.

```text
work item = одна ветка + один PR
implementation chat = рабочая сессия
```

---

## 2. Непереговорные правила

- GitHub — единственный источник кода и canonical documentation.
- VPS — единственный runtime/test-контур.
- Локальный репозиторий пользователя не используется как источник истины.
- Пользователь не редактирует код и не выполняет штатные VPS-команды для функциональных PR.
- Пользователь выполняет предметную, функциональную и визуальную приёмку.
- Preview не используется для разработки и не изменяется без отдельного решения.
- Automatic merge запрещён.
- Merge выполняется только после отдельной явной команды пользователя.
- End-user UI — русский.
- Internals используют профессиональный technical English.
- Реальные персональные, производственные оперативные данные и enterprise secrets в Git не помещаются.
- Проект является независимым прототипом, а не официальной системой работодателя.

---

## 3. Принцип минимально достаточного решения

Всегда выбирается наименьшее решение, которое достигает текущей цели и покрывает доказанные риски.

Не создавать большой work item, архитектуру, инфраструктурный контур или release cycle, когда достаточно локального обратимого изменения.

Сложность должна быть оправдана конкретным требованием, угрозой или ограничением. Лишняя работа сама является риском: увеличивает время, поверхность ошибок, стоимость проверки и блокирует пользователя.

### Acceptance loop

Во время серии пользовательских замечаний:

```text
micro-repair
→ focused/profile checks
→ быстрый development refresh
→ пользовательская проверка
```

Не выполнять после каждого малого изменения:

- полный PostgreSQL suite;
- пять exact-head workflows;
- rebuild;
- полноценный trusted deployment;
- отдельный PR или work item.

Один полный final gate выполняется после подтверждения отсутствия новых замечаний и перед merge.

---

## 4. Фактический baseline

Последний accepted product merge:

```text
DEFECT-001 / PR #16
source head:
79f3db7e5c47e1ac8ab2568028d06e4043c2c70e

merge commit:
883a108c8be2a8cd075846fdd175916917911ef6
```

Документационная синхронизация после merge:

```text
ROADMAP:
015bdc9bd93f76bc55e619eecbebd726c578dd6b

OPEN_ITEMS:
a9f6ebd5cdb383837aadb2dbc6790778d8d81cd6
```

Текущий `main` после записи этого handoff необходимо повторно сверять через GitHub. Accepted product baseline определяется merge commit `883a108c...`, а не устаревшими SHA из старых handoff.

Accepted application baseline, используемый в проектной документации:

```text
937d2cd2b187c17fac3088ccfc52079fc4608306
```

---

## 5. DEFECT-001 — завершён и принят

```text
PR:
#16 / CLOSED / MERGED

five exact-head workflows:
GREEN

full PostgreSQL/Django suite:
SUCCESS

trusted development deployment:
SUCCESS

user acceptance:
CONFIRMED

preview:
UNTOUCHED
```

Принятый scope:

- source-bound журнал дефектов по И-00-007-ОР-2025, версия 2, раздел 11, приложение 8;
- published type `journal-equipment-defects`;
- шесть утверждённых граф в рабочем и печатном представлении;
- dedicated registry/card/actions/print;
- обязательная связь с оборудованием и snapshot диспетчерского наименования;
- роли участников;
- lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
- отдельное versioned продление срока;
- immutable action evidence;
- explicit immutable operational-log link;
- минимальный non-cloning contract томов;
- deterministic presentation dataset;
- desktop/mobile representation;
- клик по неинтерактивной части строки открывает карточку, не перехватывая ссылки, кнопки, поля и выделение текста.

Текущий визуальный стиль является legacy-интерфейсом и не считается принятым целевым UX/UI.

---

## 6. CI diagnostics

Прямо в `main` добавлен узкий механизм сохранения диагностик Django failures:

```text
commit:
14db8089ae3b79d8ef6ae0b3f3293f3724770f48

message:
CI: preserve actionable Django failure diagnostics
```

При падении полного Django suite workflow сохраняет:

- `django-test-failure.txt` — компактные failing test names, traceback и итоговый блок;
- `django-test.log` — полный вывод;
- Step Summary;
- artifact `django-test-diagnostics-<run_id>`.

Правило: до получения точного failing test и traceback причина считается гипотезой, а не установленным фактом.

---

## 7. ACCESS-001 — закрыт без merge

```text
PR:
#17

state:
CLOSED / NOT MERGED / SUPERSEDED

branch:
infra/access-001-public-development-https

preview:
UNTOUCHED
```

Большой nginx/Certbot/HTTPS-контур закрыт, потому что практическая задача доступа была решена более простым host-local механизмом. Ветка сохранена только как история исследования и rollback evidence.

Возвращаться к публичному HTTPS можно только по отдельному явному решению пользователя.

---

## 8. Development access

На VPS установлен host-local convenience mechanism:

```text
sudo dev-on
sudo dev-off
sudo dev-status
```

При включённом режиме development доступен по прежнему адресу порта `8766`; публичный HTTP не является шифрованным production-доступом.

Этот механизм не является source-controlled продуктовым deployment и не должен расширяться без необходимости.

---

## 9. Следующий work item — DEV-FAST-001

GitHub issue:

```text
#18 — Trusted hot refresh from PR comment
```

Статус:

```text
READY TO START
implementation: NOT STARTED
branch: NOT CREATED
PR: NOT CREATED
```

### Цель

```text
чат создаёт presentation-only micro-repair в активном PR
→ выполняет focused checks
→ публикует /eod-hot-refresh <exact-head-sha>
→ trusted workflow проверяет actor / PR / exact SHA / paths
→ restricted controller обновляет development
→ collectstatic / restart / health-check
→ чат возвращает адрес пользовательской проверки
```

Пользователь не выполняет SSH/VPS-команды.

### Разрешённый scope первой версии

```text
src/templates/**
src/static/**
```

### Явно запрещено

```text
models
migrations
settings
urls
services
management commands
dependencies
Dockerfile
Compose
database operations
presentation reset
preview
automatic merge
```

### Security contract

- workflow берётся только из `main`;
- actor имеет write/admin permission;
- PR открыт и находится в том же repository;
- SHA в команде точно совпадает с live PR head;
- controller повторно получает `refs/pull/<number>/head`;
- changed paths проходят allowlist;
- используется существующий restricted SSH gateway;
- overlay применяется только к `eod-development`;
- перед заменой создаётся backup;
- при ошибке выполняется rollback;
- state marker фиксирует overlay SHA;
- preview остаётся untouched;
- full suite не является условием промежуточного hot refresh;
- один полный security/runtime gate выполняется перед merge самого DEV-FAST-001.

DEV-FAST-001 затрагивает trusted security boundary и поэтому требует одного отдельного PR. После принятия механизм используется для быстрых UX/UI repairs.

---

## 10. После DEV-FAST-001

### UX/UI foundation

На основе журнала дефектов создать минимальный общий слой:

- application shell;
- navigation;
- desktop/mobile registry patterns;
- tables, search, filters and sorting;
- cards;
- forms and date/time controls;
- status/action hierarchy;
- validation and notifications;
- typography, spacing, density and CSS tokens.

Это не финальная брендовая полировка всего приложения.

### Следующий product vertical slice

```text
PRODUCT-D2 — Журнал заявок
```

Затем:

```text
PRODUCT-D3 — Журнал распоряжений
→ Operational Journal lifecycle
→ другие source-bound journals
```

---

## 11. Предметные инварианты

- Оперативный журнал остаётся специализированным модулем.
- Остальные рабочие журналы используют общий structured-document core и source-bound формы.
- Оператор не конструирует произвольные формы рабочих журналов.
- ЩПТ и ШОТ относятся к одной technical equipment family; различие сохраняется как исходное обозначение или вариант исполнения.
- Paper/hybrid/electronic modes не объявляются юридически эквивалентными без нормативного основания.
- УКЭП/УНЭП не заявляются без подтверждённой реализации и нормативной модели.
- Наличие модели, route, template или test не означает готовность vertical slice.
- Один журнал доводится до automated и user acceptance, затем начинается следующий.

---

## 12. Правило сохранения контекста

`CURRENT_HANDOFF.md` обновляется:

- после каждого merge;
- при смене приоритета;
- после создания нового active branch/PR;
- после важного архитектурного или процессного решения;
- перед завершением или переносом основного интеграционного чата.

`ROADMAP.md` и `OPEN_ITEMS.md` обновляются при изменении последовательности работ или статуса work item.

GitHub всегда имеет приоритет над текстом handoff при расхождении SHA, PR-state или workflow status.

---

## 13. Starter для implementation-чата DEV-FAST-001

```text
Начинаем DEV-FAST-001 — Trusted hot refresh from PR comment.

Сначала через GitHub проверь фактическое состояние:

1. current main HEAD;
2. issue #18;
3. отсутствие открытых PR;
4. accepted DEFECT-001 merge commit 883a108c8be2a8cd075846fdd175916917911ef6;
5. существующие trusted workflows, restricted SSH gateway и development controller;
6. AGENTS.md и принцип минимально достаточного решения.

До завершения gap analysis не создавай ветку, PR и не меняй VPS.

Первый ответ должен содержать:

FACT
CURRENT TRUST BOUNDARY
MINIMAL DESIGN
FILES TO CHANGE
TEST PLAN
RISKS
VERDICT: READY TO IMPLEMENT или BLOCKED

Ограничения:

- цель только presentation-only hot refresh для src/templates/** и src/static/**;
- не расширять scope на общий deployment redesign, HTTPS, CI optimization или product code;
- не создавать новый gateway, если достаточно расширить существующий restricted controller;
- пользовательские VPS-команды: ZERO;
- preview: UNTOUCHED;
- automatic merge: FORBIDDEN;
- один work item = одна ветка + один Draft PR;
- после gap analysis предложить минимальный branch name и PR contract, но не начинать реализацию без подтверждения пользователя.
```
