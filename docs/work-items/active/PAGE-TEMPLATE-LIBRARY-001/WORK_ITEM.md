# PAGE-TEMPLATE-LIBRARY-001

**Status:** IN_PROGRESS / trusted baseline re-verification before production templates
**Issue:** #72
**Branch:** `ux/page-template-library-001`
**Draft PR:** #73 / OPEN / DRAFT / NOT MERGED
**Base:** `main` @ `820cdfb9cac9fdd5a8b2fcd09de2a6ce51d846fa`
**Owner role:** `UX_PLATFORM_OWNER`
**Risk:** `PSR-010`

## Owner-approved direction

Implement four reusable server-rendered Django page profiles — registry, journal, specialist workspace and timeline — as template inheritance/block contracts on the accepted shared UX platform. Do not build a page-builder DSL or a second design system.

Canonical design: `docs/superpowers/specs/2026-09-02-page-template-library-design.md`.
Implementation plan: `docs/superpowers/plans/2026-09-02-page-template-library.md`.

## Dependency preflight

GitHub facts prove the final UX foundation repair is merged:

- issue #69: CLOSED / COMPLETED;
- final closure PR #71: MERGED;
- final PR head: `1497e661935c5ec21e4d7ce1d8457cbeb2effe1d`;
- accepted-main successor after merge: `820cdfb9cac9fdd5a8b2fcd09de2a6ce51d846fa`;
- owner visual acceptance was recorded in PR #71;
- exact-head repository checks on the final PR head passed.

The final trusted-controller run `33577538211` did **not** pass: its request validator succeeded, but the GitHub runner timed out establishing the VPS SSH connection; fallback rollback also timed out. This is an infrastructure/transport failure, not application-test evidence, and must not be rewritten as PASS.

Production implementation remains fail-closed until the predecessor acceptance record is reconciled and a trusted runtime baseline succeeds.

## Scope

- shared profile templates under `src/templates/shared/page_profiles/`;
- generic profile layout only in existing UX-platform static owners;
- thin reference integration for OPJ registry / registered journal / shift workspace and DEFECT detail timeline;
- focused source/render tests and shared UX evidence;
- VPS-local visual repair loop before ready push;
- one final exact-head GitHub cycle and trusted Development verification.

## Hard boundaries

- no broad `LEGACY-UX-MIGRATION-001`;
- no new product modules;
- no domain lifecycle/model/migration changes;
- no second visual system or page-builder framework;
- no Preview/pilot/production deployment;
- no Ready for Review / merge without explicit owner command.

## Acceptance

`Registry, journal, specialist workspace and timeline profiles are reusable.`

Evidence requirements from the industrialization program:

- PR;
- exact head;
- merge commit;
- workflow runs;
- owner acceptance;
- shared UX contract evidence.
