# APPLICATION — module contract

## MODULE ID
`APPLICATION` — Оперативные заявки.

## НАЗНАЧЕНИЕ
Заявки на изменение режима/состояния с card, status history and links.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
create application with equipment/window · approve/reject with history · link switching and OPJ · work without mandatory SCADA map.

## PRIMARY FACTS / DERIVED VIEWS
Facts: application/revision; approval decision; time window; equipment scope. Views: registry; card/history; calendar.

## РОЛИ И ПОЛНОМОЧИЯ
create/approve rights are separate · external dispatch personnel via authority model.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic target; required fields and proven mode VERIFY.

## СВЯЗИ
source for switching/OPJ links · SCADA optional.

## SOURCE IDS / BENCHMARK
`REF-OD-017`, `REF-OD-057`, `SRC-RESEARCH-VERTICAL`. Decisions: `D-05`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: card/equipment/window; approval history; links. Post-demo: SCADA integration; mode calculations.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-APPLICATION-REGISTRY` (NOT_STARTED/ABSENT; APPLICATION-001; AC-APPLICATION-REGISTRY-001), `CAP-APPLICATION-LIFECYCLE` (NOT_STARTED/ABSENT; APPLICATION-001; AC-APPLICATION-LIFECYCLE-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `OPJ`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved form/lifecycle; external roles. Forbidden: не делать SCADA mandatory; не copy application into OPJ.
