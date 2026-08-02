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
2. точное условие, пункт и источник для каждого conditional right;
3. ручное создание, редактирование и деактивация карточек;
4. ручное создание недостающих подразделений, должностей и рабочих мест;
5. controlled XLSX preview/publish для штатной матрицы и внешних списков;
6. separate dispatcher/operational/CUS/related-site/commercial/contractor
   semantics;
7. immutable history и action-time authority evaluation;
8. Direction A management workspace `/organization/`.

## FACTUAL START AND ACCEPTED CORRECTIONS

Переиспользованы `Organization`, hierarchical `Division`, `Workplace`,
`Employee`, `EmployeeQualification`, `OperationalRightDefinition`,
`EmployeeOperationalRight`, operational reporting lines, energy-site service,
personnel importer provenance, role/substitution foundation и
normative-evidence canonical JSON/SHA-256.

Первый candidate был отклонён как technical grant list. Матричный candidate был
принят по концепции и общей композиции, после чего пользователь потребовал:

- выровнять и сделать читаемыми заголовки матрицы;
- заменить дешёвую раскрывающуюся легенду встроенной цветовой легендой под
  деревом;
- использовать semantic icons для руководства, оперативного персонала, ТОиР,
  РЗА, ВЭУ, подстанций и технических подразделений;
- показывать точное условие, а не только «предоставлено с условием»;
- добавить РЗА и внешние оперативные справочники по структуре предоставленных
  списков;
- заменить старую technical `/organization/` полноценным Direction A workspace;
- устранить пустые dropdowns в одиночном добавлении;
- применить canonical interface typography ко всем Direction A screens.

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

## MATRIX AND CONDITION REPAIR

```text
src/apps/organizations/personnel_reference_models.py
src/apps/organizations/personnel_reference_signals.py
src/apps/organizations/migrations/0013_operational_right_condition_detail.py
src/apps/organizations/authority_views.py
src/templates/organizations/authority_registry.html
src/templates/organizations/employee_detail.html
src/templates/organizations/_external_operational_contacts.html
src/static/organizations/personnel_authority_repair.css
src/static/organizations/personnel_authority_matrix.js
src/static/system/icons.svg
```

Implemented:

- `OperationalRightConditionDetail` one-to-one with published source right;
- exact title, description, source clause and source reference;
- `+1` → paragraph 5.4 and `+2` → paragraph 5.13 of the Rules approved by
  Ministry of Labor order 15.12.2020 No. 903н;
- unknown index must contain exact user-entered text/source or remains explicit
  unresolved/VERIFY;
- condition tooltip from the matrix cell;
- full condition block in «Кто имеет право» and employee card;
- aligned 38/152 px grouped/right headers and consistent column geometry;
- integrated colored legend under the organization tree;
- colored categories АТП / ОП / ОРП / РП / АТП-ОП;
- semantic organization icons;
- RZA chips and explicit electrical-safety wording;
- tabs for ODU/RDU, CUS/related sites, contractors and checks.

## EXTERNAL DIRECTORIES AND RZA DEMO

```text
src/apps/organizations/migrations/0014_seed_demo_external_operational_directories.py
src/apps/organizations/migrations/0015_stabilize_demo_external_directory_codes.py
```

Conditional synthetic demo data only when `Organization(code="DEMO")` exists:

- ODU South;
- North Caucasus RDU;
- North Caucasus PMES and CUS;
- 500 kV Nevinnomyssk substation;
- commercial wind-farm dispatch center;
- management, dispatchers, CUS and related-site operational personnel;
- contacts, schedules, operational scope, authority summary, validity and basis;
- RZA categories III/IV for synthetic штатный employees.

No real names, phones, local acts or source workbooks are committed.

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
- exact condition editing for conditional rights;
- organization profiles for own/DC/grid/site/commercial/contractor contours;
- external operational roles: dispatcher, operational, management, CUS,
  commercial dispatcher and related-site personnel;
- two downloadable XLSX templates;
- SHA-256 duplicate-file detection;
- parse/validate/preview with CREATE/UPDATE/error;
- duplicate match by personnel number and exact name inside source organization;
- individual and group/block selection before publication;
- explicit publish with per-card immutable change records;
- absence from a new file never deactivates an existing card automatically;
- existing dropdown values are populated for selected/default organization;
- missing division/position/workplace can be created in the employee form with
  deterministic internal codes.

## ORGANIZATION WORKSPACE AND TYPOGRAPHY

```text
src/apps/organizations/views.py
src/templates/organizations/directory.html
src/static/organizations/personnel_directory.css
src/static/system/eod_typography.css
src/templates/shared/direction_a/base.html
```

`/organization/` now provides:

- organization contour cards;
- hierarchy and separate division status;
- center leadership;
- employee/contact/qualification/right table;
- immediate operational reporting lines kept separate from administrative tree;
- energy sites and servicing divisions, including accepted demo relations for
  Kuzminskaya wind farm and Barsuki 330 kV substation;
- external operational contacts;
- recent imports and immutable changes.

The canonical Direction A font stack is applied across navigation, forms,
tables and controls. Code/audit remains monospace; operational-journal document
font remains controlled by its own print/editor preference.

## TEST CONTRACT

Tests prove:

- hierarchy and matrix render in Direction A shell;
- source cell is a granted right and conditional marker produces `VERIFY`;
- exact `+1/+2` condition, clause and source render in all user views;
- integrated category legend and semantic organization icon render;
- RZA category/scope render in matrix and employee card;
- ODU/RDU directory is separate from contractor engagement;
- `/organization/` is a management workspace while preserving reporting lines,
  separate divisions and site-service relations;
- manual create persists contacts and immutable audit;
- manual creation of division/position/workplace works without empty selects;
- editing moves the existing card without duplication;
- right edit closes old revision and creates linked evaluator grant/condition;
- XLSX template → preview → selected publish creates qualification/right/grant;
- empty errors and boundary snapshots are valid structured values;
- seed/import are idempotent where required;
- anonymous access is rejected;
- no real data enter the acceptance UI or Git.

Latest proven pre-coordination repair head:

```text
41bb2c1ba99decedf19fbc22dd2f25eed187dd2d
664 Django/PostgreSQL tests / OK / skipped=1
5 mandatory workflows / SUCCESS
migrations 0013, 0014, 0015 / APPLIED IN CI
container stack and preview smoke / SUCCESS
```

## PROTECTED BOUNDARY

- no OPJ/SHIFT/DEFECT/work-permit/switching lifecycle integration;
- no automatic direct import of arbitrary production workbook layout;
- no real personal data or local acts in Git;
- no automatic publication of every person in a broad external source;
- no automatic deactivation of omitted people;
- no invented condition text;
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
review state: ACCEPTANCE REPAIR FINAL VALIDATION
runtime: PREVIOUS MANAGEMENT CANDIDATE d141313a ON DEVELOPMENT
repair candidate: EXACT-HEAD GATE REQUIRED AFTER COORDINATION DOCS
acceptance: PENDING NEW REPAIR CANDIDATE
preview: UNTOUCHED
```
