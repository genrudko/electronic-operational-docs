# SWITCHING-DOCUMENTS — module contract

## MODULE ID
`SWITCHING-DOCUMENTS` — Бланки и программы переключений.

## НАЗНАЧЕНИЕ
Ручные ordinary/typical forms and programs with structured steps, versions, review, print and archive.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
create from template/manual · edit structured steps · record review comment/block release · approve/print/archive.

## PRIMARY FACTS / DERIVED VIEWS
Facts: switching template/version; document/version; operation step; review comment/resolution; approval; archive record. Views: template/document registry; authoring workspace; review queue; print/archive.

## РОЛИ И ПОЛНОМОЧИЯ
author/check/approve/execute rights separated · history immutable.

## ДОКУМЕНТЫ И LEGAL MODE
Electronic document-management target; legal/signature boundary VERIFY.

## СВЯЗИ
links application/schemes/OPJ/equipment · no topology calculation.

## SOURCE IDS / BENCHMARK
`REF-OD-015`, `REF-OD-016`, `REF-OD-018`, `REF-OD-019`, `REF-OD-027`, `REF-OD-028`, `REF-OD-030`, `REF-OD-031`, `SRC-RESEARCH-SPECIALIZED`. Decisions: `D-06`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: ordinary/typical templates; manual structured operations; versions/comments/approval; print/archive. Post-demo: auto-generation; topology/interlock; scheme editor.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-SWITCHING-TEMPLATES` (NOT_STARTED/ABSENT; SWITCHING-DOCUMENTS-001; AC-SWITCHING-TEMPLATES-001), `CAP-SWITCHING-DOCUMENT` (NOT_STARTED/ABSENT; SWITCHING-DOCUMENTS-001; AC-SWITCHING-DOCUMENT-001), `CAP-SWITCHING-REVIEW` (NOT_STARTED/ABSENT; SWITCHING-DOCUMENTS-001; AC-SWITCHING-REVIEW-001), `CAP-SWITCHING-ARCHIVE` (NOT_STARTED/ABSENT; SWITCHING-DOCUMENTS-001; AC-SWITCHING-ARCHIVE-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `APPLICATION`, `SCHEMES-DOCUMENTS`, `PERSONNEL-AUTHORITY`, `CROSS-DOC`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: approved forms/roles; execution marks. Forbidden: не обещать auto safe sequence; не bind comment to exact step without decision.
