# PROJECT-STATE-RECONCILIATION-001 — каноническое состояние и защита от drift

## Ownership

Volatile coordination belongs only to
[`CURRENT_STATE.md`](../../../project/CURRENT_STATE.md). This work-item contract
does not repeat current SHA, issue, PR, branch, runtime or Preview values.

Planning status belongs to
[`DEMO_RELEASE_PLAN.yaml`](../../../project/DEMO_RELEASE_PLAN.yaml).
Industrialization phases/dependencies/gates are defined by
[`INDUSTRIALIZATION_PROGRAM.yaml`](../../../project/INDUSTRIALIZATION_PROGRAM.yaml).

## Goal

Restore factual canonical state after accepted `PROJECT-SUSTAINABILITY-001` and
make future documentation/planning drift fail closed. This is Phase 0 work and a
mandatory `SAFE-CONTINUATION` dependency.

## Implemented factual reconciliation

GitHub history was reconciled for accepted and active contours, including:

- `MASTER-DATA-ALIGNMENT-001`;
- `NORMATIVE-EVIDENCE-001`;
- `PERSONNEL-AUTHORITY-001`;
- `OPJ-LIFECYCLE-001`;
- `PROJECT-SUSTAINABILITY-001`;
- current `PROJECT-STATE-RECONCILIATION-001`.

Accepted candidate/final heads and merge commits are retained in the canonical
planning evidence and historical ledgers. Where a PR had a user-accepted
candidate followed by synchronization, both heads are preserved instead of
being collapsed.

## Implemented ownership model

- `CURRENT_STATE.md` — only volatile project-state owner.
- `DEMO_RELEASE_PLAN.yaml` — only release/module/capability/work-item status
  owner.
- `INDUSTRIALIZATION_PROGRAM.yaml` — accepted definition of 8 phases, 30 work
  items, dependencies, risks and gate boundaries; no current status ownership.
- `CURRENT_HANDOFF.md` — navigation only.
- `MODULE_MAP.md`, `IMPLEMENTATION_SEQUENCE.md`,
  `DEMO_RELEASE_MASTER_CHECKLIST.md` and `INDUSTRIALIZATION_PROGRAM.md` —
  deterministic generated views.
- baseline/acceptance histories — event ledgers, never current-state owners.

## Permanent validator

The Documentation Contract now rejects:

1. duplicate work-item IDs;
2. missing module/work-item references;
3. risk-register `proposed_work_item` references that do not resolve;
4. dependencies on absent work items;
5. normal dependencies on later phases;
6. missing gate work items;
7. direct or transitive `PILOT-READY` mandatory-core dependencies outside core;
8. hidden mandatory dependencies on scope-dependent work items;
9. stale accepted module/work-item status;
10. accepted work items retained in execution queue;
11. duplicate owner-style volatile fields;
12. Markdown/program projection drift;
13. stale generated module map, sequence, checklist or program human view;
14. active work item whose planning status is not `IN_PROGRESS`.

Every contract diagnostic includes file, identifier, rule, expected and actual.

## Fail-closed fixture catalog

`tests/process/fixtures/documentation_state_contract.json` contains:

- positive baseline;
- missing work-item reference;
- duplicate work-item ID;
- dependency on absent work item;
- mandatory-core dependency outside core;
- hidden dependency on scope-dependent work item;
- reverse interphase dependency;
- missing gate work item;
- stale accepted status;
- duplicate volatile owner;
- Markdown/YAML projection mismatch;
- stale derived view.

## Preserved boundaries

No product code, Django models, migrations, data, runtime, Compose, VPS or
Preview changes are allowed or included. The work item does not implement module
activation/registry, does not start `SHIFT-HANDOVER-001`, does not create new
journals/modules and does not change accepted `SAFE-CONTINUATION` or
`PILOT-READY` boundaries.

The Demo subject scope remains unchanged. The product queue is only marked
paused pending `SAFE-CONTINUATION` and a separate explicit owner decision.

## Validation profile

`DOCS / GOVERNANCE / DOCUMENTATION_AUTOMATION`

Required before user acceptance:

- compile updated validators/tests;
- full positive and negative fixture suite;
- Documentation Contract;
- all applicable exact-head workflows;
- final changed-file boundary review;
- confirmation of no product/runtime/schema/data diff;
- PR body with exact-head run IDs;
- PR remains Draft.

## Stop condition

Stop on user acceptance. Do not move PR to Ready for Review and do not merge
without a separate explicit command.
