# ЭОД — текущее состояние

**Дата factual check:** 01.08.2026  
**Единственный владелец:** accepted main SHA, active work item/issue/PR/branch и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 49964f2dcaf7e4659a99a240dcd899d42a7dfe15
active work item: PROCESS-GATE-STATE-001
active issue: #38
active PR: #39 / OPEN / DRAFT / NOT MERGED
active branch: repair/process-gate-state-001
runtime impact: NONE
preview: UNTOUCHED
```

`PROCESS-GATE-STATE-001` is a bounded process/CI repair. It corrects canonical state ownership and removes historical coordination markers from architectural gates. It does not change application code, models, migrations, templates, static assets, runtime, schema or data.

Product PR #35 (`MASTER-DATA-ALIGNMENT-001`) remains open and Draft at its existing product head. It is a blocked dependent PR, not a source of truth for this repair and is not modified here.

Release/module/capability/work-item planning state remains owned by [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation without duplicated volatile values remains in [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).

After this repair is accepted and merged, the post-merge coordination update must record the new accepted main and return the active work item to PR #35 before its exact-head workflows are rerun.
