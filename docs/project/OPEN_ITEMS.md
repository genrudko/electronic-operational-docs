# ЭОД — открытые вопросы и отложенные задачи

**Актуализировано:** 29.07.2026

## 1. Current active work

```text
work item:
OPJ-UX-001

issue:
#24

Draft PR:
#25

branch:
ux/opj-ux-001

candidate head:
663086c9c0b0dfa0d4e970185f0f52269be20a61

state:
OPEN / DRAFT / NOT MERGED

preview:
UNTOUCHED
```

Current blocker: отсутствует. Ожидается пользовательская desktop/mobile приёмка и repairs в том же PR.

## 2. OPJ-UX-001 acceptance

Проверить:

- одинаковый shell на home/defect/OPJ;
- единые page headers, buttons, fields, tabs, panels and status language;
- registry and registered form;
- shift workspace;
- editor/ribbon/focus/keyboard;
- hierarchy selectors;
- mobile without two-page imitation;
- overlays within viewport;
- no regression of accepted defect UX.

Не добавлять:

- draft registration;
- handover/close endpoints;
- false lifecycle controls;
- templates/abbreviations;
- automatic events;
- offline/SCADA.

## 3. Shared UX/UI

Canonical:

```text
docs/project/PRODUCT_UX_PRINCIPLES.md
```

Open implementation debt after PR #25:

- confirm all accepted defect routes consume shared system assets;
- eliminate remaining visual-only feature duplication when a second consumer exists;
- create `UI-CONTRACT-001`;
- define stable browser fixture/route matrix;
- decide when screenshot comparison becomes blocking;
- measure visual test flaky rate before pixel-perfect gate.

Rule: no new independent module design system.

## 4. Research decisions

Canonical traceability:

```text
docs/research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv
```

### Accepted principles

- best-of-breed critical path;
- authoring vs lifecycle;
- derived registers, not duplicate databases;
- separate shift handover;
- separate rounds;
- optional SCADA boundary;
- history instead of overwrite;
- acknowledgement/instruction/knowledge/signature separation.

### VERIFY

- electronic signature modes;
- exact work-order lifecycle;
- automatic BP/TBP/TPP;
- RZA/TM model;
- grounding location model;
- legal status of two-sided key confirmation.

### DEFER

- offline;
- rounds implementation;
- SCADA integration;
- engineering switching;
- action-management layer.

## 5. Development optimization

Canonical:

```text
docs/process/DEVELOPMENT_ACCELERATION.md
```

### Immediate process rules

- one PR per work item;
- focused checks for micro-repair;
- hot refresh for allowed templates/static;
- one full final gate;
- failure-only diagnostics;
- user manual commands target `0`.

### CI-OPT-001 — next short process slice

Open questions:

- which exact CI run is source of full-suite trust;
- how controller proves same SHA/environment;
- which VPS smoke replaces repeated full suite;
- whether migration/data changes require mandatory VPS full tests;
- path/risk profile selection;
- documentation/required-check impact.

Must not weaken required checks or exact-SHA security.

### DEV-EVIDENCE-001

- one machine-owned PR comment;
- run IDs;
- test count;
- migrations;
- deployed SHA;
- rollback;
- DB operations;
- preview state;
- acceptance URL.

### WORKITEM-BOOTSTRAP-001

- small manifest;
- issue/branch/PR/checklist;
- risk profile;
- test groups;
- protected boundaries.

Must not generate domain decisions.

## 6. Operational journal product gaps

### OPJ-LIFECYCLE-001

- connect draft to immutable registration;
- event/registration times;
- source type;
- correction/cancellation;
- links and integrity;
- tests/routes/services.

### OPJ-ASSISTANCE-001

- templates;
- abbreviations;
- suggestions;
- copy/repeat validation;
- minimal typing;
- no interference with manual entry.

### SHIFT-HANDOVER-001

- preparation;
- report;
- active documents;
- unfinished actions;
- both sides;
- roles/evidence;
- close semantics.

## 7. Applications and dispositions

### PRODUCT-D2

Open:

- source-bound form;
- statuses;
- requested/factual intervals;
- equipment state;
- conflict presentation;
- roles;
- OPJ/disposition/switching links.

### PRODUCT-D3

Open:

- document vs fact of execution;
- participant changes;
- deadlines;
- history;
- work register as derived view;
- links.

## 8. Permits and works

### PERMIT-AUTHORING-001

- copy/template;
- personnel eligibility;
- standard measures;
- print preview;
- paper/PDF;
- benchmark against narrow authoring tools.

### PERMIT-LIFECYCLE-001

Blocked by normative/domain decisions:

- signature/evidence modes;
- instructions;
- admission;
- daily admission;
- team changes;
- transfer;
- suspension/resume;
- close/storage.

## 9. Switching

### SWITCHING-DOCUMENTS-001

- registry/card;
- type/status;
- structured operation sequence;
- versions;
- equipment/basis;
- executor/controller;
- print.

### Deferred engineering contour

- topology;
- interlocks;
- RZA;
- automatic generation;
- scheme state.

## 10. Data

Open:

- canonical published power-system dataset;
- personnel rights/qualifications;
- workplace and document publications;
- managed RU→EN domain lexicon;
- deterministic presentation scenarios beyond defect;
- preserve common ЩПТ/ШОТ family.

## 11. Hosting

`HOST-MOVE-001` after current paid period:

- select provider;
- reproducible Ubuntu/Docker/PostgreSQL bootstrap;
- restore backup;
- controller activation;
- GitHub Actions connectivity;
- dev/preview isolation;
- DNS/HTTPS if required;
- keep old VPS as rollback window.

Repeated current-host outages are documented operational risk.

## 12. Non-negotiable boundaries

- GitHub is source of truth;
- preview is not development;
- development is not `main`;
- automatic merge prohibited;
- user does not program or orchestrate normal deployment;
- same-purpose UI uses shared contract;
- research is not automatic requirement;
- full gate once on final head;
- no claim without evidence.
