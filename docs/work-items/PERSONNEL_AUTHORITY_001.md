# PERSONNEL-AUTHORITY-001 — execution package

**Issue:** #42  
**Branch:** `feature/personnel-authority-001`  
**Starting main:** `711780222ad1656e54052da116c2dde8fba9e5e6`  
**Accepted application baseline:** `6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0`

## WORK ITEM

```text
ID: PERSONNEL-AUTHORITY-001
PARENT RELEASE: DEMO-RELEASE BASELINE V1.0
PARENT MODULE: PERSONNEL-AUTHORITY
CAPABILITIES:
- CAP-PERSONNEL-REGISTRY
- CAP-AUTHORITY-GRANTS
- CAP-AUTHORITY-ACTION-TIME
- CAP-AUTHORITY-EXTERNAL
ACCEPTANCE:
- AC-PERSONNEL-REGISTRY-001
- AC-AUTHORITY-GRANTS-001
- AC-AUTHORITY-ACTION-TIME-001
- AC-AUTHORITY-EXTERNAL-001
```

## GOAL

Довести существующий personnel foundation до bounded-контура оперативных полномочий:

1. structured grant: лицо + действие + область + период + основание;
2. server-side authority-at-action evaluation;
3. explicit external/seconded/contractor and substitution semantics;
4. immutable snapshot фактов, использованных при решении;
5. отсутствие authorization по одной должности, application role или импортной отметке.

## FACTUAL START

Существуют и переиспользуются:

- `Organization`, `Division`, `Workplace`, `OperationalArea`, `Position`, `Employee`;
- `EmployeeQualification`;
- `OperationalRightDefinition` и импортируемый `EmployeeOperationalRight`;
- `RoleAssignment`, `ResponsibilityScope`, `Substitution` как отдельный legacy/application foundation;
- `EmployeeEnergySiteAuthorization`;
- controlled personnel importer и provenance;
- `LegalModeDecision`, `EvidenceEvent`, canonical JSON, SHA-256 и actor snapshot;
- read-only personnel directory и employee card.

Не существовали как законченный contract:

- structured action/object scope grant;
- explainable `ALLOW / DENY / VERIFY` evaluator;
- immutable authority evaluation snapshot;
- bounded external personnel engagement;
- explicit non-automatic substitution of operational rights.

## DOMAIN BOUNDARY

1. Application role, position, qualification, site authorization и operational right не взаимозаменяемы.
2. `ALLOW` требует явный matching grant с действующим периодом, scope и подтверждённым basis.
3. `VERIFY` не превращается в `ALLOW` автоматически.
4. Замещение разрешает только явно перечисленные actions/scope и только если исходный grant допускает замещение.
5. Внешний персонал требует отдельную действующую связь home organization → host organization.
6. Квалификации принадлежат фактическому actor и не наследуются при замещении.
7. Snapshot содержит факты решения, но не password/token/secret.
8. Authority result не является юридическим заключением и не заменяет evidence event предметного действия.

## IMPLEMENTED SLICE 1 — PURE CONTRACT

```text
src/apps/organizations/authority.py
src/apps/organizations/tests/test_authority_contract.py
```

Реализованы:

- `AuthorityDecision`: `ALLOW`, `DENY`, `VERIFY`;
- `AuthorityBasisStatus`: `CONFIRMED`, `VERIFY`, `REJECTED`;
- structured `AuthorityScope` для organization/division/workplace/operational area/energy site/equipment;
- actor/request/grant/qualification/substitution/external-engagement facts;
- deterministic pure `evaluate_authority()`;
- stable reason codes;
- deep immutable snapshot;
- digest через принятый `apps.normatives.evidence.sha256_digest`;
- recursive secret-like key rejection;
- timezone-aware action-time and validity windows.

Focused tests проверяют:

- explicit confirmed grant → `ALLOW`;
- должность и application role без grant → `DENY`;
- unconfirmed basis → `VERIFY`;
- expired grant и scope mismatch → `DENY`;
- required qualification at action time;
- explicit bounded substitution;
- external personnel host engagement;
- inactive/expired employment;
- deterministic immutable snapshot;
- secret rejection и timezone validation.

## NEXT SLICE

1. Проверить slice 1 через exact-head CI.
2. После зелёного contract gate добавить persistence:
   - structured grant;
   - external personnel engagement;
   - append-only authority evaluation record;
   - migration and PostgreSQL tests.
3. Реализовать ORM-backed evaluator service без изменения consuming modules.
4. Только после устойчивого persistence/service contract добавить read-only acceptance UI.

## ALLOWED BOUNDARY

См. issue #42. Основная граница:

```text
docs/work-items/PERSONNEL_AUTHORITY_001.md
applicable canonical plan/module/checklist views
src/apps/organizations/authority*.py
src/apps/organizations/models.py / services.py / migrations / tests
src/apps/organizations/views.py / urls.py / forms.py / admin.py
src/templates/organizations/**
minimal imports/normatives bridge only when proven
```

## PROTECTED BOUNDARY

- OPJ/SHIFT/DEFECT/work-permit/switching lifecycle;
- master-data/import redesign;
- historical migrations/import facts;
- real personal data/local acts;
- second signature/hash/authentication framework;
- preview;
- Ready for Review and merge without explicit user command.

## RISK / DELIVERY

```text
slice 1: APP_LOGIC
persistence: SCHEMA_DATA
runtime delivery: FULL_DEVELOPMENT after persistence
preview: UNTOUCHED
merge: FORBIDDEN WITHOUT EXPLICIT USER COMMAND
```

## CURRENT STATE

```text
issue: #42 / OPEN
PR: PENDING
review state: DRAFT IMPLEMENTATION
runtime: NOT DEPLOYED
acceptance: NOT STARTED
```
