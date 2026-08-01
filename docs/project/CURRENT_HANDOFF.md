# Chat 0 — current handoff navigator

This file is a stable navigation page. It does not own or repeat current SHA, issue, branch, pull-request, runtime or preview values.

## Authoritative entry points

1. Volatile project state: [`CURRENT_STATE.md`](CURRENT_STATE.md).
2. Release/module/capability planning state: [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml).
3. Dependency order and work-item queue: [`../product/IMPLEMENTATION_SEQUENCE.md`](../product/IMPLEMENTATION_SEQUENCE.md).
4. Global derived checklist: [`DEMO_RELEASE_MASTER_CHECKLIST.md`](DEMO_RELEASE_MASTER_CHECKLIST.md).
5. Canonical documentation index: [`../INDEX.md`](../INDEX.md).
6. Development process: [`../process/DEVELOPMENT_WORKFLOW.md`](../process/DEVELOPMENT_WORKFLOW.md).
7. Process hardening contract: [`../process/PROCESS_HARDENING.md`](../process/PROCESS_HARDENING.md).

## Reading rule

Always read `CURRENT_STATE.md` immediately before acting. GitHub state remains stronger than documentation, and a new commit invalidates earlier exact-head workflow evidence.

Use the release plan and its derived views for module scope, dependencies, capabilities and acceptance. Do not infer current coordination state from historical records, release notes, branch names or this navigator.

## Change rule

Update volatile facts only in `CURRENT_STATE.md`. Update release/module planning facts in `DEMO_RELEASE_PLAN.yaml` and regenerate or verify its human-readable views. Keep this page limited to navigation.
