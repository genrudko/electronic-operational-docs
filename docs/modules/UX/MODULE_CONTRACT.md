# UX — module contract

## MODULE ID
`UX` — Direction A UX.

## НАЗНАЧЕНИЕ
Единая visual/interaction system для shell, shared primitives и специализированных workspaces.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
работать во всех модулях в одной системе · переключить light/dark/system без смешанных поверхностей · пройти desktop/mobile сценарий.

## PRIMARY FACTS / DERIVED VIEWS
Facts: не владеет primary facts. Views: shared shell; component catalog; route/state matrix; theme tokens.

## РОЛИ И ПОЛНОМОЧИЯ
UI не предоставляет предметное право · скрытие control не заменяет server authorization.

## ДОКУМЕНТЫ И LEGAL MODE
Экранная тема не влияет на legal mode и print.

## СВЯЗИ
shared layer для всех маршрутов · specialized workspace сохраняет shared primitives.

## SOURCE IDS / BENCHMARK
`SRC-DEC-STAGE2`, `SRC-UX-DIRECTION-A`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-FUNCTIONAL`: shared shell/components; 1440x900,1024x768,390x844; all UI states; light/dark/system. Post-demo: accessibility certification; native mobile apps.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`. `CAP-UX-SHARED` (ACCEPTED/IMPLEMENTED-ACCEPTED; UX-FOUNDATION-001; AC-UX-SHARED-001), `CAP-UX-THEME` (READY/ABSENT; UX-THEME-001; AC-UX-THEME-001), `CAP-UX-RESPONSIVE` (IN_PROGRESS/IMPLEMENTED-PARTIAL; UX-CONTRACT-001; AC-UX-RESPONSIVE-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `PLATFORM`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: route inventory; status contrast. Forbidden: не создавать design system на каждый журнал; не использовать hardcoded feature surfaces.
