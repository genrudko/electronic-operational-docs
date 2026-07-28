# CHAT 0 — CURRENT HANDOFF

**Проект:** Электронная оперативная документация (ЭОД)  
**Репозиторий:** `genrudko/electronic-operational-docs`  
**Дата handoff:** 28.07.2026  
**Назначение:** восстановление основного интеграционного контекста и передача нового work item в отдельный implementation-чат.

---

## 1. Роли чатов

Основной интеграционный чат отвечает за:

- архитектурные и процессные решения;
- baseline и accepted state;
- выбор нового work item;
- итоговую пользовательскую приёмку;
- отдельное разрешение на merge.

Implementation-чат отвечает за фактическую разработку одного work item, профильные проверки, быстрые development refresh и обработку пользовательских замечаний.

```text
work item = одна ветка + один PR
implementation chat = рабочая сессия
```

UX-FOUNDATION-001 должен выполняться в отдельном implementation-чате. Финальное решение о приёмке и merge возвращается в Chat 0.

---

## 2. Непереговорные правила

- GitHub — единственный источник кода и canonical documentation.
- VPS — runtime/test-контур, а не источник кода.
- Пользователь не редактирует код и не выполняет штатные VPS-команды для функциональных PR.
- Preview не используется для разработки и не изменяется без отдельного решения.
- Automatic merge запрещён.
- Merge выполняется только после отдельной явной команды пользователя.
- End-user UI — русский.
- Internals используют профессиональный technical English.
- Реальные персональные, производственные оперативные данные и enterprise secrets в Git не помещаются.
- Проект является независимым прототипом, а не официальной системой работодателя.

### Минимально достаточное решение

Всегда выбирается наименьшее решение, которое достигает текущей цели и покрывает доказанные риски.

Во время серии визуальных замечаний:

```text
micro-repair
→ focused/profile checks
→ trusted hot refresh
→ пользовательская проверка
```

Полный PostgreSQL suite, пять exact-head workflows и полноценный trusted deployment не запускаются после каждого малого изменения. Один полный final gate выполняется на окончательном head перед merge.

---

## 3. Фактический baseline

Текущий `main` после завершения DEV-FAST-001 repair:

```text
6959b9767ce411e74fc4788d5da8dac97f41018f
Merge PR #21: DEV-FAST-001 container overlay repair
```

Последний принятый продуктовый vertical slice:

```text
DEFECT-001 / PR #16 / MERGED / ACCEPTED
source head:
79f3db7e5c47e1ac8ab2568028d06e4043c2c70e
merge commit:
883a108c8be2a8cd075846fdd175916917911ef6
```

Accepted application baseline, используемый в проектной документации:

```text
937d2cd2b187c17fac3088ccfc52079fc4608306
```

На момент handoff открытых PR нет.

---

## 4. DEFECT-001 — reference product slice

Журнал дефектов принят предметно и функционально.

Реализовано:

- source-bound форма по И-00-007-ОР-2025, версия 2, раздел 11, приложение 8;
- published type `journal-equipment-defects`;
- dedicated registry, card, actions and print;
- обязательная связь с оборудованием и snapshot диспетчерского наименования;
- lifecycle `REGISTERED → IN_PROGRESS → RESOLVED → CLOSED`;
- отдельное versioned продление срока;
- immutable action evidence;
- explicit immutable operational-log link;
- deterministic presentation dataset;
- desktop/mobile representation;
- открытие карточки кликом по неинтерактивной части строки без перехвата ссылок, кнопок, полей и выделения текста.

Текущий визуальный стиль DEFECT-001 является legacy-интерфейсом и не считается принятым целевым UX/UI.

---

## 5. DEV-FAST-001 — завершён

GitHub issue:

```text
#18 — DEV-FAST-001: Trusted hot refresh from PR comment
CLOSED / COMPLETED
```

Основная реализация:

```text
PR #19 / MERGED
source head:
70b1f2ad4c4889714412d2f3cffd48e6b8b968ec
merge commit:
8684fb6f64485171fc2b3ff828d955b32a2104fc
```

Container-copy repair:

```text
PR #21 / MERGED
final source head:
302cc560f846788f40630bf9782b0fc60a98f349
merge commit / current main:
6959b9767ce411e74fc4788d5da8dac97f41018f
```

Runtime activation выполнена однократно заменой только:

```text
/usr/local/sbin/eod-development-controller
```

Canary:

```text
PR #20 / CLOSED / NOT MERGED
head:
bbdcf32a143623ff1cfa226eef89567bd36f32eb
```

Доказано:

- presentation-only file из `src/static/**` появился в development без image build;
- повторный exact PR/SHA run завершился штатно;
- development health-check успешен;
- PostgreSQL и migrations не затронуты;
- preview `UNTOUCHED`;
- automatic merge отсутствует;
- тестовый PR закрыт без merge.

Первое падение последнего canary-run было сетевым timeout SSH от GitHub Actions к VPS. Повтор только упавшего job прошёл успешно; controller в первом запуске не выполнялся.

### Рабочий контракт hot refresh

Разрешены только added/modified regular `100644` blobs:

```text
src/templates/**
src/static/**
```

Запрещены deletions, renames, symlinks, executable blobs, models, migrations, settings, urls, services, dependencies, Dockerfile, Compose, database operations, presentation reset, preview и automatic merge.

После локального presentation repair implementation-чат самостоятельно:

1. проверяет diff и профильные тесты;
2. публикует `/eod-hot-refresh <exact-head-sha>` в активном PR;
3. отслеживает короткий workflow;
4. возвращает пользователю адрес проверки;
5. при ошибке самостоятельно извлекает диагностику и исправляет причину без штатных VPS-команд пользователя.

---

## 6. Development access

Host-local convenience commands:

```text
sudo dev-on
sudo dev-off
sudo dev-status
```

Development URL reference screen:

```text
http://5.181.177.72:8766/operations/defects/
```

Публичный HTTP на `8766` не является production-доступом и включается пользователем только на время проверки.

---

## 7. Утверждённое визуальное направление

Пользователь выбрал **Direction A — спокойное светлое документно-операционное направление**.

Целевые свойства:

- светлая нейтральная основа;
- спокойный синий акцент без SCADA-эффекта;
- высокая рабочая плотность без ощущения admin-panel;
- компактная шапка;
- постоянная понятная навигация;
- полноценный табличный реестр на desktop;
- отдельная рабочая карточка с блоком связей и файлов;
- аккуратная status/action hierarchy;
- меньше декоративных бабблов и технических формулировок;
- читаемое адаптивное представление на мобильных устройствах.

Концепт не копируется буквально. Реальные поля, названия, роли, lifecycle, ссылки и предметные правила берутся из принятого DEFECT-001.

---

## 8. Следующий work item — UX-FOUNDATION-001

Статус на момент handoff:

```text
issue: NOT CREATED
branch: NOT CREATED
PR: NONE
implementation: NOT STARTED
```

Цель — создать минимальный переиспользуемый UI-layer перед следующим журналом, используя DEFECT-001 как reference screen.

Первый scope:

- application shell и навигация;
- compact page header;
- desktop registry/table pattern;
- mobile list/card pattern;
- поиск, фильтры и сортировка;
- карточка записи и формы;
- date/time controls;
- statuses и action hierarchy;
- validation/notification patterns;
- typography, spacing, density и CSS tokens.

Это не полная брендовая переработка всего приложения и не новый product vertical slice.

### Обязательные замечания к журналу дефектов

- центрировать заголовки таблицы;
- уменьшить занимаемое шапкой и служебными блоками пространство;
- сделать карточки менее техническими;
- добавить сквозную пользовательскую нумерацию строк;
- сделать связь с оперативным журналом понятной оператору;
- добавить настраиваемую сортировку и нормальные фильтры;
- улучшить date/time controls;
- сделать статусы визуально явными;
- обеспечить полноценную мобильную читаемость.

### Граница реализации

- предметная модель, lifecycle и evidence DEFECT-001 не меняются без доказанного UX-блокера;
- модели, migrations и services не добавляются только ради визуального слоя;
- существующий PR/branch сохраняется на весь цикл замечаний;
- промежуточные template/static repairs доставляются через DEV-FAST-001;
- один full final gate выполняется после завершения пользовательских замечаний;
- merge разрешается только отдельной командой в Chat 0.

---

## 9. После UX-FOUNDATION-001

Следующий product vertical slice:

```text
PRODUCT-D2 — Журнал заявок
```

Затем:

```text
PRODUCT-D3 — Журнал распоряжений
→ Operational Journal lifecycle
→ другие source-bound journals
```

Каждый следующий журнал должен переиспользовать общие UX-компоненты, а не копировать legacy UI.

---

## 10. Старт отдельного implementation-чата

Новый чат должен начать работу строго по:

```text
docs/project/UX_FOUNDATION_001_NEW_CHAT_STARTER.md
```

До проверки фактических шаблонов, static assets, routes и tests не делать предположений о структуре реализации.

Первый практический результат нового чата:

```text
FACT
IMPLEMENTATION CONTRACT
FIRST DELIVERY SLICE
READY TO IMPLEMENT / BLOCKED
```

Результат должен быть коротким и предметным, без большого повторного аудита уже принятых DEFECT-001 и DEV-FAST-001.
