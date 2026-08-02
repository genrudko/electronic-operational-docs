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

Довести существующий personnel foundation до пользовательского bounded-контура:

1. опубликованная матрица штатного персонала с иерархией подразделений;
2. ручное создание, редактирование и деактивация карточек;
3. controlled XLSX preview/publish для штатной матрицы и внешних списков;
4. structured right: лицо + action + scope + validity + basis + condition;
5. отдельные dispatcher/operational/CUS/related-site/contractor semantics;
6. immutable history и action-time authority evaluation.

## FACTUAL START

Переиспользованы `Organization`, hierarchical `Division`, `Workplace`,
`Employee`, `EmployeeQualification`, `OperationalRightDefinition`,
`EmployeeOperationalRight`, personnel importer provenance, role/substitution
foundation и normative-evidence canonical JSON/SHA-256.

Первый candidate был отклонён как технический grant list. Второй matrix candidate
принят по концепции и оформлению, после чего пользователь потребовал полноценный
контур ведения данных: create/edit/deactivate, batch XLSX, легенду категорий,
явный тип группы по электробезопасности, специальные квалификации РЗА/высоты и
отдельные внешние оперативные справочники.

## ACCEPTED DOMAIN CORRECTION

- положительная ячейка утверждённой матрицы является предоставленным правом;
- `+1`, `+2`, `+3` сохраняют право и добавляют обязательное условие;
- `OperationalAuthorityGrant` — linked evaluator projection, а не второе ручное
  назначение;
- изменение опубликованного права/квалификации создаёт новую редакцию и закрывает
  предыдущую;
- физическое удаление карточки и истории запрещено;
- штатная матрица, внешний operational directory и contractor engagement — три
  разных контура.

## IMPLEMENTED DOMAIN FOUNDATION

```text
src/apps/organizations/authority.py
src/apps/organizations/authority_models.py
src/apps/organizations/authority_services.py
src/apps/organizations/migrations/0008_personnel_authority_persistence.py
```

Guarantees: explainable `ALLOW / DENY / VERIFY`, exact action-time validity and
scope, qualification of actual actor, bounded substitution, explicit external
engagement, append-only snapshot/digest and no authorization by position or app
role alone.

## MATRIX PUBLICATION SLICE

```text
src/apps/organizations/management/commands/seed_demo_personnel_authority.py
src/apps/organizations/migrations/0010_publish_demo_personnel_authority_matrix.py
src/apps/organizations/authority_views.py
src/templates/organizations/authority_registry.html
src/templates/organizations/employee_detail.html
src/static/organizations/personnel_authority_matrix.css
src/static/organizations/personnel_authority_readability.css
src/static/organizations/personnel_authority_matrix.js
src/static/organizations/personnel_authority_profile.css
```

Implemented: 22 grouped right definitions, 17 synthetic employees, more than 100
positive cells, linked projections, hierarchy tree, sticky matrix, readable
aligned headers, category legend, explicit «группа по электробезопасности»,
filters, «Кто имеет право», complete employee profile, external personnel and
action-time history.

## PERSONNEL MANAGEMENT SLICE

```text
src/apps/organizations/personnel_management_models.py
src/apps/organizations/personnel_management_services.py
src/apps/organizations/personnel_edit_services.py
src/apps/organizations/personnel_management_views.py
src/apps/organizations/migrations/0011_personnel_management.py
src/apps/organizations/migrations/0012_personnel_change_snapshot_blank.py
src/templates/organizations/employee_editor.html
src/templates/organizations/personnel_record_form.html
src/templates/organizations/organization_form.html
src/templates/organizations/personnel_import_upload.html
src/templates/organizations/personnel_import_detail.html
src/static/organizations/personnel_management.css
src/static/organizations/personnel_import_selection.js
src/static/organizations/personnel_import_selection.css
```

Implemented:

- manual create/edit of employee and contacts;
- moving an existing employee without duplication;
- deactivation instead of physical delete;
- versioned electrical qualification, RZA/height/special qualification and right;
- organization profiles for own/DC/grid/site/commercial/contractor contours;
- external operational roles: dispatcher, operational, management, CUS,
  commercial dispatcher and related-site personnel;
- two downloadable XLSX templates;
- SHA-256 duplicate-file detection;
- parse/validate/preview with CREATE/UPDATE/error;
- duplicate match by personnel number and exact name inside source organization;
- individual and group/block selection before publication;
- recommended external selection for dispatch/operational/management/CUS/
  Nevinnomyssk/commercial blocks;
- explicit publish with per-card immutable change records;
- absence from a new file never deactivates an existing card automatically.

No real person, contact, workbook or local act is committed.

## TEST CONTRACT

Tests prove:

- hierarchy and matrix render in Direction A shell;
- source cell is a granted right and conditional marker produces `VERIFY`;
- manual create persists contacts and immutable audit;
- editing moves the existing card without duplication;
- right edit closes the old revision and creates a linked evaluator grant;
- XLSX template → preview → selected publish creates qualification/right/grant;
- empty errors and boundary snapshots are valid structured values;
- seed/import are idempotent where required;
- anonymous access is rejected;
- no real data enter the acceptance UI or Git.

## PROTECTED BOUNDARY

- no OPJ/SHIFT/DEFECT/work-permit/switching lifecycle integration;
- no automatic direct import of arbitrary production workbook layout;
- no real personal data or local acts in Git;
- no automatic publication of every person in a broad external source;
- no automatic deactivation of omitted people;
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
review state: PERSONNEL MANAGEMENT CANDIDATE VALIDATION
runtime: PREVIOUS MATRIX CANDIDATE ON DEVELOPMENT
acceptance: PENDING NEW CREATE/EDIT/IMPORT CANDIDATE
preview: UNTOUCHED
```
