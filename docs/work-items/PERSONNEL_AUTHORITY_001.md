# PERSONNEL-AUTHORITY-001 — execution package

**Issue:** #42

**PR:** #43

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

Существовали и переиспользованы:

- `Organization`, `Division`, `Workplace`, `OperationalArea`, `Position`, `Employee`;
- `EmployeeQualification`;
- `OperationalRightDefinition` и импортируемый `EmployeeOperationalRight`;
- `RoleAssignment`, `ResponsibilityScope`, `Substitution` как отдельный application foundation;
- `EmployeeEnergySiteAuthorization`;
- controlled personnel importer и provenance;
- `LegalModeDecision`, `EvidenceEvent`, canonical JSON, SHA-256 и actor snapshot;
- read-only personnel directory и employee card.

Доказанные initial gaps:

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
7. Свободный русский текст квалификации не превращается автоматически в технический authority code.
8. Snapshot содержит факты решения, но не password/token/secret.
9. Authority result не является юридическим заключением и не заменяет evidence event предметного действия.

## IMPLEMENTED SLICE 1 — PURE CONTRACT

```text
src/apps/organizations/authority.py
src/apps/organizations/tests/test_authority_contract.py
```

Реализованы pure facts, structured scopes, stable reason codes, deterministic `evaluate_authority()`, timezone validity, deep immutable snapshot, secret guard и digest через принятый normative-evidence primitive.

Exact-head gate:

```text
0200a2be6dfc5e948eb27dbed77d9e2aa39c0d4d
5 / 5 workflows SUCCESS
```

## IMPLEMENTED SLICE 2 — PERSISTENCE AND ORM SERVICE

```text
src/apps/organizations/authority_models.py
src/apps/organizations/authority_services.py
src/apps/organizations/apps.py
src/apps/organizations/migrations/0008_personnel_authority_persistence.py
src/apps/organizations/tests/test_authority_persistence.py
src/apps/organizations/tests/test_authority_qualification_codes.py
```

Persistence:

- `OperationalAuthorityGrant`;
- `ExternalPersonnelEngagement`;
- `OperationalAuthoritySubstitution` linked to existing `Substitution`;
- append-only `AuthorityEvaluationRecord` with correction link;
- DB constraints for validity, uniqueness and cross-organization boundaries;
- update/delete protection for snapshots;
- ORM-backed `evaluate_and_record_authority()` reusing the pure evaluator.

Critical repair: only controlled ASCII catalog values become technical qualification codes. Russian prose remains descriptive data and cannot silently satisfy action requirements.

Exact-head gate:

```text
4c65f3ab1d6631fa661c9ffba94443620a30e71a
5 / 5 workflows SUCCESS
full PostgreSQL suite SUCCESS
```

## IMPLEMENTED SLICE 3 — READ-ONLY ACCEPTANCE UI

Routes:

```text
/organization/authorities/
/organization/employees/<uuid>/
/organization/authority-evaluations/<uuid>/
```

Views show:

- structured grants separately from imported positive source markers;
- scope, validity, granting organization, basis and status;
- external personnel home/host relationship;
- action-time history with `ALLOW / DENY / VERIFY` and reason codes;
- exact immutable snapshot and SHA-256 digest;
- empty states without fake lifecycle or write controls.

Tests verify authentication, read-only boundary, source-fact/grant distinction and evaluation details.

## PRESENTATION DATA

```text
src/apps/organizations/management/commands/seed_demo_personnel_authority.py
src/apps/organizations/migrations/0009_seed_demo_personnel_authority.py
src/apps/organizations/tests/test_authority_seed_command.py
```

- management command is idempotent;
- reversible conditional data migration runs only when `Organization(code="DEMO")` already exists; otherwise no-op;
- migration path itself is executed by tests against a populated synthetic Demo database;
- four synthetic `DEMO-ONLY` grants/evaluations demonstrate `ALLOW`, `DENY`, `VERIFY` and external contractor `ALLOW`;
- no real persons, local acts, production authority matrix or sensitive source file enters Git.

## ALLOWED BOUNDARY

See issue #42. Current changed-file boundary remains within organizations authority contract/persistence/routes/templates/tests, focused presentation seed and canonical coordination documentation.

## PROTECTED BOUNDARY

- OPJ/SHIFT/DEFECT/work-permit/switching lifecycle;
- master-data/import redesign;
- historical imported facts;
- real personal data/local acts;
- second signature/hash/authentication framework;
- preview;
- Ready for Review and merge without explicit user command.

## RISK / DELIVERY

```text
change class: STANDARD
schema/data risk: SCHEMA_DATA
delivery profile: FULL_DEVELOPMENT
preview: UNTOUCHED
merge: FORBIDDEN WITHOUT EXPLICIT USER COMMAND
```

## REMAINING GATE

1. Complete final exact-head five-workflow gate after documentation sync.
2. Trigger trusted `vps-development-rebuild` only on that exact head.
3. Verify transactional migration, populated read-only routes and controller exact SHA.
4. Hand the development candidate to the user for acceptance.
5. Keep PR Draft; do not merge or mark Ready without a separate command.

## CURRENT STATE

```text
issue: #42 / OPEN
PR: #43 / OPEN / DRAFT / NOT MERGED
review state: IMPLEMENTATION CANDIDATE
runtime: NOT YET DEPLOYED ON FINAL HEAD
acceptance: NOT STARTED
preview: UNTOUCHED
```
