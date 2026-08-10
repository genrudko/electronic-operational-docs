# ЭОД — текущее состояние

**Дата factual check:** 10.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 1befcb73a8a6f7cc03c2e18d292cbb2c85ef6594
active work item: UX-PLATFORM-FOUNDATION-001
active issue: #69
active PR: #70 / OPEN / DRAFT / NOT MERGED
active branch: ux/ux-platform-foundation-001
runtime impact: DEVELOPMENT
preview: UNTOUCHED
```

## Active UX-PLATFORM-FOUNDATION-001 execution

`UX-PLATFORM-FOUNDATION-001` выполняется только в issue #69, ветке `ux/ux-platform-foundation-001` и Draft PR #70.

Цель текущего work item — превратить принятый Direction A / DEFECT / OPJ / UX-THEME визуальный язык в общую UX platform: один application shell, один semantic-token owner, reusable visual/interaction primitives и устойчивые interaction contracts, доказанные на DEFECT и OPJ.

Hard boundaries текущего PR:

- не реализуется `PAGE-TEMPLATE-LIBRARY-001`;
- не выполняется broad `LEGACY-UX-MIGRATION-001`;
- не создаются новые product modules;
- не изменяются domain lifecycle, OPJ registration/autosave/revisions/locking, DEFECT lifecycle, Module Registry semantics или stored business data;
- Preview, pilot и production не изменяются;
- Ready for Review и merge запрещены до отдельной команды владельца.

Trusted Development delivery разрешён только для final visual candidate; deployed SHA обязан совпадать с final PR head.

## Accepted MODULE-REGISTRY-001 baseline

`MODULE-REGISTRY-001` принят владельцем и merged обычным merge commit:

```text
accepted PR: #68 / CLOSED / MERGED
accepted exact head: f00d99b6434477c7bcefceff5253d6ccbe4a5fca
merge commit / accepted main: 1befcb73a8a6f7cc03c2e18d292cbb2c85ef6594
issue: #67 / CLOSED / COMPLETED
owner acceptance: PASSED
runtime impact: NONE
preview: UNTOUCHED
```

Accepted baseline включает deterministic module manifests, scoped lifecycle/activation audit, central module-access semantics, representative OPJ↔DEFECT integration и сохранение retained history при деактивации/повторной активации. Все девять применимых exact-head workflows завершились `SUCCESS`:

```text
EOD CI:                      31416503293 / SUCCESS
EOD Dependency Provenance:   31416503309 / SUCCESS
EOD Backup Restore Drill:    31416503474 / SUCCESS
EOD Development Stack:       31416503465 / SUCCESS
AUTO-001A Foundation CI:     31416503539 / SUCCESS
AUTO-001B Controller CI:     31416503568 / SUCCESS
EOD Documentation Contract: 31416503580 / SUCCESS
EOD Deployment Profile:      31416503584 / SUCCESS
EOD Secret Hygiene:          31416503615 / SUCCESS
```

`SAFE-CONTINUATION` фактически и канонически достигнут: **8/8 ACCEPTED**.

Утверждённый владельцем маршрут сохраняется:

`SAFE closure -> MODULE-REGISTRY-001 -> UX-PLATFORM-FOUNDATION-001 -> PAGE-TEMPLATE-LIBRARY-001 -> controlled existing-UI migration -> new product/module development -> remaining PILOT hardening in risk-based portions`.

Предметная очередь остаётся paused до завершения UX platform и следующего page-template этапа; `SHIFT-HANDOVER-001` не стартовал.

Полная immutable история ранее принятых baseline хранится в [`ACCEPTANCE_HISTORY.md`](ACCEPTANCE_HISTORY.md) и [`BASELINE_HISTORY.md`](BASELINE_HISTORY.md). Release/module/capability/work-item planning state хранится только в [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml).
