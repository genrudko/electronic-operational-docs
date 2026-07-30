# SCHEMES-DOCUMENTS — module contract

## MODULE ID
`SCHEMES-DOCUMENTS` — Утверждённые и оперативные схемы.

## НАЗНАЧЕНИЕ
Версионируемое хранение схем без встроенного editor в Demo.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
найти current scheme · просмотреть fullscreen/print · увидеть approval/history · связать с equipment/document.

## PRIMARY FACTS / DERIVED VIEWS
Facts: scheme type/applicability; revision/approval; current marker. Views: registry; viewer/fullscreen; revision history; print.

## РОЛИ И ПОЛНОМОЧИЯ
управление revision требует права · viewer доступен по applicability.

## ДОКУМЕНТЫ И LEGAL MODE
DEMO-REFERENCE; paper/electronic boundary определяется local contract.

## СВЯЗИ
используется switching/OPJ · future editor uses same stable IDs.

## SOURCE IDS / BENCHMARK
`REF-OD-025`, `REF-OD-026`, `REF-OD-042`, `REF-OD-043`, `REF-OD-044`, `REF-OD-045`, `REF-OD-046`, `REF-OD-047`, `REF-OD-048`, `REF-OD-049`, `REF-OD-050`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-REFERENCE`: registry/type/applicability; current revision/history; viewer/fullscreen/print. Post-demo: scheme editor/UGO; topology/state/interlocks; switching integration.

## CURRENT CODE STATUS / CAPABILITIES
`FOUNDATION-ONLY`; release `NOT_STARTED`. `CAP-SCHEMES-REGISTRY` (NOT_STARTED/FOUNDATION-ONLY; SCHEMES-DOCUMENTS-001; AC-SCHEMES-REGISTRY-001), `CAP-SCHEMES-VERSIONS` (NOT_STARTED/FOUNDATION-ONLY; SCHEMES-DOCUMENTS-001; AC-SCHEMES-VERSIONS-001), `CAP-SCHEMES-VIEW` (NOT_STARTED/FOUNDATION-ONLY; SCHEMES-DOCUMENTS-001; AC-SCHEMES-VIEW-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `WORKPLACE-DOCS`, `MASTER-DATA`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approval rules; file formats/rights. Forbidden: не делать editor в Demo; не создавать второй catalog для future editor.
