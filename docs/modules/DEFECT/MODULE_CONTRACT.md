# DEFECT — module contract

## MODULE ID
`DEFECT` — Журнал дефектов оборудования.

## НАЗНАЧЕНИЕ
Самостоятельный primary fact дефекта с lifecycle, history, print and OPJ/equipment links.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
register defect · assign deadline/responsible · record resolution/ack/close · view immutable history.

## PRIMARY FACTS / DERIVED VIEWS
Facts: defect record; deadline; resolution evidence; closure evidence; OPJ relation. Views: registry; detail; print; history.

## РОЛИ И ПОЛНОМОЧИЯ
actions require authority · future authority model does not rewrite accepted history.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; proven mode VERIFY.

## СВЯЗИ
links OPJ/equipment/inspections/works · не является строкой ОЖ.

## SOURCE IDS / BENCHMARK
`REF-OD-060`, `SRC-AUDIT-STAGE1`. Decisions: `D-08`.

## DEMO / POST-DEMO
`DEMO-FUNCTIONAL`: accepted DEFECT-001 vertical slice; separate card/lifecycle/history/print. Post-demo: advanced classifiers/analytics; EAM integration.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-ACCEPTED`; release `ACCEPTED`. `CAP-DEFECT-REGISTRY` (ACCEPTED/IMPLEMENTED-ACCEPTED; DEFECT-001; AC-DEFECT-REGISTRY-001), `CAP-DEFECT-LIFECYCLE` (ACCEPTED/IMPLEMENTED-ACCEPTED; DEFECT-001; AC-DEFECT-LIFECYCLE-001), `CAP-DEFECT-OPJ-LINK` (ACCEPTED/IMPLEMENTED-ACCEPTED; DEFECT-001; AC-DEFECT-OPJ-LINK-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: proven legal mode; future classifiers. Forbidden: не сводить defect к ОЖ; не обнулять accepted DEFECT-001.
