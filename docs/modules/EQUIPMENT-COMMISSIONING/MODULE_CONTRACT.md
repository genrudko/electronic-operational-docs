# EQUIPMENT-COMMISSIONING — module contract

## MODULE ID
`EQUIPMENT-COMMISSIONING` — Ввод оборудования в работу.

## НАЗНАЧЕНИЕ
Bounded commissioning journal with basis, before/after state, checks, restrictions and links.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
create equipment commissioning record · record basis/checks · store before/after state · link repair/defect/application/OPJ.

## PRIMARY FACTS / DERIVED VIEWS
Facts: commissioning record; basis; state snapshots; check result; restriction. Views: registry; equipment history/detail.

## РОЛИ И ПОЛНОМОЧИЯ
executor/confirming person checked · registered record immutable.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; exact form/proven mode VERIFY.

## СВЯЗИ
links master data/defect/application/OPJ.

## SOURCE IDS / BENCHMARK
`REF-OD-061`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: equipment/basis/time; checks/state; restrictions/links. Post-demo: automatic EAM/SCADA import.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-COMMISSIONING-RECORD` (NOT_STARTED/ABSENT; EQUIPMENT-COMMISSIONING-001; AC-COMMISSIONING-RECORD-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `DEFECT`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved form/roles; required checks. Forbidden: не выдумывать universal fields; не exclude due to VERIFY.
