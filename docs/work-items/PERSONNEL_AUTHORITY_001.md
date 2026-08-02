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

Довести существующий personnel foundation до bounded-контура оперативных
полномочий:

1. опубликованная матрица штатного персонала с иерархией подразделений;
2. structured right: лицо + право/action + scope + validity + basis + condition;
3. server-side authority-at-action evaluation;
4. отдельные external/seconded/contractor и substitution semantics;
5. immutable snapshot фактов, использованных при решении.

## FACTUAL START

Переиспользованы `Organization`, hierarchical `Division`, `Workplace`,
`Employee`, `EmployeeQualification`, `OperationalRightDefinition`,
`EmployeeOperationalRight`, personnel importer provenance, role/substitution
foundation и normative-evidence canonical JSON/SHA-256.

Исходный implementation candidate ошибочно показывал плоский список evaluator
grants и трактовал импортную отметку только как вспомогательный source fact.
Пользовательская приёмка выявила, что утверждённый список лиц с предоставлением
прав является матрицей, которой в эксплуатации пользуются одновременно для
просмотра полного профиля сотрудника, поиска всех лиц с конкретным правом и
сравнения подразделений.

## ACCEPTED DOMAIN CORRECTION

Для утверждённой действующей редакции:

- положительная ячейка сама является предоставленным правом;
- `+1`, `+2`, `+3` сохраняют право, но добавляют обязательное условие;
- `EmployeeOperationalRight` является published authority fact;
- `OperationalAuthorityGrant` создаётся как связанная машинная проекция для
  evaluator, а не как второе ручное назначение;
- внешний персонал остаётся отдельным контуром.

## IMPLEMENTED DOMAIN FOUNDATION

Pure contract and persistence remain in:

```text
src/apps/organizations/authority.py
src/apps/organizations/authority_models.py
src/apps/organizations/authority_services.py
src/apps/organizations/migrations/0008_personnel_authority_persistence.py
```

Guarantees:

- explainable `ALLOW / DENY / VERIFY`;
- exact action-time validity and scope;
- qualification check against actual actor;
- non-automatic bounded substitution;
- explicit external engagement;
- append-only snapshot and SHA-256 digest;
- no authorization by position or application role alone.

## MATRIX PUBLICATION SLICE

```text
src/apps/organizations/management/commands/seed_demo_personnel_authority.py
src/apps/organizations/migrations/0010_publish_demo_personnel_authority_matrix.py
src/apps/organizations/authority_views.py
src/templates/organizations/authority_registry.html
src/templates/organizations/employee_detail.html
src/static/organizations/personnel_authority_matrix.css
src/static/organizations/personnel_authority_matrix.js
src/static/organizations/personnel_authority_profile.css
```

The slice implements:

- 22 grouped right definitions corresponding to the approved matrix structure;
- 17 synthetic employees distributed through the existing organization tree;
- qualification for every employee;
- more than 100 positive cells with plain and conditional markers;
- one linked evaluator projection for every published source right;
- reversible conditional Demo migration;
- primary matrix view with sticky identity columns and grouped rights header;
- organization tree, collapse, subtree filter, search, personnel category and
  electrical-safety group filters;
- «Кто имеет право» view using the same tree and a right selector;
- complete employee profile grouped by right category;
- separate external personnel and action-time history views.

No real person, source workbook or local act is committed.

## TEST CONTRACT

Tests must prove:

- hierarchy and matrix render in Direction A shell;
- positive source cell is described as a granted right, not as a non-authorizing
  trace marker;
- conditional marker is visible and materialized as `VERIFY` basis;
- employee card contains qualification and full grouped rights profile;
- every synthetic source right has a linked evaluator projection;
- seed command and migration are idempotent;
- `ALLOW`, `DENY`, `VERIFY` and external `ALLOW` remain covered;
- anonymous access is rejected;
- no write controls or real data enter the acceptance UI.

## PROTECTED BOUNDARY

- no OPJ/SHIFT/DEFECT/work-permit/switching lifecycle integration;
- no production personnel import;
- no real personal data or local acts;
- no second signature/hash/authentication framework;
- preview remains `UNTOUCHED`;
- Ready for Review and merge require explicit user command.

## RISK / DELIVERY

```text
change class: STANDARD
schema/data risk: SCHEMA_DATA
delivery profile: FULL_DEVELOPMENT
preview: UNTOUCHED
merge: FORBIDDEN WITHOUT EXPLICIT USER COMMAND
```

## CURRENT STATE

```text
issue: #42 / OPEN
PR: #43 / OPEN / DRAFT / NOT MERGED
review state: MATRIX IMPLEMENTATION IN PROGRESS
runtime: PREVIOUS REJECTED CANDIDATE ON DEVELOPMENT
acceptance: PENDING NEW MATRIX CANDIDATE
preview: UNTOUCHED
```
