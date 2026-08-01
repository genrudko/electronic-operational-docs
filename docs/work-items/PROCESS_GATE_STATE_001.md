# PROCESS-GATE-STATE-001 — canonical state and gate repair

**Issue:** #38  
**Branch:** `repair/process-gate-state-001`  
**Starting main:** `49964f2dcaf7e4659a99a240dcd899d42a7dfe15`  
**Change class:** `STANDARD`  
**Risk profile:** `SECURITY_INFRA`  
**Delivery:** `NONE`

## FACT

Draft PR #35 at exact head `d59146638686e8c4602673e8e08041bd6fd1d916` passes Ruff, compile, Django check, migration consistency and PostgreSQL migrations, but three workflows stop before their intended checks.

Exact failures:

- `EOD CI` run `30707110803`, job `91388015388`, step `Run current architectural gate`;
- `EOD Documentation Contract` run `30707110808`, job `91388015330`, step `Validate documentation contract`;
- `AUTO-001B Controller CI` run `30707110799`, job `91388015193`, step `Run current architectural gate compatibility`.

The obsolete contract requires:

```text
accepted main baseline: main / 2a9b92362b90861501cf11d073668478655fd191
completed work item: PROJECT-BASELINE-001
```

The canonical ownership contract already states:

- `docs/project/CURRENT_STATE.md` owns volatile accepted main, active work item/PR and runtime state;
- `docs/project/DEMO_RELEASE_PLAN.yaml` owns release/module/capability/work-item planning state;
- `docs/project/CURRENT_HANDOFF.md` is navigation only.

The implementation contradicts that model through historical SHA/work-item hard-coding, synthetic legacy text and duplicated volatile state.

## SCOPE

1. Introduce one reusable, focused current-state contract.
2. Remove historical coordination markers from the Patch 011.7 architecture gate without removing its product invariants.
3. Make documentation validation enforce ownership instead of masking duplicate values.
4. Keep the handoff navigation-only.
5. Add focused regression tests proving current main and active Draft work are not tied to a historical work item.

## PROTECTED BOUNDARY

- no `src/apps/**` changes;
- no models, migrations, templates or static assets;
- no runtime, schema, data or deployment changes;
- no preview write;
- no changes to PR #35 product diff;
- no gate bypass and no automatic merge.

## TEST PLAN

```text
python -m ruff check scripts tests/process
python -m compileall -q scripts tests/process
python -m unittest discover -s tests/process -p 'test_project_state_contract.py'
python scripts/check_documentation_contract.py
python scripts/gate_patch_011_7.py
```

Then require exact-head success from the affected process workflows.

## VERDICT

```text
READY TO IMPLEMENT
```
