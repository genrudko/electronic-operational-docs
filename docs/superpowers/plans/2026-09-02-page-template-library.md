# PAGE-TEMPLATE-LIBRARY-001 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver four reusable server-rendered Django page profiles (registry, journal, specialist workspace, timeline) on the accepted EOD UX platform, with bounded OPJ/DEFECT reference integrations and no second design system.

**Architecture:** A five-template hierarchy under `src/templates/shared/page_profiles/` owns only page composition. Existing `ux_platform*` CSS remains the style owner. Domain templates extend profiles and retain all domain behavior and specialist inner geometry.

**Tech Stack:** Django templates, existing EOD CSS/JS UX platform, Django `SimpleTestCase`/template rendering tests, existing VPS candidate/browser harness, GitHub exact-head gates.

**Spec:** `docs/superpowers/specs/2026-09-02-page-template-library-design.md`

## Global Constraints

- Work only in issue #72 / branch `ux/page-template-library-001` / its Draft PR.
- Base implementation on factual GitHub `main`.
- Do not modify Preview/pilot/production.
- Do not add page-builder DSL, new visual tokens, new generic JS framework, or repair-specific CSS.
- Preserve OPJ/DEFECT lifecycle, forms, URLs and existing JS hook IDs/classes.
- Use TDD for production template/CSS changes: RED must be observed before GREEN.
- Run focused/VPS-local checks before ready push; do not use GitHub as the repair loop.
- No Ready for Review or merge without explicit owner command.

---

### Task 0: Reconcile predecessor acceptance and activate the work item

**Files:**
- Modify: `docs/project/DEMO_RELEASE_PLAN.yaml`
- Modify: `docs/project/CURRENT_STATE.md`
- Modify generated project views required by the release-plan contract
- Create/modify: `docs/work-items/active/PAGE-TEMPLATE-LIBRARY-001/WORK_ITEM.md`

- [ ] Record factual final UX foundation closure: issue #69 completed, PR #71 merged, exact head `1497e661935c5ec21e4d7ce1d8457cbeb2effe1d`, merge/main successor `820cdfb9cac9fdd5a8b2fcd09de2a6ce51d846fa`, owner acceptance evidence and exact-head workflow evidence.
- [ ] Record the failed trusted run `33577538211` accurately as a VPS SSH transport failure; do not claim it passed.
- [ ] Keep `PAGE-TEMPLATE-LIBRARY-001` fail-closed until a trusted baseline is re-established; use a valid planning status transition (`NOT_STARTED → BLOCKED` if needed).
- [ ] Regenerate deterministic release-plan views using repository functions/scripts and run:
  - `python3 scripts/demo_release_plan.py`
  - `python3 scripts/project_state_contract.py`
  - focused process tests covering release-plan/project-state contracts.
- [ ] Commit the canonical planning/spec slice and push it to establish the Draft PR.
- [ ] Trigger the normal trusted Development controller on the planning-only exact head. After SUCCESS, record predecessor acceptance and transition `PAGE-TEMPLATE-LIBRARY-001` to `IN_PROGRESS`; rerun state contracts.

### Task 1: Define the reusable profile contract with a failing test

**Files:**
- Create: `src/apps/system/tests/test_page_template_library.py`
- Create: `src/templates/shared/page_profiles/base.html`
- Create: `src/templates/shared/page_profiles/registry.html`
- Create: `src/templates/shared/page_profiles/journal.html`
- Create: `src/templates/shared/page_profiles/specialist_workspace.html`
- Create: `src/templates/shared/page_profiles/timeline.html`

- [ ] Write tests asserting the five templates and required public blocks/classes; run the test and observe RED because the profile library does not exist.
- [ ] Implement the minimal template hierarchy from the approved spec.
- [ ] Render representative child templates with optional blocks empty and populated; assert safe output and heading/region structure.
- [ ] Run `python3 src/manage.py test apps.system.tests.test_page_template_library` and confirm GREEN.
- [ ] Commit only Task 1 files.

### Task 2: Add generic profile composition to existing UX owners

**Files:**
- Modify: `src/apps/system/tests/test_page_template_library.py`
- Modify: `src/static/system/ux_platform_compositions.css`
- Modify: `src/static/system/ux_platform_responsive.css`
- Modify only if required: `src/static/system/ux_mobile_surfaces.css`

- [ ] Add failing assertions for shared profile layout selectors and accepted responsive boundaries; observe RED.
- [ ] Add minimal generic profile CSS using existing semantic tokens/primitives.
- [ ] Assert no document-wide overflow rule is introduced and no feature-prefixed generic owner appears.
- [ ] Run focused page-template and existing UX-platform responsive tests; confirm GREEN.
- [ ] Commit only Task 2 files.

### Task 3: Prove registry reuse on OPJ

**Files:**
- Modify: `src/apps/system/tests/test_page_template_library.py`
- Modify: `src/templates/operational_log/registry.html`
- Modify only when required by adapter: existing OPJ registry partials, without changing domain semantics

- [ ] Add a failing test requiring the OPJ registry to extend/use the shared registry profile while retaining key registry classes, URLs and empty-state contract; observe RED.
- [ ] Convert only the outer OPJ registry composition to profile blocks.
- [ ] Preserve table/card/domain markup and existing JS hooks.
- [ ] Run page-template tests plus focused OPJ registry tests; confirm GREEN.
- [ ] Commit only Task 3 files.

### Task 4: Prove journal and specialist-workspace reuse on OPJ

**Files:**
- Modify: `src/apps/system/tests/test_page_template_library.py`
- Modify: `src/templates/operational_log/detail.html`
- Modify: `src/templates/operational_log/shift_workspace.html`

- [ ] Add failing tests requiring journal/workspace profiles and asserting protected OPJ hooks remain present; observe RED.
- [ ] Convert only outer composition to `journal.html` and `specialist_workspace.html` blocks.
- [ ] Preserve approved journal table geometry, settings dialog, lifecycle actions, draft editor, ribbon, autosave/locking hooks, reference pickers and print behavior.
- [ ] Run page-template tests and focused OPJ UX/lifecycle tests; confirm GREEN.
- [ ] Commit only Task 4 files.

### Task 5: Prove timeline reuse on DEFECT

**Files:**
- Modify: `src/apps/system/tests/test_page_template_library.py`
- Modify: `src/templates/equipment_defects/detail.html`
- Reuse existing: `src/templates/equipment_defects/_detail_repair2_*.html`

- [ ] Add a failing test requiring the DEFECT detail page to use the timeline profile while retaining defect lifecycle/action/audit hooks; observe RED.
- [ ] Move only the outer page/detail/chronology framing into timeline blocks.
- [ ] Preserve defect lifecycle, forms, domain partials and `defect-timeline` semantics.
- [ ] Run page-template tests plus focused DEFECT tests; confirm GREEN.
- [ ] Commit only Task 5 files.

### Task 6: Cross-profile regression and documentation

**Files:**
- Modify: `docs/ux/UX_PLATFORM_FOUNDATION.md`
- Create: `docs/ux/PAGE_TEMPLATE_LIBRARY.md`
- Modify: `docs/INDEX.md`
- Modify tests/evidence harness only where needed to exercise the four reference profiles

- [ ] Document the stable block API, profile selection rules, non-goals and examples.
- [ ] Add/extend source contract tests preventing a second generic page-template owner.
- [ ] Run focused system/OPJ/DEFECT tests, Ruff/compile/system check and `git diff --check`.
- [ ] Run `scripts/vps_candidate.sh verify` with the focused page-template/profile test labels.
- [ ] Exercise OPJ registry, registered journal, shift workspace and DEFECT detail in light/dark at desktop/compact/phone; verify keyboard/focus, print-sensitive journal behavior and document-overflow gates.
- [ ] Repair locally and repeat candidate/browser checks until stable; do not push repair iterations.
- [ ] Commit only after the local candidate is coherent.

### Task 7: Final exact-head acceptance boundary

- [ ] Ensure branch is based on current `main` (`behind_by: 0`) without losing isolated worktree changes.
- [ ] Run full local completion checks required by repository workflow.
- [ ] Push the ready implementation once.
- [ ] Wait for all applicable exact-head GitHub workflows; repair only if a factual gate exposes a defect.
- [ ] Trigger final trusted Development on the same exact head and verify health/auth/clean-tree result.
- [ ] Update Draft PR/work-item evidence with exact head, workflow runs, trusted result and shared UX contract evidence.
- [ ] Leave Preview untouched and `OWNER VISUAL ACCEPTANCE = PENDING` until the owner inspects the final Development candidate.
- [ ] Do not mark Ready for Review or merge until an explicit owner command.
