# PERSONNEL-AUTHORITY — module contract

## MODULE ID
`PERSONNEL-AUTHORITY` — Персонал и оперативные полномочия.

## НАЗНАЧЕНИЕ
Лица, должности, квалификации, подрядчики и operational rights с structured scope, validity, basis и immutable authority-at-action snapshot.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
выдать право на действие/объект/срок · проверить право в момент действия · учесть явное замещение · проверить подрядный/командированный персонал · сохранить authority snapshot и объяснимый результат.

## PRIMARY FACTS / DERIVED VIEWS
Facts: person/history; position/category; qualification/group; imported positive source marker; structured operational grant; external engagement; substitution; authority evaluation. Views: lists of rights; person card; `ALLOW / DENY / VERIFY` result; reasons; history.

## РОЛИ И ПОЛНОМОЧИЯ
Application role, должность, квалификация, допуск к объекту и operational right разделены. Controlled action разрешается только server-side action-time evaluation; position/application role без structured grant не дают `ALLOW`.

## ДОКУМЕНТЫ И LEGAL MODE
Knowledge check, instruction, PEP/action confirmation и authority evaluation являются разными evidence objects. Authority evaluation не объявляет юридическую значимость и не заменяет `EvidenceEvent`.

## СВЯЗИ
Потребляется controlled actions последующих модулей · использует `MASTER-DATA` и `NORMATIVE-EVIDENCE` · переиспользует существующие employee/qualification/personnel-import facts.

## SOURCE IDS / BENCHMARK
`REF-OD-051`, `REF-OD-052`, `REF-OD-053`, `SRC-DEC-STAGE2`. Decisions: targeted benchmark по work item.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: personnel/qualifications; structured rights with scope/validity/basis; contractors/seconded/system-operator personnel; bounded substitution; action-time evaluation and immutable snapshot. Post-demo: HR/AD/СКУД integration; automatic external grants; production authority federation.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`; active work item `PERSONNEL-AUTHORITY-001`, issue #42, Draft PR #43.

- `CAP-PERSONNEL-REGISTRY`: existing employee/directory/qualification foundation, integration in progress; `AC-PERSONNEL-REGISTRY-001`.
- `CAP-AUTHORITY-GRANTS`: pure structured grant contract implemented; persistence pending; `AC-AUTHORITY-GRANTS-001`.
- `CAP-AUTHORITY-ACTION-TIME`: pure explainable evaluator and immutable snapshot implemented; ORM persistence/service pending; `AC-AUTHORITY-ACTION-TIME-001`.
- `CAP-AUTHORITY-EXTERNAL`: pure external-engagement/substitution semantics implemented; persistence/UI pending; `AC-AUTHORITY-EXTERNAL-001`.

Current slice:

```text
src/apps/organizations/authority.py
src/apps/organizations/tests/test_authority_contract.py
```

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `NORMATIVE-EVIDENCE`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data. Read-only acceptance UI starts only after persistence/service contract is stable.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: exact local right catalog; employment/substitution semantics per applicable local acts; basis applicability; downstream action requirements. Forbidden: смешивать app role и operational right; разрешать по должности; считать импортированную положительную отметку достаточным action-authorizing grant; автоматически переносить все права при замещении; объявлять `VERIFY` разрешением.
