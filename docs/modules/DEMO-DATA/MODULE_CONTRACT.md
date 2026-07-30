# DEMO-DATA — module contract

## MODULE ID
`DEMO-DATA` — Детерминированные данные и сценарии.

## НАЗНАЧЕНИЕ
Reproducible safe seed/reset and end-to-end presentation scenarios.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
seed same dataset by exact SHA · reset safely · run accepted scenarios · distinguish presentation data from readiness.

## PRIMARY FACTS / DERIVED VIEWS
Facts: demo fixture catalog; seed manifest; reset evidence; scenario definition. Views: dataset; scenario; reset/seed result.

## РОЛИ И ПОЛНОМОЧИЯ
demo identities fictional · real operational/personal data forbidden.

## ДОКУМЕНТЫ И LEGAL MODE
Demo data creates no legal documents and proves no legal readiness.

## СВЯЗИ
depends on shown modules · does not alter production contracts.

## SOURCE IDS / BENCHMARK
`SRC-AUDIT-STAGE1`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-FUNCTIONAL`: deterministic seed; safe reset; end-to-end scenarios. Post-demo: production data onboarding.

## CURRENT CODE STATUS / CAPABILITIES
`PRESENTATION-ONLY`; release `IN_PROGRESS`. `CAP-DEMO-SEED` (IN_PROGRESS/PRESENTATION-ONLY; DEMO-DATA-001; AC-DEMO-SEED-001), `CAP-DEMO-RESET` (IN_PROGRESS/IMPLEMENTED-PARTIAL; DEMO-DATA-001; AC-DEMO-RESET-001), `CAP-DEMO-SCENARIOS` (NOT_STARTED/PRESENTATION-ONLY; DEMO-DATA-001; AC-DEMO-SCENARIOS-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `DASHBOARD-REPORTING`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: final scenario catalog; coverage all modules. Forbidden: не use real enterprise data; не equate seed with ready lifecycle.
