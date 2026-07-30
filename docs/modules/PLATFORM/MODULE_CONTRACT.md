# PLATFORM — module contract

## MODULE ID
`PLATFORM` — Платформенные механизмы.

## НАЗНАЧЕНИЕ
Идентификация, аудит, неизменяемость, вложения, поиск, печать и изолированный runtime.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
зарегистрировать immutable snapshot · получить audit trail · найти и распечатать документ · подтвердить runtime health.

## PRIMARY FACTS / DERIVED VIEWS
Facts: authentication event; audit event; immutable snapshot/hash; attachment metadata. Views: audit trail; search results; print view; runtime evidence.

## РОЛИ И ПОЛНОМОЧИЯ
предметное право задаёт PERSONNEL-AUTHORITY · service account не подменяет автора.

## ДОКУМЕНТЫ И LEGAL MODE
Техническая целостность и ПЭП-primitives не доказывают legal mode документа.

## СВЯЗИ
primitives для всех модулей · не владеет предметными lifecycle.

## SOURCE IDS / BENCHMARK
`SRC-AUDIT-STAGE1`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-FUNCTIONAL`: identity/audit; snapshots/hashes; attachments/search/print; runtime boundaries. Post-demo: HA/replication; full offline-first; uncatalogued integrations.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`. `CAP-PLATFORM-AUDIT` (IN_PROGRESS/IMPLEMENTED-PARTIAL; PLATFORM-AUDIT-001; AC-PLATFORM-AUDIT-001), `CAP-PLATFORM-RUNTIME` (ACCEPTED/IMPLEMENTED-ACCEPTED; AUTO-001; AC-PLATFORM-RUNTIME-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: none. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: retention policy; ПЭП boundary. Forbidden: не переносить предметные статусы в core; не объявлять техническую подпись юридической.
