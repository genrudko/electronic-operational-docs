# UX_IMPLEMENTATION_ROADMAP — поэтапное внедрение UX-001 v0.3

> **Пакет:** UX-001 v0.3  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Граница:** roadmap не присваивает patch numbers, не меняет domain model и не утверждает journal lifecycle.

## 1. Strategy

UX-001 внедряется без остановки основной продуктовой разработки:

```text
evidence
→ visual direction
→ reference contracts
→ minimum foundation
→ real vertical slice
→ runtime acceptance
→ extraction/reuse
→ legacy retirement
```

No big-bang rewrite. No palette-only restyle.

## 2. Stage 0 — evidence consolidation

### Выполнено

- current desktop runtime video reviewed;
- source/templates/CSS/JS findings retained;
- visual/product decision recorded;
- evidence categories separated;
- visible marker duplication recorded;
- three reference contracts prepared.

### Не выполнено

- keyboard-only capture;
- exact caret/PgUp/PgDown reproduction;
- 1440/1280/960/768/390 viewports;
- dark theme;
- 200% zoom;
- contrast report;
- screen-reader/focus return;
- network/version conflict capture.

Stage 0 remains partially open.

## 3. Stage 1 — reference visual validation

Before production implementation:

- create low/medium fidelity layouts for three reference families;
- apply candidate palette and typography;
- compare 2–3 shell treatments;
- validate card reduction and table density;
- run long Russian fixture;
- user selects direction;
- accepted token values recorded.

Output: accepted visual option, rejected alternatives/trade-offs and token decision log.

This stage may use static prototypes; it does not change production code.

## 4. Stage 2 — minimum P0 foundation

Scope:

- token layer;
- typography/surfaces;
- focus-visible;
- buttons;
- statuses/banners;
- page header/context path;
- field/error;
- overlay root;
- shell skeleton;
- compatibility aliases.

Apply first to shell and one low-risk route. Do not remove legacy CSS yet.

Gate:

- long nav labels;
- light theme;
- keyboard shell;
- no overlay regression;
- no third-party identity resemblance;
- current routes intact.

## 5. Stage 3 — first structured reference vertical slice

### Selection rule

PLAN-001 chooses the slice.

Preferred candidate:

```text
defect journal list + form + detail
+ source operational relation
```

If another journal is selected, it must exercise equivalent P0 components.

Scope:

- journal-specific IA;
- compact filters;
- async pickers;
- source-bound form;
- state/integrity hierarchy;
- contextual actions;
- relation labels;
- controlled table overflow;
- context restoration;
- long-data fixture.

Gate:

- domain source/lifecycle accepted;
- keyboard-only journey;
- normal/error/empty/loading/read-only;
- technical/demo distinction;
- user visual/domain acceptance.

## 6. Stage 4 — operational journal stabilization in parallel

This may proceed alongside Stage 3 where changes are isolated.

Priority:

1. semantic marker duplication;
2. caret/blank click;
3. native keyboard precedence;
4. overlay/focus return;
5. truthful autosave;
6. stable drawer geometry;
7. passive/active editor chrome;
8. print/clean-copy policy.

Not a complete journal rewrite.

Gate: internal demonstration scenario for journal passes in full.

## 7. Stage 5 — component extraction after real use

After accepted structured slice and journal usage:

- data grid;
- filter bar;
- pickers;
- state banner;
- relation component;
- timeline item;
- form section;
- provenance disclosure.

Rule: no premature generic abstraction. Two real usages required for nonprimitive components.

## 8. Stage 6 — rollout by archetype

Apply accepted foundation progressively:

1. structured journals chosen by product plan;
2. document registry/detail;
3. equipment/personnel directories;
4. import/staging;
5. administration;
6. paper-first registers with explicit boundary.

Each route keeps a migration note and compatibility strategy.

## 9. Stage 7 — accessibility and responsive release gate

Continuous checks, formally closed before relevant release:

- keyboard matrix;
- focus return;
- screen-reader semantics;
- contrast;
- 200% zoom;
- reduced motion;
- auxiliary mobile;
- horizontal overflow keyboard;
- long-shift review.

Dark theme closes only when its release scope is confirmed.

## 10. Stage 8 — legacy CSS/JS retirement

Only after reference components are proven:

```text
static/system/
├─ tokens.css
├─ foundations.css
├─ components/
├─ archetypes/
└─ legacy.css
```

Actions:

- deprecate legacy classes;
- remove raw semantic colors;
- remove arbitrary z-index;
- move inline scripts to owned modules;
- delete dead patch-specific blocks;
- add visual regression snapshots.

File split is secondary to clear ownership and cascade.

## 11. Workstreams that do not block each other

| Workstream | Can proceed while |
|---|---|
| PLAN-001 domain choice | visual reference validation |
| journal marker repair | structured reference design |
| token prototype | source-form research |
| keyboard evidence capture | low-risk shell prototype |
| long-data fixtures | component contract refinement |
| legacy inventory | new foundation introduced additively |

## 12. Candidate implementation slices

Names/numbers are not final and belong to integration chat.

| Candidate slice | Contents | Dependency |
|---|---|---|
| Foundation A | tokens, typography, focus, buttons, statuses | accepted reference direction |
| Shell A | lighter shell, context path, overlay root | Foundation A |
| Structured A | picker, filter bar, grid | PLAN-001 slice |
| Product A | selected list/form/detail family | domain source/lifecycle |
| Journal Stability A | markers, keyboard, focus, drawer | operational journal |
| Relations A | relation/timeline/provenance | two real usages |
| Release A11y | accessibility/responsive gates | release scope |
| Legacy Cleanup | retirement and visual regression | proven reuse |

## 13. Definition of Done per UX slice

- exact application baseline;
- evidence/source link;
- domain decision available;
- candidate vs accepted tokens explicit;
- all states implemented;
- keyboard/focus evidence;
- long Russian data;
- target viewports;
- light theme;
- dark theme only if scoped;
- no raw third-party branding;
- no arbitrary semantic color/z-index;
- automated checks where feasible;
- runtime screenshots/video;
- user visual/domain acceptance;
- canonical docs updated;
- limitations recorded.

## 14. Stop conditions

Return to design/domain decision when:

- source form ambiguous;
- lifecycle meaning unclear;
- role behavior contradictory;
- abstraction hides journal-specific information;
- visual treatment hides integrity/lifecycle conflict;
- mobile compromises desktop shift work;
- palette begins to resemble identifiable third-party branding;
- reference screen fails controlled density.

## 15. Immediate next recommendation

Documentary next step:

```text
prepare 2–3 visual variants of the three reference families
using candidate tokens
→ user selects direction
→ integration chat records accepted tokens
```

Product implementation next step after PLAN-001:

```text
minimum P0 foundation
+ selected structured vertical slice
+ parallel blocking journal stabilization
```

This sequence preserves development velocity and avoids both big-bang rewrite and superficial recoloring.

## FOR_MAIN_INTEGRATION_CHAT

- Baseline: `main / e18872face7f27f489056b72fed31e5586121b0c`.
- PLAN-001 remains authority for first structured slice.
- UX-001 does not assign patch numbers or mutate domain model.
- Marker duplication is independent blocking repair candidate.
- Candidate visual tokens require reference acceptance before canonicalization.
- Rollout is additive; legacy removal occurs last.
