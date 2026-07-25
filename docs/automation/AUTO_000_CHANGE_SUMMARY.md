# AUTO-000 — change summary

## Baseline

```text
base: main / 4237aadc2cfdee518567024c2b45b653f49c16e7
branch: docs/004-auto-000-development-automation-contract
change type: documentation-only
```

## Purpose

Зафиксировать architecture/security/acceptance contract минимальной автоматизации PR → VPS development до появления исполняемого AUTO-001.

## Runtime impact

```text
application behavior: unchanged
models/migrations: none
runtime data: unchanged
GitHub workflows: unchanged
VPS configuration: unchanged
secrets: unchanged
preview rebuild: not required
```

## Canonical synchronization

- current main HEAD updated after QUALITY-001;
- full PostgreSQL test baseline recorded as 497/497;
- obsolete 0-test debt removed;
- AUTO-000/AUTO-001 inserted before continuation of PLAN-001;
- accepted application baseline intentionally remains unchanged until recorded post-merge preview evidence.

## Next step after acceptance

Separate AUTO-001 implementation branch and Draft PR. No implementation starts from this documentation branch.
