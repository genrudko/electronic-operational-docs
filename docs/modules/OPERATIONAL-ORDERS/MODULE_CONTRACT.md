# OPERATIONAL-ORDERS — module contract

## MODULE ID
`OPERATIONAL-ORDERS` — Журнал распоряжений.

## НАЗНАЧЕНИЕ
Самостоятельный бумажный журнал распоряжений с явно маркированным electronic mirror.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
create mirror record · record giver/receiver/content · reflect execution and OPJ link · show paper reference.

## PRIMARY FACTS / DERIVED VIEWS
Facts: mirror record; paper reference; execution evidence; participants snapshot. Views: mirror registry; card; mirror correction history.

## РОЛИ И ПОЛНОМОЧИЯ
rights of giver/receiver checked · mirror does not replace paper signature.

## ДОКУМЕНТЫ И LEGAL MODE
PAPER-WITH-ELECTRONIC-MIRROR.

## СВЯЗИ
links OPJ/CROSS-DOC · separate from order-work journal.

## SOURCE IDS / BENCHMARK
`REF-OD-058`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-PAPER-MIRROR`: mirror label; paper reference; participants/content/execution. Post-demo: full electronic original.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-ORDERS-MIRROR` (NOT_STARTED/ABSENT; OPERATIONAL-ORDERS-001; AC-ORDERS-MIRROR-001), `CAP-ORDERS-EXECUTION` (NOT_STARTED/ABSENT; OPERATIONAL-ORDERS-001; AC-ORDERS-EXECUTION-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `OPJ`, `PERSONNEL-AUTHORITY`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: exact columns/local form; mirror correction rules. Forbidden: не смешивать с ORDER-WORK-JOURNAL; не называть mirror electronic original.
