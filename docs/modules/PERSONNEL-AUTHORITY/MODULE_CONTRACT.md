# PERSONNEL-AUTHORITY — module contract

## MODULE ID
`PERSONNEL-AUTHORITY` — Персонал и оперативные полномочия.

## НАЗНАЧЕНИЕ
Лица, должности, квалификации, подрядчики и operational rights с scope, validity, basis и immutable snapshot.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
выдать право на объект/срок · проверить право в момент действия · учесть замещение/подрядчика · сохранить authority snapshot.

## PRIMARY FACTS / DERIVED VIEWS
Facts: person/history; position/category; qualification/group; granted right; scope/validity/basis; substitution. Views: lists of rights; person card; allow/deny result; history.

## РОЛИ И ПОЛНОМОЧИЯ
application role отделена от operational right · server-side action-time evaluation.

## ДОКУМЕНТЫ И LEGAL MODE
Knowledge check, instruction and PEP are separate evidence objects.

## СВЯЗИ
потребляется всеми controlled actions · использует MASTER-DATA/NORMATIVE-EVIDENCE.

## SOURCE IDS / BENCHMARK
`REF-OD-051`, `REF-OD-052`, `REF-OD-053`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: personnel/qualifications; rights/scope/validity; contractors/seconded; action-time snapshot. Post-demo: HR/AD integration; automatic external grants.

## CURRENT CODE STATUS / CAPABILITIES
`ABSENT`; release `NOT_STARTED`. `CAP-PERSONNEL-REGISTRY` (NOT_STARTED/ABSENT; PERSONNEL-AUTHORITY-001; AC-PERSONNEL-REGISTRY-001), `CAP-AUTHORITY-GRANTS` (NOT_STARTED/ABSENT; PERSONNEL-AUTHORITY-001; AC-AUTHORITY-GRANTS-001), `CAP-AUTHORITY-ACTION-TIME` (NOT_STARTED/ABSENT; PERSONNEL-AUTHORITY-001; AC-AUTHORITY-ACTION-TIME-001), `CAP-AUTHORITY-EXTERNAL` (NOT_STARTED/ABSENT; PERSONNEL-AUTHORITY-001; AC-AUTHORITY-EXTERNAL-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `NORMATIVE-EVIDENCE`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: right catalog; employment/substitution semantics; local grant acts. Forbidden: не смешивать app role и operational right; не разрешать только по должности.
