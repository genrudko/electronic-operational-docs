# EMERGENCY-READINESS — module contract

## MODULE ID
`EMERGENCY-READINESS` — Аварийная и пожарная готовность.

## НАЗНАЧЕНИЕ
Quick access to applicable emergency/fire instructions/cards and revision used in event context.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
open applicable instruction/card quickly · filter by object/event · snapshot used revision · link emergency OPJ context.

## PRIMARY FACTS / DERIVED VIEWS
Facts: emergency applicability; current revision; incident context snapshot; contact reference. Views: quick access; cards/instructions; revision history.

## РОЛИ И ПОЛНОМОЧИЯ
editing and emergency viewing rights separate · view does not auto-create familiarization.

## ДОКУМЕНТЫ И LEGAL MODE
DEMO-REFERENCE; source documents keep own paper/electronic mode.

## СВЯЗИ
uses workplace docs and links OPJ · not full incident management.

## SOURCE IDS / BENCHMARK
`REF-OD-001`, `REF-OD-002`, `REF-OD-003`, `REF-OD-004`, `REF-OD-005`, `REF-OD-032`, `REF-OD-033`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-REFERENCE`: quick access; object applicability; current revision; OPJ context. Post-demo: full incident workflow; SCADA triggers.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-EMERGENCY-ACCESS` (NOT_STARTED/ABSENT; EMERGENCY-READINESS-001; AC-EMERGENCY-ACCESS-001), `CAP-EMERGENCY-REVISION` (NOT_STARTED/ABSENT; EMERGENCY-READINESS-001; AC-EMERGENCY-REVISION-001), `CAP-EMERGENCY-CONTEXT` (NOT_STARTED/ABSENT; EMERGENCY-READINESS-001; AC-EMERGENCY-CONTEXT-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `WORKPLACE-DOCS`, `OPJ`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: exact card/contact classes; emergency access rights. Forbidden: не build full incident system; не treat open as familiarization.
