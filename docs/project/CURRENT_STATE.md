# ЭОД — текущее состояние

**Дата factual check:** 02.09.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 820cdfb9cac9fdd5a8b2fcd09de2a6ce51d846fa
active work item: PAGE-TEMPLATE-LIBRARY-001
active issue: #72
active PR: #73 / OPEN / DRAFT / NOT MERGED
active branch: ux/page-template-library-001
runtime impact: DEVELOPMENT
preview: UNTOUCHED
```

## Active PAGE-TEMPLATE-LIBRARY-001 execution

`PAGE-TEMPLATE-LIBRARY-001` выполняется только в issue #72, ветке `ux/page-template-library-001` и Draft PR #73.

Владелец утвердил архитектуру из четырёх server-rendered Django page profiles: registry, journal, specialist workspace и timeline. Профили строятся через template inheritance/blocks поверх принятого `ux_platform*`/Direction A слоя; новый page-builder DSL, второй design system и broad legacy migration запрещены.

Первый bounded preflight этого work item закрывает фактический post-merge state предыдущего UX contour и повторно подтверждает trusted runtime path до изменения production templates. Final UX PR #71 был merged; его applicable exact-head repository checks завершились `SUCCESS`, но trusted-controller run `33577538211` завершился `FAILURE` из-за таймаута SSH GitHub runner -> VPS. Этот транспортный сбой не объявляется успешным и должен быть re-verified на successor exact head до production page-profile implementation.

Hard boundaries текущего PR:

- не выполняется broad `LEGACY-UX-MIGRATION-001`;
- не создаются новые product modules;
- не изменяются domain models, migrations, lifecycle semantics или stored business data;
- generic layout остаётся во владельцах `ux_platform*`, feature code не создаёт вторую generic visual system;
- Preview, pilot и production не изменяются;
- Ready for Review и merge запрещены до отдельной команды владельца.

## Accepted UX-PLATFORM-FOUNDATION-001 baseline

`UX-PLATFORM-FOUNDATION-001` принят владельцем и merged окончательным repair через PR #71:

```text
accepted issue: #69 / CLOSED / COMPLETED
accepted PR: #71 / CLOSED / MERGED
accepted exact head: 1497e661935c5ec21e4d7ce1d8457cbeb2effe1d
merge commit / accepted main: 820cdfb9cac9fdd5a8b2fcd09de2a6ce51d846fa
owner visual acceptance: PASSED
applicable exact-head repository checks: SUCCESS
trusted run 33577538211: FAILURE / GitHub-runner-to-VPS SSH timeout
preview: UNTOUCHED
```

The transport failure is retained as factual evidence rather than rewritten. The successor page-template work item must re-establish trusted Development connectivity before changing production profile templates.

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
