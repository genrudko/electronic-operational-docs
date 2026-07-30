# OPJ — module contract

## MODULE ID
`OPJ` — Оперативный журнал и переговоры.

## НАЗНАЧЕНИЕ
Специализированный ОЖ: draft/revisions, immutable registration, correction/cancellation events и operational communication.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
вести draft/autosave · register immutable entry · correct/cancel by new event · record operational communication.

## PRIMARY FACTS / DERIVED VIEWS
Facts: journal/sequence; draft/revisions; registered entry; correction/cancellation; communication fact. Views: workspace; registered journal; entry detail; print/history.

## РОЛИ И ПОЛНОМОЧИЯ
registration/communication require rights · entry stores authority snapshot.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic-original target; proven mode VERIFY until official/local evidence.

## СВЯЗИ
links SHIFT/DEFECT/APPLICATION/GROUNDING · не поглощает facts other modules.

## SOURCE IDS / BENCHMARK
`REF-OD-023`, `REF-OD-056`, `SRC-AUDIT-STAGE1`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: draft/revisions; immutable registration; historical correction; operational communications. Post-demo: offline conflict merge; SCADA event ingest.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`. `CAP-OPJ-DRAFT` (IN_PROGRESS/IMPLEMENTED-PARTIAL; OPJ-LIFECYCLE-001; AC-OPJ-DRAFT-001), `CAP-OPJ-REGISTER` (IN_PROGRESS/IMPLEMENTED-PARTIAL; OPJ-LIFECYCLE-001; AC-OPJ-REGISTER-001), `CAP-OPJ-CORRECTION` (NOT_STARTED/ABSENT; OPJ-LIFECYCLE-001; AC-OPJ-CORRECTION-001), `CAP-OPJ-COMMUNICATION` (NOT_STARTED/ABSENT; OPJ-LIFECYCLE-001; AC-OPJ-COMMUNICATION-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `UX`, `PERSONNEL-AUTHORITY`, `MASTER-DATA`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: correction/retention contract; proven legal mode. Forbidden: не превращать ОЖ в контейнер всего; не переписывать registered original.
