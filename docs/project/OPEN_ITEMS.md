# ЭОД — открытые вопросы и отложенные задачи

**Актуализировано:** 26.07.2026

## 1. Текущий work item — DEFECT-001

```text
branch:
feature/defect-001-equipment-defect-journal

Draft PR:
#16

status:
IMPLEMENTATION IN PROGRESS / NOT DEPLOYED / NOT ACCEPTED

base main:
b75db8bc073e4b02a3254512e9b99d00f3e6e0e2

preview:
UNTOUCHED
```

Implemented in branch:

- exact source-bound type and immutable published revision;
- source trace to И-00-007-ОР-2025 version 2, section 11, appendix 8;
- exact six-column registry and browser-print representation;
- mandatory structured equipment relation and dispatcher-name snapshot;
- separate registered user and person who discovered the defect;
- roles, guarded lifecycle and terminal lock;
- separate deadline extension with previous/new deadline and immutable evidence;
- acknowledgement before close;
- explicit immutable operational-log entry relation;
- minimum non-cloning volume contract;
- dedicated UI and generic-route guard;
- deterministic five-state presentation data;
- focused tests and PostgreSQL concurrency test;
- canonical documentation for the active slice.

Still open before product acceptance:

1. stable final exact head;
2. Ruff/compile/Django/migration checks;
3. focused source-bound test pass;
4. one full PostgreSQL suite on final exact head;
5. all five exact-head workflows green;
6. trusted `vps-development-refresh` deployment;
7. exact-SHA controller evidence and healthy development runtime;
8. preview proof remains `UNTOUCHED`;
9. user product and visual review;
10. separate explicit merge command.

The user performs no VPS commands, test runs, log collection, patch application or
configuration edits.

## 2. DEFECT-001 acceptance risks to verify

- published schema remains exactly source-bound and immutable;
- no generic create/edit/transition bypass exists;
- equipment link cannot be omitted;
- `created_by` and `DISCOVERED_BY` remain independent;
- deadline extension never silently replaces history;
- close cannot bypass resolution and acknowledgement;
- terminal record cannot be changed or physically deleted;
- cross-organization equipment/person/log relations are rejected;
- action snapshot and SHA-256 remain consistent;
- new volume never clones or moves unresolved records;
- old volume end date equals resolution date of the last unresolved defect;
- print view has exactly the six approved columns and no technical fields;
- presentation reset remains deterministic and idempotent;
- UI states clearly that the contour does not replace the mandatory paper original
  and does not claim УКЭП.

## 3. Operational Journal

Blocking lifecycle gaps outside DEFECT-001:

- draft → immutable registered entry;
- handover preparation;
- сдача/приёмка;
- close shift;
- unfinished draft checks;
- signatures/action evidence.

Editor/stability backlog:

- caret at end;
- Ctrl+Left/Right/Home/End within entry;
- PgUp/PgDown without page scroll;
- editable semantic links;
- no duplicated marker on copy/paste;
- no page jump outside sheet;
- templates, abbreviations and suggestions.

DEFECT-001 uses only registered entries as an optional basis and does not expand
these unfinished lifecycles.

## 4. Data

Open after the active slice:

- publish accepted canonical power-system dataset;
- distinguish staging from publication;
- personnel rights and qualifications;
- personnel/workplace source publications;
- unified deterministic presentation reset beyond the defect slice;
- managed RU→EN domain lexicon;
- preserve common ЩПТ/ШОТ equipment family.

## 5. Structured Journals

After DEFECT-001 acceptance and merge decision:

- Application Journal;
- Disposition Journal;
- Equipment Commissioning;
- RZA/Telemechanics;
- work journals after normative decision.

Each requires source traceability, specialized rules, dedicated UI, links,
presentation data, automated gates and user acceptance. A generic registry alone is
not a completed journal.

## 6. Work permits and orders

Open normative/product questions:

- original mode;
- separate work journals;
- target briefings;
- primary/daily admission;
- crew changes;
- workplace transfers;
- suspension/resumption;
- completion/closure/storage;
- signatures/action evidence;
- current-operation work lists.

## 7. Switching

Minimum contour remains open:

- registry/card;
- types/statuses;
- equipment;
- application/disposition basis;
- executor/controller;
- dates/file;
- operational-log link;
- manual operation sequence.

Automatic generation/topology/interlocks remain later.

## 8. Keys journal

Paper-first:

- paper remains working original;
- full electronic issue/return lifecycle is not mandatory;
- optional reference/control contour requires separate decision.

## 9. UX-001

Still provisional:

- visual acceptance pending;
- accepted tokens absent;
- DEFECT-001 is the first real structured-journal reference implementation;
- product correctness takes priority over cosmetic parallel work.

## 10. Infrastructure

AUTO-001A/B are accepted. Only evidence-driven follow-ups remain open:

- credential rotation/revoke procedure;
- stale-lock recovery evidence;
- artifact retention;
- backup policy for future migration-heavy product slices;
- browser automation after product scenarios stabilize.

DEFECT-001 does not create a new controller, gateway, workflow or automation layer.
Automatic merge and preview write remain forbidden.
