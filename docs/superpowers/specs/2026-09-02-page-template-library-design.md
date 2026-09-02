# PAGE-TEMPLATE-LIBRARY-001 — Design

**Date:** 2026-09-02
**Work item:** `PAGE-TEMPLATE-LIBRARY-001`
**Issue:** #72
**Branch:** `ux/page-template-library-001`
**Base:** `main` at `820cdfb9cac9fdd5a8b2fcd09de2a6ce51d846fa`

## 1. Purpose

Create a reusable server-rendered page-profile library on top of the accepted UX platform so new journals and modules do not copy route-local page geometry or invent another visual system.

The library has four canonical profiles required by the industrialization program:

1. registry;
2. journal;
3. specialist workspace;
4. timeline.

This is a composition layer, not a page-builder framework. It does not own domain models, business lifecycle, permissions, stored data, or specialist inner-widget behavior.

## 2. Chosen architecture

Use Django template inheritance and named blocks as the public composition contract. The shared profile library lives under:

`src/templates/shared/page_profiles/`

with these templates:

- `base.html`;
- `registry.html`;
- `journal.html`;
- `specialist_workspace.html`;
- `timeline.html`.

`base.html` extends `shared/direction_a/base.html`. The four concrete profiles extend `base.html` and define only generic composition. Domain templates extend a profile and fill blocks; they do not copy the profile shell.

No JSON/YAML schema, runtime page-builder DSL, Python component registry, or client-side composition engine is introduced.

## 3. Public template contract

The base profile exposes stable named blocks:

- `profile_kicker` — short semantic context;
- `profile_title` — page title;
- `profile_lede` — optional explanatory text;
- `profile_meta` — status/context metadata;
- `profile_actions` — page-level commands;
- `profile_context` — filters, selectors, scope/context controls;
- `profile_summary` — optional facts/counters/summary strip;
- `profile_body` — primary domain content;
- `profile_secondary` — supporting content after the primary surface;
- `profile_aside` — optional secondary rail where the profile permits it;
- `profile_footer` — optional terminal notes/actions;
- `profile_overlays` — dialogs/drawers/menus rendered outside normal flow.

All optional blocks render safely when empty. The block API is deliberately small: domain-specific controls remain inside domain templates rather than becoming generic profile options.

## 4. Profile semantics

### Registry

Composition order:

`header/actions → context/filters → summary → primary registry surface → secondary/footer`

The profile is suitable for module registries, directories, worklists and other bounded collection pages. It does not dictate table versus cards; responsive representation remains a shared/platform or domain-owned concern.

### Journal

Composition order:

`header/actions → journal context/selector → summary → registered journal surface → secondary/footer`

The profile owns framing only. Source-bound journal columns, approved-form semantics, record lifecycle markers, correction/cancellation controls, print semantics and journal typography preferences remain domain-owned.

### Specialist workspace

Composition order:

`workspace header/actions → context/toolbars → primary full-width work area → auxiliary region → overlays`

The profile deliberately allows full-width specialist geometry. OPJ editor ribbon, draft rows, autosave, locking, reference pickers and other specialist interaction contracts remain domain-owned.

### Timeline

Composition order:

`header/actions → context/summary → primary detail → chronological event region → optional aside/footer`

The profile supplies consistent chronology framing without prescribing event schema. Domain event content, audit semantics and lifecycle truth remain domain-owned.

## 5. CSS ownership

No second design system is created.

Generic profile layout selectors are added only to existing platform owners:

- `src/static/system/ux_platform_compositions.css` — base/profile composition;
- `src/static/system/ux_platform_responsive.css` — shared FULL DESKTOP / COMPACT behavior;
- `src/static/system/ux_mobile_surfaces.css` — only if PHONE-specific stacking cannot be expressed by existing rules.

The implementation uses existing semantic tokens, spacing, typography, controls, panels, tables, focus states and Direction A primitives. It must not introduce a new palette, font scale, shadow/radius system, repair stylesheet, or feature-prefixed generic component family.

Responsive boundaries remain the accepted UX-platform contract:

- FULL DESKTOP: above `61.25rem`;
- COMPACT: `48rem` through `61.25rem`;
- PHONE: below `48rem`.

Ordinary profiles cannot create document-level horizontal overflow. Intrinsically wide specialist/domain surfaces may own local scrolling only where already justified by the UX contract.

## 6. Reference integrations

This work item proves reuse through thin adapters on accepted DEFECT/OPJ references, without broad legacy migration:

- `operational_log/registry.html` → registry profile;
- `operational_log/detail.html` → journal profile;
- `operational_log/shift_workspace.html` → specialist workspace profile;
- `equipment_defects/detail.html` → timeline profile.

Integration must preserve existing domain inner markup, IDs/classes used by JavaScript, URLs, forms, lifecycle behavior and server context. The profile replaces duplicated outer composition only; it does not redesign the reference screens.

No other route-by-route migration is part of this work item.

## 7. Accessibility and interaction

Because profiles extend the existing application shell, they inherit current theme, focus, keyboard and first-paint contracts. Profile markup must preserve semantic heading order, labelled regions, keyboard-reachable commands and dialog/drawer ownership.

The library adds no JavaScript unless a genuinely generic interaction gap is proven. Existing domain JS hooks must not be renamed merely to fit the profile library.

## 8. Testing and evidence

Implementation follows TDD.

Source/render contract tests will prove:

- all five shared templates exist;
- each concrete profile extends the shared profile base;
- the public block contract is stable;
- profile classes are owned by existing platform CSS;
- optional regions can be empty;
- OPJ/DEFECT reference templates use the intended profiles;
- protected domain JS hooks and lifecycle markup remain present;
- no new design-system owner is introduced.

Then focused Django tests and the VPS-local candidate flow validate the real rendered references. Browser evidence covers light/dark, desktop/compact/phone, keyboard/focus where applicable, print-sensitive journal behavior, and document-overflow checks.

Intermediate visual repair stays on the VPS candidate/overlay loop. GitHub receives the ready implementation only after local acceptance, followed by one final exact-head repository gate and final trusted Development verification.

## 9. State and dependency handling

`UX-PLATFORM-FOUNDATION-001` is merged in GitHub through final PR #71, but canonical planning files on `main` still report it `IN_PROGRESS`. Its last trusted-controller attempt (`33577538211`) failed because the GitHub runner could not establish the VPS SSH connection and the fallback rollback timed out; the exact-head repository checks themselves were successful.

Therefore this work item starts fail-closed: planning/design work may proceed, but production template implementation does not begin until predecessor acceptance is reconciled with factual GitHub evidence and a trusted runtime baseline is successfully re-established without weakening the trust boundary.

## 10. Non-goals / hard boundaries

- no `LEGACY-UX-MIGRATION-001` broad migration;
- no new product module;
- no declarative page-builder framework;
- no client-side SPA composition layer;
- no domain model/migration/lifecycle changes;
- no Module Registry redesign;
- no Preview, pilot or production deployment;
- no Ready for Review or merge without explicit product-owner command.

## 11. Acceptance

The work item is technically complete only when:

- registry, journal, specialist workspace and timeline profiles are executable and reusable;
- OPJ/DEFECT references demonstrate the profile contracts without domain regressions;
- shared UX contract tests and browser evidence pass;
- responsive/light/dark/keyboard/print behavior remains within the accepted platform contract;
- the exact final branch head passes applicable GitHub gates;
- final trusted Development succeeds on that exact head;
- Preview remains untouched;
- owner visual acceptance is recorded before merge.
