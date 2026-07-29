# ЭОД — roadmap

**Актуализировано:** 29.07.2026

## 1. Принцип

Roadmap управляется:

- фактическим GitHub state;
- runtime evidence;
- user acceptance;
- демонстрационными сценариями;
- нормативными и исследовательскими decisions.

Research observation не становится requirement автоматически. Green CI не завершает product work без user acceptance.

## 2. Current baseline

```text
accepted UX/application merge:
a880a632b750309c7fbfb918af15b49d99b5a93f

last accepted product/UX work:
UX-FOUNDATION-001 / PR #23 / MERGED / ACCEPTED

active work:
OPJ-UX-001 / issue #24 / Draft PR #25

active candidate:
663086c9c0b0dfa0d4e970185f0f52269be20a61

preview:
UNTOUCHED
```

## 3. Завершено

| Work item | Статус | Результат |
|---|---|---|
| INFRA-001–003 | Accepted | Linux/PostgreSQL, preview, isolated development |
| DOCS-001–003 | Accepted | Canonical project operating system |
| QUALITY-001 | Accepted | Full Django test discovery |
| AUTO-000 | Accepted | Automation/security/acceptance contract |
| AUTO-001A/B | Accepted | Trusted exact-SHA development controller |
| DEV-FAST-001 | Accepted | Templates/static hot refresh |
| PLAN-001 | Accepted | Evidence audit and first vertical slice |
| DEFECT-001 | Accepted | Source-bound equipment defect journal |
| UX-FOUNDATION-001 | Accepted | Direction A and reference UX foundation |
| Vertical-products research 20260729 | Accepted as decision input | 27 sources and canonical decision matrix |

## 4. Active — OPJ-UX-001

Goal:

- second real Direction A consumer;
- shared system layer;
- unified same-purpose elements across home, defect and OPJ;
- specialized operational journal workspace;
- no lifecycle expansion.

Exit criteria:

- one shared visual/interaction system;
- no copied independent `opj-da-*`;
- registry, registered journal and shift workspace aligned;
- editor/ribbon/three-column form preserved;
- desktop/mobile accepted;
- final exact-head gate;
- explicit merge command.

## 5. Short process optimization after OPJ acceptance

### CI-OPT-001

Remove proven duplication:

```text
GitHub exact-head full suite
→ trusted same-SHA deployment
→ VPS migrations/check/runtime smoke
```

No required check weakening.

### DEV-EVIDENCE-001

One machine-owned PR evidence summary and acceptance route.

### UI-CONTRACT-001

Shared UI source/browser contract:

- shared assets;
- real routes;
- desktop/mobile matrix;
- screenshot artifacts;
- smoke interactions;
- no second visual system.

Only `CI-OPT-001` is planned as the immediate short slice. The remaining items may be combined with the next product work if that is simpler.

## 6. Operational journal product sequence

### OPJ-LIFECYCLE-001

- draft → immutable registered entry;
- event time and registration time;
- source and author snapshots;
- correction/cancellation without rewriting original;
- exact audit and integrity.

### OPJ-ASSISTANCE-001

- templates;
- abbreviations;
- repeat/copy with validation;
- equipment/personnel/document insertion;
- context suggestions;
- operator confirmation before registration.

### SHIFT-HANDOVER-001

- preparation;
- report;
- active documents;
- unfinished actions;
- handing-over and receiving participants;
- repeat authentication/evidence according to accepted domain contract;
- result recorded in operational journal.

Exact order between assistance and handover may be changed by the demonstration scenario, but they remain separate work items.

## 7. Structured journals

### PRODUCT-D2 — applications

Critical path:

```text
equipment
→ requested state and interval
→ reason
→ participants
→ links
→ status/history
```

Must work without mandatory SCADA.

### PRODUCT-D3 — dispositions/orders

- document basis;
- executor;
- deadline;
- actual execution state;
- participant changes with history;
- derived work register;
- links to OPJ, application and work.

### Other structured journals

- equipment commissioning;
- RZA/TM only after `RZA-TM-RESEARCH`;
- keys as paper-first/reference until separate decision;
- grounding as independent future inventory+operation model;
- rounds as separate route/checkpoint vertical slice.

## 8. Permits and work

### PERMIT-AUTHORING-001

Critical path:

```text
copy/template
→ personnel and measures
→ validation
→ print preview
→ paper/PDF output
```

Goal: practical speed comparable with specialized authoring tools.

### PERMIT-LIFECYCLE-001

After normative decision:

- issue and preparation;
- instructions;
- admission;
- team changes;
- transfer;
- suspension/resume;
- completion/close/storage;
- evidence/signature mode.

Authoring and lifecycle are not merged into one oversized first slice.

## 9. Switching documents

### SWITCHING-DOCUMENTS-001

- registry/card;
- BP/TBP/program types;
- template/copy;
- structured numbered operations;
- versions;
- executor/controller;
- basis/equipment;
- print;
- manual review/approval.

### ENGINEERING-SWITCHING-LATER

- topology;
- actual scheme state;
- interlocks;
- RZA logic;
- automatic sequence generation.

The engineering contour is not part of the internal prototype.

## 10. Cross-document development

Future:

- `CROSS-DOCUMENT-ACTIONS-001`;
- linked-document timeline;
- task/source/deadline/executor/shift;
- derived reports;
- no duplicate manual databases.

## 11. Deferred

- `ROUNDS-001`;
- `GROUNDING-001`;
- `OFFLINE-001`;
- `SCADA-INTEGRATION`;
- automatic BP/TBP/TPP generation;
- full legal electronic signature;
- industrial HA/replication;
- `HOST-MOVE-001` after current hosting period.

## 12. Internal prototype exit

- coherent Direction A across main routes;
- operational journal UX and registration lifecycle;
- shift handover;
- applications and dispositions;
- accepted defect flow;
- permit authoring minimum;
- switching document minimum;
- cross-document links;
- deterministic presentation data;
- 6–8 scenarios;
- one final regression/acceptance gate;
- honest paper/hybrid limitations.

## 13. Development process rule

```text
micro-repair
→ focused checks
→ hot refresh
→ acceptance

final head
→ one full final gate
→ explicit merge
```

Complex automation is added only after measurement of a real bottleneck.
