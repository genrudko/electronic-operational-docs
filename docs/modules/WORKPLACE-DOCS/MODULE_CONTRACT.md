# WORKPLACE-DOCS — module contract

## MODULE ID
`WORKPLACE-DOCS` — Документация рабочего места.

## НАЗНАЧЕНИЕ
Реестр, применимость, версии, комплектность, review dates и ознакомление с точной редакцией.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
найти current revision · увидеть missing/overdue document · заменить revision без потери истории · зафиксировать familiarization.

## PRIMARY FACTS / DERIVED VIEWS
Facts: document class/applicability; revision; review schedule; completeness rule; familiarization event. Views: registry/detail; completeness matrix; overdue view.

## РОЛИ И ПОЛНОМОЧИЯ
управление редакциями и ознакомление имеют разные права · event привязан к exact revision.

## ДОКУМЕНТЫ И LEGAL MODE
Знак +/- источника не является legal-mode evidence.

## СВЯЗИ
поставляет docs схемам/emergency · не является universal journal builder.

## SOURCE IDS / BENCHMARK
`REF-OD-006`, `REF-OD-009`, `REF-OD-022`, `REF-OD-024`, `REF-OD-034`, `REF-OD-035`, `REF-OD-054`, `REF-OD-055`, `REF-OD-063`, `SRC-AUDIT-STAGE1`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-REFERENCE`: registry/applicability; versions/review; completeness; familiarization. Post-demo: full ECM; electronic key journal.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`. `CAP-WORKPLACE-REGISTRY` (IN_PROGRESS/IMPLEMENTED-PARTIAL; WORKPLACE-DOCS-001; AC-WORKPLACE-REGISTRY-001), `CAP-WORKPLACE-REVISION` (IN_PROGRESS/IMPLEMENTED-PARTIAL; WORKPLACE-DOCS-001; AC-WORKPLACE-REVISION-001), `CAP-WORKPLACE-COMPLETENESS` (NOT_STARTED/ABSENT; WORKPLACE-DOCS-001; AC-WORKPLACE-COMPLETENESS-001), `CAP-WORKPLACE-FAMILIARIZATION` (NOT_STARTED/ABSENT; WORKPLACE-DOCS-001; AC-WORKPLACE-FAMILIARIZATION-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `PERSONNEL-AUTHORITY`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: obligation rules; local familiarization process. Forbidden: не приравнивать acknowledgement к training; не выводить legal mode из +/-.
