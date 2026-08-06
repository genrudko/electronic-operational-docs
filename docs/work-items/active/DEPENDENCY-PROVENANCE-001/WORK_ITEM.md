# DEPENDENCY-PROVENANCE-001

## Статус

`IN_PROGRESS` в issue #57, ветке
`supply-chain/dependency-provenance-001` и Draft PR #58.

Финальная пользовательская приёмка, Ready for Review и merge требуют отдельной
явной команды владельца продукта.

## Цель

Закрыть риски `PSR-017`, `PSR-023` и `PSR-016`: сделать dependency, image и
build inputs воспроизводимыми, проверяемыми и атрибутируемыми, исключив
плавающие версии и недоказанные источники.

## Основание

- `SECRET-HYGIENE-001` — ACCEPTED / MERGED;
- accepted exact head: `cd7dc07a9c77a71a5b1166aa7a57ee4d3afa93da`;
- merge commit: `95b8dd6017745886f110f052ea0950b3d48173d8`;
- Phase 0 — COMPLETE;
- `SAFE-CONTINUATION` — 3 из 8 accepted до старта этого work item;
- dependency chain разрешает запуск `DEPENDENCY-PROVENANCE-001`.

## Program contract

```text
phase: 1
priority: P0
type: SUPPLY_CHAIN
owner role: SUPPLY_CHAIN_OWNER
dependency: SECRET-HYGIENE-001 / ACCEPTED
gate impact: SAFE-CONTINUATION
parallelization group: P1-SUPPLY-SEQUENTIAL
blocking rule: PHASE_0_ACCEPTED_AND_ALL_DEPENDENCIES_ACCEPTED
```

Acceptance statement:

> Locked hashed dependencies, pinned image digests, SBOM and build provenance.

## Canonical ownership

- `docs/project/CURRENT_STATE.md` владеет volatile active state;
- `docs/project/DEMO_RELEASE_PLAN.yaml` владеет mutable work-item status и
  acceptance evidence;
- `docs/project/INDUSTRIALIZATION_PROGRAM.yaml` владеет phase, dependency, risk
  и gate contract;
- этот файл задаёт implementation/acceptance boundary, но не создаёт второго
  planning-state owner;
- GitHub exact-head evidence сильнее текстовых отчётов.

## Scope

1. Inventory всех dependency/build inputs:
   - Python direct, transitive, build и test dependencies;
   - JavaScript/browser/build dependencies, если применимы;
   - Docker base/service images;
   - GitHub Actions references;
   - system packages из Dockerfiles/bootstrap/deployment scripts;
   - generated assets и внешние build-time downloads.
2. Canonical lock/provenance contract:
   - читаемый direct intent;
   - locked transitive resolution;
   - integrity hashes, где ecosystem их поддерживает;
   - deterministic documented regeneration;
   - fail-closed rejection stale/manual drift.
3. Immutable digest pinning для container images с human-readable version
   comment/reference.
4. Immutable commit SHA pinning для GitHub Actions с readable version comment.
5. Machine-readable SBOM для принятой application/container boundary.
6. Build provenance/attestation, связанная с exact commit и immutable inputs.
7. Permanent gates против unpinned references, missing hashes, declaration/lock
   drift и provenance другого head.
8. Operator procedure для обычного и emergency dependency update.

## Обязательный initial inventory

До выбора lock/SBOM tooling необходимо доказательно определить фактическую
packaging/build model из `pyproject.toml`, существующих lock files, Dockerfiles,
Compose, workflows и deployment scripts.

Запрещено вводить второй package manager, второй lock owner или внешний service
без доказанной необходимости.

Отдельно классифицируются:

- application runtime dependencies;
- development/test tooling;
- container/system packages;
- CI actions;
- build outputs и attestations.

## Acceptance criteria

- clean environment воспроизводит принятый dependency graph;
- installation проверяет lock и integrity hashes;
- applicable frontend/build dependencies имеют эквивалентный deterministic lock;
- images pinned immutable digest, mutable tag alone запрещён;
- GitHub Actions pinned immutable commit SHA;
- SBOM детерминированно описывает принятую boundary;
- provenance привязана к final exact head и immutable inputs;
- negative fixtures блокируют version/hash/digest/action-SHA/head drift;
- `SECRET-HYGIENE-001` redaction/publication contract сохраняется;
- artifacts не содержат credentials;
- все applicable workflows зелёные на одном final exact head;
- product/domain behavior, UX, models, migrations, data и live Preview не
  изменяются.

## Out of scope

- `DEPLOYMENT-PROFILE-001` configuration semantics;
- backup/restore drill;
- общий threat model `SECURITY-BASELINE-001`;
- module activation/registry implementation;
- MFA/RBAC/admin hardening;
- subject journals и `SHIFT-HANDOVER-001`;
- live VPS/Preview delivery без отдельного доказанного основания;
- automatic dependency upgrades или uncontrolled auto-merge;
- утверждение, что SBOM сама по себе доказывает отсутствие уязвимостей.

## Protected boundary

- no product/domain models or migrations;
- no user-facing templates/styles/UX;
- no production/demo subject data;
- no change to accepted OPJ, authority or normative lifecycle semantics;
- Preview remains `UNTOUCHED`;
- no Ready for Review or merge without explicit owner command.

## Required acceptance evidence

```text
pr
exact_head
merge_commit
workflow_runs
owner_acceptance
dependency_lock_and_provenance
```

## Stop condition

После implementation, focused regressions и полного applicable exact-head gate
остановиться на открытом Draft PR для содержательной приёмки владельцем.
