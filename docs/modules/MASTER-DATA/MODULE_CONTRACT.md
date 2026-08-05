# MASTER-DATA — module contract

## MODULE ID
`MASTER-DATA` — Организации, объекты и оборудование.

## НАЗНАЧЕНИЕ
Единые справочники организаций, рабочих мест, оборудования и диспетчерской
структуры.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
выбрать оборудование по иерархии/alias · сохранить equipment snapshot ·
определить способ управления.

## PRIMARY FACTS / DERIVED VIEWS
Facts: organization/division/workplace; equipment asset/type; dispatch
relations; aliases. Views: trees/selectors; equipment card; history.

## РОЛИ И ПОЛНОМОЧИЯ
изменение справочника отделено от оперативного права · история хранит snapshot.

## ДОКУМЕНТЫ И LEGAL MODE
Справочные записи не определяют legal mode оперативного документа.

## СВЯЗИ
поставляет references/snapshots · не владеет журналами.

## SOURCE IDS / BENCHMARK
`REF-OD-013`, `REF-OD-020`, `REF-OD-021`, `SRC-AUDIT-STAGE1`. Decisions:
targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-FUNCTIONAL`: organizations/workplaces; equipment/aliases; dispatch
relations. Post-demo: ERP/EAM/SCADA sync; unreviewed import.

## CURRENT CODE STATUS / CAPABILITIES

Текущий planning status принадлежит только
`docs/project/DEMO_RELEASE_PLAN.yaml`. Модуль остаётся
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`, поскольку открытые classifier и
administrative-boundary VERIFY items не закрыты.

При этом bounded work item `MASTER-DATA-ALIGNMENT-001` принят: PR #35, exact
head `e507b63ab35a4767c25364d729accb9a741af874`, merge commit
`b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb`.

- `CAP-MASTER-ORG` / `AC-MASTER-ORG-001` — accepted bounded slice.
- `CAP-MASTER-EQUIPMENT` / `AC-MASTER-EQUIPMENT-001` — accepted.
- `CAP-MASTER-DISPATCH` / `AC-MASTER-DISPATCH-001` — accepted bounded slice.

Принятие work item не означает автоматическую полную приёмку всего будущего
Demo-depth модуля.

## DEPENDENCIES / UX CONTRACT
Dependencies: `PLATFORM`. Direction A; 1440×900, 1024×768, 390×844;
loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: classifier catalog; admin boundaries. Forbidden: не разделять ЩПТ и ШОТ
на виды только по названию; не считать importer product module.
