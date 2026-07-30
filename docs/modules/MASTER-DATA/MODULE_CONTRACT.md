# MASTER-DATA — module contract

## MODULE ID
`MASTER-DATA` — Организации, объекты и оборудование.

## НАЗНАЧЕНИЕ
Единые справочники организаций, рабочих мест, оборудования и диспетчерской структуры.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
выбрать оборудование по иерархии/alias · сохранить equipment snapshot · определить способ управления.

## PRIMARY FACTS / DERIVED VIEWS
Facts: organization/division/workplace; equipment asset/type; dispatch relations; aliases. Views: trees/selectors; equipment card; history.

## РОЛИ И ПОЛНОМОЧИЯ
изменение справочника отделено от оперативного права · история хранит snapshot.

## ДОКУМЕНТЫ И LEGAL MODE
Справочные записи не определяют legal mode оперативного документа.

## СВЯЗИ
поставляет references/snapshots · не владеет журналами.

## SOURCE IDS / BENCHMARK
`REF-OD-013`, `REF-OD-020`, `REF-OD-021`, `SRC-AUDIT-STAGE1`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-FUNCTIONAL`: organizations/workplaces; equipment/aliases; dispatch relations. Post-demo: ERP/EAM/SCADA sync; unreviewed import.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`. `CAP-MASTER-ORG` (IN_PROGRESS/IMPLEMENTED-PARTIAL; MASTER-DATA-ALIGNMENT-001; AC-MASTER-ORG-001), `CAP-MASTER-EQUIPMENT` (ACCEPTED/IMPLEMENTED-ACCEPTED; EQUIPMENT-FOUNDATION; AC-MASTER-EQUIPMENT-001), `CAP-MASTER-DISPATCH` (IN_PROGRESS/IMPLEMENTED-PARTIAL; MASTER-DATA-ALIGNMENT-001; AC-MASTER-DISPATCH-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `PLATFORM`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: classifier catalog; admin boundaries. Forbidden: не разделять ЩПТ и ШОТ на виды только по названию; не считать importer product module.
