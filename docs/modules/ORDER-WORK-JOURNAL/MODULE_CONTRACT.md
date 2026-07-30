# ORDER-WORK-JOURNAL — module contract

## MODULE ID
`ORDER-WORK-JOURNAL` — Журнал работ по распоряжениям.

## НАЗНАЧЕНИЕ
Paper work journal with clearly labeled electronic mirror.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
enter mirror of paper row · record basis/performers/result · link OPJ/equipment · show paper reference.

## PRIMARY FACTS / DERIVED VIEWS
Facts: mirror record; paper journal reference; execution snapshot; participants. Views: mirror registry; card/history.

## РОЛИ И ПОЛНОМОЧИЯ
participant rights checked · mirror does not replace paper record.

## ДОКУМЕНТЫ И LEGAL MODE
DEMO-PAPER-MIRROR.

## СВЯЗИ
separate from operational orders and permit journal.

## SOURCE IDS / BENCHMARK
`REF-OD-059`, `SRC-DEC-STAGE2`. Decisions: `D-03`, `D-04`, `D-12`.

## DEMO / POST-DEMO
`DEMO-PAPER-MIRROR`: mirror label; participants/execution; paper reference. Post-demo: full electronic original.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-ORDER-WORK-MIRROR` (NOT_STARTED/ABSENT; ORDER-WORK-JOURNAL-001; AC-ORDER-WORK-JOURNAL-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `PERSONNEL-AUTHORITY`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: exact form/local rights; mirror correction rules. Forbidden: не смешивать with orders journal; не называть mirror original.
