# PERMIT-WORK-JOURNAL — module contract

## MODULE ID
`PERMIT-WORK-JOURNAL` — Журнал работ по нарядам.

## НАЗНАЧЕНИЕ
Electronic primary journal derived from permit/work facts without second independent database.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
derive journal row from source facts · open source from row · render approved view/print · prevent independent edit.

## PRIMARY FACTS / DERIVED VIEWS
Facts: journal projection config; source references. Views: electronic journal; print/filter/search.

## РОЛИ И ПОЛНОМОЧИЯ
view rights follow source · journal grants no new authority.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic-original target; proven mode VERIFY.

## СВЯЗИ
derived from work permit/execution · separate from order-work journal.

## SOURCE IDS / BENCHMARK
`REF-OD-059`, `SRC-DEC-STAGE2`, `SRC-RESEARCH-SPECIALIZED`. Decisions: `D-04`.

## DEMO / POST-DEMO
`DEMO-FUNCTIONAL`: derived formation; traceability; electronic register/print. Post-demo: manual second database.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-PERMIT-JOURNAL-DERIVED` (NOT_STARTED/ABSENT; PERMIT-WORK-JOURNAL-001; AC-PERMIT-JOURNAL-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `WORK-PERMIT`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved form; proven legal mode. Forbidden: не создавать duplicate fact; не смешивать with paper mirror journal.
