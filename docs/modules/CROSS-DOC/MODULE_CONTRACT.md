# CROSS-DOC — module contract

## MODULE ID
`CROSS-DOC` — Междокументные связи.

## НАЗНАЧЕНИЕ
Typed relations with provenance and context snapshots without duplicate primary facts.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
link OPJ/defect/application/work/equipment · show source trail · preserve context snapshot · avoid duplicate fact.

## PRIMARY FACTS / DERIVED VIEWS
Facts: typed relation; relation provenance; context snapshot. Views: relation graph; backlinks; source trail.

## РОЛИ И ПОЛНОМОЧИЯ
rights checked in source and target modules · relation grants no authority.

## ДОКУМЕНТЫ И LEGAL MODE
Relation does not change legal mode or turn mirror into original.

## СВЯЗИ
shared capability · owns no domain fact.

## SOURCE IDS / BENCHMARK
`SRC-DEC-STAGE2`, `SRC-RESEARCH-VERTICAL`. Decisions: `D-15`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: typed relation; provenance/snapshot; reverse navigation. Post-demo: event bus; external knowledge graph.

## CURRENT CODE STATUS / CAPABILITIES
`FOUNDATION-ONLY`; release `NOT_STARTED`. `CAP-CROSSDOC-LINK` (NOT_STARTED/FOUNDATION-ONLY; CROSS-DOC-001; AC-CROSSDOC-LINK-001), `CAP-CROSSDOC-PROVENANCE` (NOT_STARTED/FOUNDATION-ONLY; CROSS-DOC-001; AC-CROSSDOC-PROVENANCE-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `PLATFORM`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: relation type catalog; cancellation rules. Forbidden: не duplicate primary facts; не use untyped generic links.

## ГОРИЗОНТАЛЬНЫЕ СВЯЗИ

Горизонтальная связь соединяет самостоятельные первичные факты разных предметных модулей в рамках одного оперативного процесса. Примеры:

- запись ОЖ → дефект оборудования;
- оперативная заявка → программа или бланк переключений;
- запись ОЖ о допуске → наряд или распоряжение;
- установка/снятие ПЗ → оборудование, запись ОЖ и документ переключений;
- результат осмотра → дефект и запись ОЖ.

Каждый модуль продолжает владеть своим первичным фактом. `CROSS-DOC` хранит только тип связи, источник, цель, provenance, context snapshot и состояние самой связи.

## ВЕРТИКАЛЬНЫЕ СВЯЗИ

Вертикальная связь обеспечивает прослеживаемость происхождения и развития факта во времени. Она связывает, например:

```text
основание или заявка
→ разрешение
→ исполняющий документ
→ запись ОЖ о начале
→ фактические действия
→ запись ОЖ о выполнении
→ результат или изменённое состояние оборудования
```

К вертикальным связям относятся source trail, производный документ, исполнение, результат, закрытие, исправление, отмена и другие типизированные этапы одной причинно-временной цепочки. Прямые ссылки обязаны сопровождаться обратной навигацией.

## OWNERSHIP И ГРАНИЦЫ `CROSS-DOC-001`

1. Общесистемный каталог типов связей, provenance, context snapshots, backlinks, source trail и relation graph реализуются в `CROSS-DOC-001`.
2. До `CROSS-DOC-001` предметный модуль может иметь только узкую внутреннюю связь, необходимую для собственного lifecycle: например, исправление зарегистрированной записи ОЖ относится к исходной записи ОЖ.
3. Узкая внутренняя связь не должна становиться параллельным универсальным relation engine и не должна заранее кодировать связи с ещё не реализованными модулями.
4. Связь не предоставляет право на действие, не меняет legal mode, не делает зеркало оригиналом и не переносит ownership первичного факта.
5. Безтиповые generic foreign-key links, копирование текста исходного факта вместо relation и дублирование одного факта в нескольких модулях запрещены.
6. Отмена или недействительность связи не удаляет связанные первичные факты и должна сохранять собственную историю.
