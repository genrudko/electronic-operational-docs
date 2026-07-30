# WORK-PERMIT — module contract

## MODULE ID
`WORK-PERMIT` — Наряд-допуск.

## НАЗНАЧЕНИЕ
Hybrid permit: electronic authoring/version/card/print with paper original and required paper actions.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
create from approved form/template · check all participant rights · generate print original · maintain electronic card without replacing paper signatures.

## PRIMARY FACTS / DERIVED VIEWS
Facts: permit draft/version; participants/roles; equipment/workplace scope; safety measures; paper reference. Views: authoring workspace; state card; print form; version history.

## РОЛИ И ПОЛНОМОЧИЯ
each role checked by scope/time · crew changes historical.

## ДОКУМЕНТЫ И LEGAL MODE
DEMO-HYBRID; paper original/signatures retained where electronic replacement not proven.

## СВЯЗИ
source for permit work journal · links grounding/equipment/OPJ.

## SOURCE IDS / BENCHMARK
`REF-OD-010`, `REF-OD-012`, `REF-OD-014`, `REF-OD-059`, `SRC-RESEARCH-SPECIALIZED`. Decisions: `D-01`, `D-02`.

## DEMO / POST-DEMO
`DEMO-HYBRID`: authoring/versions; authority checks; print original; honest hybrid labels. Post-demo: fully electronic participant lifecycle; automatic admission.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-PERMIT-AUTHORING` (NOT_STARTED/ABSENT; WORK-PERMIT-001; AC-PERMIT-AUTHORING-001), `CAP-PERMIT-HYBRID` (NOT_STARTED/ABSENT; WORK-PERMIT-001; AC-PERMIT-HYBRID-001), `CAP-PERMIT-PRINT` (NOT_STARTED/ABSENT; WORK-PERMIT-001; AC-PERMIT-PRINT-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `PERSONNEL-AUTHORITY`, `MASTER-DATA`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved form/local regulation; exact signature boundary. Forbidden: не смешивать authoring and paper lifecycle; не заявлять full electronic signatures.
