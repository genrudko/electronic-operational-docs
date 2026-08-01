# PROCESS-GATE-STATE-001 — canonical state and gate repair

## Identity

- Issue: #38
- Branch: `repair/process-gate-state-001`
- Starting main: `49964f2dcaf7e4659a99a240dcd899d42a7dfe15`
- Change class: `STANDARD`
- Risk profile: `SECURITY_INFRA`
- Delivery: `NONE`

## Factual defect

Three workflows on Draft PR #35 stop before their intended checks because current gates require an historical accepted-main SHA and the completed `PROJECT-BASELINE-001` marker. The documentation checker also masks duplicate volatile state instead of enforcing the canonical owner model.

The accepted ownership model is:

- `docs/project/CURRENT_STATE.md` owns current accepted main, active work and runtime facts;
- `docs/project/DEMO_RELEASE_PLAN.yaml` owns release/module/capability planning data;
- `docs/project/CURRENT_HANDOFF.md` is navigation only.

## Scope

1. Add one reusable current-state contract.
2. Remove historical coordination markers from the Patch 011.7 gate while preserving its product invariants.
3. Enforce ownership directly in documentation validation.
4. Keep the handoff navigation-only.
5. Add focused regression tests.

## Protected boundary

No application code, models, migrations, templates, static assets, runtime, schema, data, deployment, preview or PR #35 product changes.

## Test plan

```text
python -m ruff check scripts tests/process
python -m compileall -q scripts tests/process
python -m unittest discover -s tests/process -p 'test_project_state_contract.py'
python scripts/check_documentation_contract.py
python scripts/gate_patch_011_7.py
```

## Verdict

`READY TO IMPLEMENT`
