# OPJ — module contract

## MODULE ID
`OPJ` — Оперативный журнал и переговоры.

## НАЗНАЧЕНИЕ
Специализированный ОЖ: draft/revisions, immutable registration,
correction/cancellation events и operational communication.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
вести draft/autosave · register immutable entry · correct/cancel by new event ·
record operational communication.

## PRIMARY FACTS / DERIVED VIEWS
Facts: journal/sequence; draft/revisions; registered entry;
correction/cancellation; communication fact. Views: workspace; registered
journal; entry detail; print/history.

## РОЛИ И ПОЛНОМОЧИЯ
registration/communication require rights · entry stores authority snapshot.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic-original target; proven mode VERIFY until official/local evidence.

## СВЯЗИ
links SHIFT/DEFECT/APPLICATION/GROUNDING · не поглощает facts other modules.

## SOURCE IDS / BENCHMARK
`REF-OD-023`, `REF-OD-056`, `SRC-AUDIT-STAGE1`. Decisions: targeted benchmark
по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: draft/revisions; immutable registration; historical correction;
operational communications. Post-demo: offline conflict merge; SCADA event
ingest.

## CURRENT CODE STATUS / CAPABILITIES

Текущий planning status принадлежит только
`docs/project/DEMO_RELEASE_PLAN.yaml`. По принятой истории GitHub модуль имеет
`IMPLEMENTED-ACCEPTED`; release `ACCEPTED`.

Историческое acceptance evidence: PR #47, exact head
`65997a9d51de4d066ec07277d4c660bfc307650e`, merge commit
`c4e344342b647ce59a390a04329d2cadb1f34d7c`.

- `CAP-OPJ-DRAFT` / `AC-OPJ-DRAFT-001` — accepted.
- `CAP-OPJ-REGISTER` / `AC-OPJ-REGISTER-001` — accepted.
- `CAP-OPJ-CORRECTION` / `AC-OPJ-CORRECTION-001` — accepted.
- `CAP-OPJ-COMMUNICATION` / `AC-OPJ-COMMUNICATION-001` — accepted.

## DEPENDENCIES / UX CONTRACT
Dependencies: `UX`, `PERSONNEL-AUTHORITY`, `MASTER-DATA`. Direction A;
1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: final legal mode and retention periods. Forbidden: не превращать ОЖ в
контейнер всего; не переписывать registered original; не считать принятый OPJ
реализацией `SHIFT-HANDOVER-001` или общего `CROSS-DOC-001`.

## ГРАНИЦА «ЧЕРНОВИК → ЧИСТОВИК»

1. `OperationalDraftEntry` является редактируемой рабочей записью открытой
   смены. Для неё действуют autosave, revisions, conflict detection, удаление
   из рабочего набора и восстановление. Изменение такой записи является обычным
   редактированием черновика, а не исправлением зарегистрированной записи.
2. Регистрация отдельной подготовленной строки создаёт связанный неизменяемый
   `OperationalLogEntry` в зарегистрированном журнале — чистовике.
3. После успешной регистрации исходная черновая строка не должна исчезать без
   объяснения. Она сохраняет прослеживаемую связь с чистовиком, получает явное
   состояние «зарегистрирована» и становится недоступной для редактирования.
4. Открытая смена продолжает работу с остальными незарегистрированными строками.
   Регистрация записи не равна сдаче смены и не закрывает смену автоматически.
5. Исправление и отмена допустимы только для зарегистрированного чистовика. Они
   создают новую связанную зарегистрированную запись или append-only событие,
   сохраняют первоначальную редакцию и не изменяют исходный
   `OperationalLogEntry`.
6. `SHIFT-HANDOVER-001` использует уже сформированный зарегистрированный журнал
   при сдаче и приёмке смены, но не владеет механизмом регистрации строк.

## ПОЛЬЗОВАТЕЛЬСКАЯ ГРАНИЦА LIFECYCLE

- Основными пользовательскими пространствами остаются принятый рабочий
  черновик и зарегистрированный журнал.
- Отдельный полноэкранный «центр жизненного цикла записи» не является
  обязательным или основным маршрутом.
- Регистрация выполняется из контекста выбранной черновой строки; исправление,
  отмена и просмотр первоначальной редакции — из контекста зарегистрированной
  строки чистовика.
- Digest, canonical snapshot, authority evaluation и internal event codes —
  служебные реквизиты; они не доминируют в интерфейсе оператора.
- Direction A, Onest Variable, canonical EOD Outline 24 и принятая геометрия
  ОЖ сохраняются; feature-local параллельная дизайн-система запрещена.

## ОПЕРАТИВНЫЕ ПЕРЕГОВОРЫ

1. В ОЖ фиксируется оперативно значимый результат переговоров: команда,
   разрешение, подтверждение, отказ, сообщение об исполнении или сообщение о
   нарушении нормального режима.
2. Полная ручная карточка телефонного разговора или стенограмма не является
   штатным пользовательским сценарием Demo.
3. Необходимые реквизиты участника, направления и канала вводятся компактно в
   контексте записи только тогда, когда они требуются предметным сценарием;
   результат остаётся частью хронологии ОЖ.
4. Автоматическое получение аудиозаписи и метаданных из специализированной
   системы регистрации переговоров относится к последующей интеграции.
