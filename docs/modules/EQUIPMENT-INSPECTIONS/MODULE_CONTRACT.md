# EQUIPMENT-INSPECTIONS — module contract

## MODULE ID
`EQUIPMENT-INSPECTIONS` — Осмотры оборудования.

## НАЗНАЧЕНИЕ
Schedules and checklists with executor, measurements, deviations and linked defect.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
create inspection schedule · execute checklist · record measurements/deviation · create linked defect.

## PRIMARY FACTS / DERIVED VIEWS
Facts: inspection schedule; checklist revision; inspection fact; measurement/deviation. Views: schedule/calendar; inspection form; equipment history; deviation report.

## РОЛИ И ПОЛНОМОЧИЯ
executor checked by right/object · checklist version stored.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; exact forms/evidence VERIFY.

## СВЯЗИ
links master data/defect/OPJ · route engine not required for Demo.

## SOURCE IDS / BENCHMARK
`REF-OD-029`, `REF-OD-036`, `REF-OD-037`, `REF-OD-038`, `SRC-RESEARCH-SPECIALIZED`. Decisions: `D-09`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: schedule; checklist; measurements/deviation; defect creation. Post-demo: route points/GPS; offline mobile engine.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-INSPECTION-SCHEDULE` (NOT_STARTED/ABSENT; EQUIPMENT-INSPECTIONS-001; AC-INSPECTION-SCHEDULE-001), `CAP-INSPECTION-CHECKLIST` (NOT_STARTED/ABSENT; EQUIPMENT-INSPECTIONS-001; AC-INSPECTION-CHECKLIST-001), `CAP-INSPECTION-RESULT` (NOT_STARTED/ABSENT; EQUIPMENT-INSPECTIONS-001; AC-INSPECTION-RESULT-001), `CAP-INSPECTION-DEFECT` (NOT_STARTED/ABSENT; EQUIPMENT-INSPECTIONS-001; AC-INSPECTION-DEFECT-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `DEFECT`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: exact checklist/ranges; AVR program applicability. Forbidden: не defer whole module for route engine; не duplicate defect.
