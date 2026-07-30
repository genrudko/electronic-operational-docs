# CURRENT-OPERATION-WORKS — module contract

## MODULE ID
`CURRENT-OPERATION-WORKS` — Работы текущей эксплуатации.

## НАЗНАЧЕНИЕ
Approved repair-personnel list, operational-personnel schedule, execution fact and derived journal.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
manage approved work-list revision · plan operational schedule · record execution against active basis · record result/deviation/defect.

## PRIMARY FACTS / DERIVED VIEWS
Facts: work-list revision; schedule item; execution fact; result/deviation; basis snapshot. Views: work list; schedule; execution card; journal.

## РОЛИ И ПОЛНОМОЧИЯ
eligibility checked by person/work/equipment/revision · execution stores basis snapshot.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; exact forms/legal mode VERIFY.

## СВЯЗИ
links equipment/DEFECT/OPJ · not work by order.

## SOURCE IDS / BENCHMARK
`REF-OD-011`, `REF-OD-039`, `REF-OD-066`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: repair list; operational schedule; execution/result; derived journal. Post-demo: EAM integration.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-CURRENT-RULESET` (NOT_STARTED/ABSENT; CURRENT-OPERATION-WORKS-001; AC-CURRENT-RULESET-001), `CAP-CURRENT-SCHEDULE` (NOT_STARTED/ABSENT; CURRENT-OPERATION-WORKS-001; AC-CURRENT-SCHEDULE-001), `CAP-CURRENT-EXECUTION` (NOT_STARTED/ABSENT; CURRENT-OPERATION-WORKS-001; AC-CURRENT-EXECUTION-001), `CAP-CURRENT-JOURNAL` (NOT_STARTED/ABSENT; CURRENT-OPERATION-WORKS-001; AC-CURRENT-JOURNAL-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `PERSONNEL-AUTHORITY`, `MASTER-DATA`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved forms/roles; legal mode. Forbidden: не смешивать with orders; не create execution without active basis.
