# CROSS-DOC — module contract

## MODULE ID
`CROSS-DOC` — Междокументные связи.

## НАЗНАЧЕНИЕ
Typed relations with provenance and context snapshots without duplicate primary facts.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
link OPJ/defect/application/work/equipment · show source trail · preserve context snapshot · avoid duplicate fact.

## PRIMARY FACTS / DERIVED VIEWS
Facts: typed relation; relation provenance; context snapshot. Views: relation graph; backlinks; source trail.

## РОЛИ И ПОЛНОМОЧИЯ
rights checked in source and target modules · relation grants no authority.

## ДОКУМЕНТЫ И LEGAL MODE
Relation does not change legal mode or turn mirror into original.

## СВЯЗИ
shared capability · owns no domain fact.

## SOURCE IDS / BENCHMARK
`SRC-DEC-STAGE2`, `SRC-RESEARCH-VERTICAL`. Decisions: `D-15`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: typed relation; provenance/snapshot; reverse navigation. Post-demo: event bus; external knowledge graph.

## CURRENT CODE STATUS / CAPABILITIES
`FOUNDATION-ONLY`; release `NOT_STARTED`. `CAP-CROSSDOC-LINK` (NOT_STARTED/FOUNDATION-ONLY; CROSS-DOC-001; AC-CROSSDOC-LINK-001), `CAP-CROSSDOC-PROVENANCE` (NOT_STARTED/FOUNDATION-ONLY; CROSS-DOC-001; AC-CROSSDOC-PROVENANCE-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `PLATFORM`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: relation type catalog; cancellation rules. Forbidden: не duplicate primary facts; не use untyped generic links.
