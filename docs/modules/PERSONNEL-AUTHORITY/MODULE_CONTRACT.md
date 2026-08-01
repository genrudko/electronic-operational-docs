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
`IMPLEMENTED-CANDIDATE`; release `IN_PROGRESS`; active work item `PERSONNEL-AUTHORITY-001`, issue #42, Draft PR #43.

- `CAP-PERSONNEL-REGISTRY`: существующие employee/directory/qualification facts переиспользованы; карточка сотрудника разделяет source markers и structured grants; `AC-PERSONNEL-REGISTRY-001` — candidate.
- `CAP-AUTHORITY-GRANTS`: pure contract, persistent structured grant, scope/validity/basis/source trace и read-only registry реализованы; `AC-AUTHORITY-GRANTS-001` — candidate.
- `CAP-AUTHORITY-ACTION-TIME`: explainable server-side evaluator, `ALLOW / DENY / VERIFY`, append-only persistent snapshot, digest и correction link реализованы; `AC-AUTHORITY-ACTION-TIME-001` — candidate.
- `CAP-AUTHORITY-EXTERNAL`: explicit external engagement и bounded substitution contract/persistence реализованы; синтетический contractor scenario включён в presentation data; `AC-AUTHORITY-EXTERNAL-001` — candidate.

Implemented boundary:

```text
src/apps/organizations/authority.py
src/apps/organizations/authority_models.py
src/apps/organizations/authority_services.py
src/apps/organizations/migrations/0008_personnel_authority_persistence.py
src/apps/organizations/migrations/0009_seed_demo_personnel_authority.py
src/apps/organizations/management/commands/seed_demo_personnel_authority.py
src/apps/organizations/views.py
src/apps/organizations/urls.py
src/templates/organizations/authority_registry.html
src/templates/organizations/authority_evaluation_detail.html
src/templates/organizations/employee_detail.html
src/apps/organizations/tests/test_authority_*.py
```

## PERSISTENCE / EVIDENCE CONTRACT

- `OperationalAuthorityGrant`: person + right/action + scope + validity + granting organization + basis status/reference + source IDs.
- `ExternalPersonnelEngagement`: home organization → host organization + relation kind + scope + validity + basis.
- `OperationalAuthoritySubstitution`: существующий `Substitution` расширяется только явно перечисленными actions/scope; права автоматически не копируются.
- `AuthorityEvaluationRecord`: append-only; update/delete запрещены; correction создаётся новым связанным record.
- snapshot и SHA-256 переиспользуют принятый normative-evidence canonicalization contract; secret-like keys запрещены.
- импортированный `EmployeeOperationalRight` остаётся source fact и никогда сам по себе не даёт `ALLOW`.

## PRESENTATION DATA

Conditional reversible data migration выполняется только при наличии организации `DEMO`; на иных БД — no-op. Создаются исключительно синтетические `DEMO-ONLY` grants и четыре сценария: confirmed `ALLOW`, explicit `DENY`, unconfirmed `VERIFY`, external contractor `ALLOW`. Реальные ФИО, локальные акты и production authority matrix не используются.

## DEPENDENCIES / UX CONTRACT
Dependencies: `MASTER-DATA`, `NORMATIVE-EVIDENCE`. Direction A; read-only реестр, карточка сотрудника и evaluation detail. Проверяемые состояния: populated/empty, confirmed/verify/rejected, internal/external, long basis/scope, technical snapshot disclosure.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: exact local right catalog; employment/substitution semantics per applicable local acts; basis applicability; qualification code catalogs; downstream action requirements. Forbidden: смешивать app role и operational right; разрешать по должности; считать импортированную положительную отметку достаточным action-authorizing grant; автоматически переносить все права при замещении; превращать русский free text в технический qualification code; объявлять `VERIFY` разрешением.
