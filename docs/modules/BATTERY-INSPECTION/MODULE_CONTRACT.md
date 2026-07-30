# BATTERY-INSPECTION — module contract

## MODULE ID
`BATTERY-INSPECTION` — Осмотр аккумуляторных батарей.

## НАЗНАЧЕНИЕ
Periodic battery checklist, measurements, deviations and linked defect.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
choose battery/checklist · enter measurements/notes · detect deviation · create defect.

## PRIMARY FACTS / DERIVED VIEWS
Facts: battery inspection fact; checklist revision; measurement set; deviation. Views: inspection journal; parameter history; deviation report.

## РОЛИ И ПОЛНОМОЧИЯ
executor right/object checked · fields from source-bound contract.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; exact metrics/form/proven mode VERIFY.

## СВЯЗИ
links inspection/defect/OPJ.

## SOURCE IDS / BENCHMARK
`REF-OD-065`, `SRC-RESEARCH-SPECIALIZED`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: periodic checklist; measurements/notes; deviation/defect. Post-demo: telemetry collection.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-BATTERY-CHECKLIST` (NOT_STARTED/ABSENT; BATTERY-INSPECTION-001; AC-BATTERY-CHECKLIST-001), `CAP-BATTERY-MEASUREMENTS` (NOT_STARTED/ABSENT; BATTERY-INSPECTION-001; AC-BATTERY-MEASUREMENTS-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `EQUIPMENT-INSPECTIONS`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved form/metrics; period/ranges. Forbidden: не invent metric set; не copy measurements from template.
