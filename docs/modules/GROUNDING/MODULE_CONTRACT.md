# GROUNDING — module contract

## MODULE ID
`GROUNDING` — Переносные заземления.

## НАЗНАЧЕНИЕ
Inventory and separate placement/removal facts with active location and handover.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
register grounding item · place at allowed location · remove and close placement · include active placements in handover.

## PRIMARY FACTS / DERIVED VIEWS
Facts: grounding item; placement; removal event; active location. Views: inventory; active placements; history; handover snapshot.

## РОЛИ И ПОЛНОМОЧИЯ
check right/object/restrictions · placement/removal are separate immutable facts.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; exact evidence mode VERIFY.

## СВЯЗИ
links OPJ/work permit/shift/equipment · SCADA not required.

## SOURCE IDS / BENCHMARK
`REF-OD-007`, `REF-OD-008`, `SRC-RESEARCH-SPECIALIZED`. Decisions: `D-11`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: inventory; place/remove; active state; shift/OPJ link. Post-demo: SCADA placement map; topology validation.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-GROUNDING-INVENTORY` (NOT_STARTED/ABSENT; GROUNDING-001; AC-GROUNDING-INVENTORY-001), `CAP-GROUNDING-PLACEMENT` (NOT_STARTED/ABSENT; GROUNDING-001; AC-GROUNDING-PLACEMENT-001), `CAP-GROUNDING-HANDOVER` (NOT_STARTED/ABSENT; GROUNDING-001; AC-GROUNDING-HANDOVER-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `OPJ`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: location identifiers; exact restrictions. Forbidden: не объединять place/remove в mutable status; не делать SCADA mandatory.
