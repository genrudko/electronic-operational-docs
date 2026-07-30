# BREAKER-INTERRUPTIONS — module contract

## MODULE ID
`BREAKER-INTERRUPTIONS` — Отключения токов КЗ выключателями.

## НАЗНАЧЕНИЕ
Interruption events and accumulated breaker resource/threshold.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
record interruption event · record current/source if known · update accumulated resource · flag inspection/repair threshold.

## PRIMARY FACTS / DERIVED VIEWS
Facts: interruption event; current/source; accumulated count/resource; threshold requirement. Views: event journal; breaker resource card; threshold warnings.

## РОЛИ И ПОЛНОМОЧИЯ
authorized recorder · required integration not needed in Demo.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; form/proven mode VERIFY.

## СВЯЗИ
links equipment/OPJ/inspection/defect.

## SOURCE IDS / BENCHMARK
`REF-OD-064`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: manual event; resource/threshold; inspection/repair link. Post-demo: automatic RZA/SCADA import.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-BREAKER-EVENT` (NOT_STARTED/ABSENT; BREAKER-INTERRUPTIONS-001; AC-BREAKER-EVENT-001), `CAP-BREAKER-RESOURCE` (NOT_STARTED/ABSENT; BREAKER-INTERRUPTIONS-001; AC-BREAKER-RESOURCE-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved form/resource rules; current source. Forbidden: не invent auto calculations; не exclude without integration.
