# DASHBOARD-REPORTING — module contract

## MODULE ID
`DASHBOARD-REPORTING` — Оперативные представления и отчётность.

## НАЗНАЧЕНИЕ
Derived active-state views and reports without second database.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
see active defects/applications/works/groundings · drill down to source · generate report with provenance · prevent source edit from report.

## PRIMARY FACTS / DERIVED VIEWS
Facts: не владеет primary facts. Views: active dashboard; shift/period report; derived registry/print.

## РОЛИ И ПОЛНОМОЧИЯ
visibility follows source-module rights.

## ДОКУМЕНТЫ И LEGAL MODE
Derived view inherits source legal label and is not an original.

## СВЯЗИ
reads typed relations · owns no primary facts.

## SOURCE IDS / BENCHMARK
`SRC-DEC-STAGE2`, `SRC-AUDIT-STAGE1`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: active-state dashboard; drill-down; derived reports/provenance. Post-demo: enterprise BI; arbitrary report builder.

## CURRENT CODE STATUS / CAPABILITIES
`PRESENTATION-ONLY`; release `NOT_STARTED`. `CAP-DASHBOARD-ACTIVE` (NOT_STARTED/PRESENTATION-ONLY; DASHBOARD-REPORTING-001; AC-DASHBOARD-ACTIVE-001), `CAP-REPORTING-DERIVED` (NOT_STARTED/ABSENT; DASHBOARD-REPORTING-001; AC-REPORTING-DERIVED-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `CROSS-DOC`, `OPJ`, `DEFECT`, `SHIFT`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: presentation KPI list; aggregate-view rights. Forbidden: не store manual copy; не confuse presentation with lifecycle.
