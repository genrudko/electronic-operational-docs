# `PROJECT-BASELINE-001` — решения Chat 0 для Stage 2

## Статус

```text
CHAT 0 DECISION RECORD
STAGE 1 FACTUAL AUDIT: ACCEPTED AS EVIDENCE
STAGE 1 PROPOSED MODULE MAP: NOT CANONICAL
FINAL BASELINE: NOT YET APPROVED
```

## Exact work-item state

```text
issue: #26
branch: docs/project-baseline-001
Draft PR: #27
accepted main baseline: 50d96842e8700540832210990993e64fc2e3636d
Stage 1 reviewed head: a3b090b7cb1d69444c9b90ef428b26cb54148629
```

Stage 2 выполняется в той же ветке и том же Draft PR. Новый issue, branch или PR не создаются.

## 1. Источник референсного перечня

`docs/work-items/active/PROJECT_BASELINE_001_REFERENCE_SOURCE.csv` является обязательным traceable input Stage 2.

Он содержит 66 строк Референсного перечня оперативной документации. Для каждой строки в canonical coverage matrix должны быть сохранены:

- `reference_id`;
- раздел и номер документа;
- исходное наименование;
- страница/locator;
- отметка текущего электронного хранения;
- периодичность пересмотра;
- нормализованный класс;
- функциональный контур;
- решение Demo/Post-demo;
- нормативный статус;
- work item/capability;
- критерий приёмки либо честный `VERIFY`.

Предварительные поля source-файла (`candidate_module`, `preliminary_demo_position`, `decision_status`) являются исходными гипотезами. Их нельзя копировать в canonical baseline без reconciliation с настоящим решением ниже.

Отметка `+/-` в исходном перечне описывает текущую практику хранения источника и сама по себе не доказывает юридическую допустимость или запрет электронной формы.

## 2. Единая шкала глубины релиза

Canonical plan использует только следующие значения:

```text
DEMO-FUNCTIONAL
DEMO-BOUNDED
DEMO-HYBRID
DEMO-PAPER-MIRROR
DEMO-REFERENCE
POST-DEMO-INDUSTRIAL
VERIFY
EXCLUDED
```

- `DEMO-FUNCTIONAL` — целостный работающий сценарий в честно ограниченной предметной границе.
- `DEMO-BOUNDED` — рабочий контур с ограниченной глубиной, явно отражённой в UI и документации.
- `DEMO-HYBRID` — электронная подготовка/сопровождение при сохранении бумажного оригинала или обязательных бумажных действий.
- `DEMO-PAPER-MIRROR` — бумажный оригинал и явно маркированное электронное дублирование сведений.
- `DEMO-REFERENCE` — управление версией, применимостью, просмотром и связями документации без предметного редактора.
- `POST-DEMO-INDUSTRIAL` — инженерная, интеграционная, offline или промышленная глубина после презентационного релиза.
- `VERIFY` — capability входит в coverage, но точная форма/правовой режим/поля требуют доказательства.

Субъективные проценты готовности запрещены.

## 3. Каноническая модульная карта Demo

### Фундамент

1. `PLATFORM` — идентификация, аудит, вложения, поиск, печать, runtime boundaries.
2. `UX` — единая Direction A, shared shell/components, responsive contract и отдельный `UX-THEME-001`.
3. `NORMATIVE-EVIDENCE` — правовые режимы, ПЭП, идентификация, повторная аутентификация, целостность, evidence events.
4. `MASTER-DATA` — организации, объекты, оборудование, диспетчерская структура и общие справочники.
5. `PERSONNEL-AUTHORITY` — персонал, должности, квалификации, группы, подрядчики, предоставленные права, область/срок, action-time evaluation и immutable snapshot.
6. `WORKPLACE-DOCS` — реестр документации рабочего места, применимость, версии, комплектность, пересмотр, ознакомление.
7. `SCHEMES-DOCUMENTS` — утверждённые и оперативные схемы как версионируемая документация.

### Оперативные процессы

8. `OPJ` — специализированный оперативный журнал; в составе capability оперативных переговоров.
9. `SHIFT` — начало, сдача и приёмка смены как отдельный workflow.
10. `APPLICATION` — оперативные заявки.
11. `OPERATIONAL-ORDERS` — самостоятельный журнал распоряжений, бумажный оригинал + электронное дублирование.
12. `DEFECT` — журнал дефектов оборудования.
13. `GROUNDING` — инвентарь заземлений и операции установки/снятия.
14. `SWITCHING-DOCUMENTS` — ручной документальный контур БП/ТБП/программ переключений.

### Организация работ

15. `WORK-PERMIT` — гибридный наряд-допуск: authoring и сопровождение отдельно от lifecycle бумажного оригинала.
16. `PERMIT-WORK-JOURNAL` — электронный первичный журнал работ по нарядам.
17. `ORDER-WORK-JOURNAL` — бумажный оригинал + электронное дублирование журнала работ по распоряжениям.
18. `CURRENT-OPERATION-WORKS` — график оперативного персонала, перечень ремонтного персонала, конкретная работа и журнал выполнения.

### Осмотры и специализированные журналы

19. `EQUIPMENT-INSPECTIONS` — графики, чек-листы, исполнитель, факт, измерения, отклонения и создание дефекта.
20. `EQUIPMENT-COMMISSIONING` — журнал ввода оборудования в работу.
21. `RZA-TM` — bounded-контур РЗА и телемеханики без выдуманной универсальной status machine.
22. `BREAKER-INTERRUPTIONS` — учёт отключений токов КЗ выключателями и накопленного ресурса.
23. `BATTERY-INSPECTION` — журнал осмотра аккумуляторных батарей.
24. `EMERGENCY-READINESS` — быстрый доступ к действующим аварийным/противопожарным инструкциям, карточкам и применимым редакциям.

### Системная связность

25. `CROSS-DOC` — типизированные междокументные связи, provenance и snapshots.
26. `DASHBOARD-REPORTING` — только производные оперативные представления, без второй базы первичных фактов.
27. `DEMO-DATA` — детерминированные данные, reset и сквозные презентационные сценарии.

## 4. Обязательная глубина по ключевым модулям

### OPJ и SHIFT

В Demo требуется целостный bounded workflow:

- начало смены;
- ведение черновика;
- регистрация неизменяемой записи;
- корректировка/аннулирование через отдельные исторические действия, без переписывания оригинала;
- оперативные переговоры как отдельный тип/связанный факт, а не произвольная строка;
- рапорт передачи смены;
- активные документы, дефекты, заземления и незавершённые действия;
- подтверждения обеих сторон с authority-at-action evidence.

### PERSONNEL-AUTHORITY и NORMATIVE-EVIDENCE

Обязательны:

- application role и предметное оперативное право разделены;
- проверка права, области, срока и замещения в момент действия;
- immutable snapshot использованного права;
- раздельные evidence events: подпись, ознакомление, инструктаж, проверка знаний, подтверждение действия;
- ПЭП не объявляется универсально допустимой без нормативного/локального основания.

### Схемы

`SCHEMES-DOCUMENTS = DEMO-REFERENCE`:

- реестр, тип, объект применения;
- действующая редакция и история;
- утверждение/актуальность;
- просмотр, fullscreen и печать;
- связи с оборудованием и документами.

Редактор, УГО, топология, состояния, межблокировки и интеграция с переключениями — `POST-DEMO-INDUSTRIAL`.

### Переключения

`SWITCHING-DOCUMENTS = DEMO-BOUNDED`, а не полное исключение из Demo:

- обычные и типовые бланки/программы;
- шаблоны, ручные операции, версии;
- замечания, согласование и контроль исправления;
- печать;
- архив использованных документов;
- связи с заявкой, оборудованием и ОЖ.

Автогенерация, topology/interlock validation и инженерный редактор — `POST-DEMO-INDUSTRIAL`.

### Осмотры

`EQUIPMENT-INSPECTIONS = DEMO-BOUNDED`:

- график;
- чек-лист;
- исполнитель;
- факт и измерения;
- отклонение;
- создание/связь дефекта.

Маршрутные точки, GPS, offline/mobile route engine — `POST-DEMO-INDUSTRIAL`.

### Специализированные журналы

`EQUIPMENT-COMMISSIONING`, `RZA-TM`, `BREAKER-INTERRUPTIONS`, `BATTERY-INSPECTION` входят в Demo как `DEMO-BOUNDED`.

Отсутствие точной формы не является основанием исключить модуль. До получения утверждённой формы:

- capability и presentation scenario фиксируются;
- неизвестные реквизиты остаются `VERIFY`;
- универсальные поля и lifecycle не выдумываются;
- implementation work item не стартует без точечного source/benchmark contract.

### Бумажные и гибридные контуры

- `WORK-PERMIT = DEMO-HYBRID`.
- `PERMIT-WORK-JOURNAL = DEMO-FUNCTIONAL`, product target — электронный первичный журнал.
- `OPERATIONAL-ORDERS = DEMO-PAPER-MIRROR`.
- `ORDER-WORK-JOURNAL = DEMO-PAPER-MIRROR`.
- Электронная копия бумажного оригинала всегда явно маркируется как mirror, а не электронный оригинал.

## 5. Product target и доказанный legal mode разделяются

Наличие immutable модели, аудита, ПЭП primitive или принятого UI не доказывает юридический режим.

Для OPJ, DEFECT и иных электронных журналов canonical matrix должна отдельно хранить:

```text
product_target_mode
normative_evidence_status
local_act_status
proven_legal_mode
open_gap
```

Пока доказательство не завершено, `proven_legal_mode = VERIFY`, даже если product target — electronic original.

## 6. Post-demo граница

Обязательно `POST-DEMO-INDUSTRIAL`:

- электронный журнал ключей (`KEYS`), текущая модель paper-first;
- редактор схем и инженерная электрическая модель;
- автоматическая генерация переключений;
- topology/state/interlock engine;
- обязательная SCADA/ОИК-интеграция;
- полноценный offline-first и разрешение конфликтов;
- промышленная HA/репликация;
- внешние корпоративные интеграции без отдельного контракта;
- глубокая инженерная модель РЗА.

## 7. Единственные владельцы динамической истины

Stage 2 должен закрепить:

1. `docs/project/CURRENT_STATE.md` — единственный владелец текущего accepted main SHA, active work item/PR и runtime state.
2. `docs/project/DEMO_RELEASE_PLAN.yaml` — единственный machine-readable владелец release/module/capability/work-item status, depth, dependencies, source IDs и acceptance.
3. Human-readable module map, sequence и master checklist являются проверяемыми представлениями этого YAML, а не независимыми источниками.
4. `CURRENT_HANDOFF.md` становится кратким навигатором и не дублирует volatile SHA/status.
5. `BASELINE_HISTORY.md` хранит историю и не владеет текущим SHA.
6. `ROADMAP.md`, `OPEN_ITEMS.md`, старые root workflow/plan files архивируются либо превращаются в совместимые указатели только после marker/link-consumer audit.

Не удалять исторические ADR, UX evidence и provenance SHA.

## 8. UX/UI

- Direction A — единственная общесистемная visual system.
- Shared shell/components обязательны; отдельные специализированные workspaces допустимы только по предметной функции.
- `UX-THEME-001` — первый общесистемный UX work item после baseline: единые light/dark/system tokens и миграция всех маршрутов.
- Route/reference matrix должна указывать exact reference locator, adopt/adapt/reject и acceptance viewport/state.

## 9. Change control

После пользовательского утверждения `DEMO-RELEASE BASELINE V1.0` изменения release scope, module map, implementation sequence, shared UX contract и презентационных сценариев выполняются только:

```text
Chat 0 decision
→ ADR/decision record
→ plan baseline version bump
→ checklist regeneration/validation
```

Обычный feature PR не имеет права молча менять верхнеуровневый план.

## 10. Приоритет реализации после baseline

Canonical implementation sequence должна учитывать зависимости. Начальная последовательность:

1. `UX-THEME-001`;
2. `NORMATIVE-EVIDENCE` + `PERSONNEL-AUTHORITY` foundation;
3. завершение bounded lifecycle `OPJ` + `SHIFT`;
4. `CROSS-DOC` contract;
5. `APPLICATION`;
6. `GROUNDING`;
7. work contours (`WORK-PERMIT`, journals, current-operation works);
8. inspections/specialized journals;
9. workplace docs/schemes/emergency readiness;
10. switching documents;
11. dashboard/reporting and final demo scenarios.

Codex обязан проверить зависимости и может уточнить порядок внутри групп, но не менять состав модулей или Demo/Post-demo решения без `VERIFY/BLOCKER` с доказательством.
