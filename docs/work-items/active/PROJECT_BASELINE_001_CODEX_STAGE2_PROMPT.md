# Codex task — `PROJECT-BASELINE-001` / Stage 2 canonical consolidation

## WORK ITEM

```text
ID: PROJECT-BASELINE-001
ISSUE: #26
BRANCH: docs/project-baseline-001
DRAFT PR: #27
ACCEPTED MAIN BASELINE: 50d96842e8700540832210990993e64fc2e3636d
REQUIRED START HEAD: HEAD containing PROJECT_BASELINE_001_STAGE2_DECISIONS.md
TYPE: DOCUMENTATION / PRODUCT ARCHITECTURE / REPOSITORY HYGIENE
STAGE: 2 — CANONICAL CONSOLIDATION
```

## Роль

Ты выполняешь второй этап `PROJECT-BASELINE-001` в существующей ветке и существующем Draft PR.

Stage 1 принят Chat 0 как factual evidence, но его proposed module map не является канонической. Все решения для Stage 2 находятся в:

```text
docs/work-items/active/PROJECT_BASELINE_001_STAGE2_DECISIONS.md
```

Точная 66-строчная транскрипция Референсного перечня находится в:

```text
docs/work-items/active/PROJECT_BASELINE_001_REFERENCE_SOURCE.csv
```

Не выполняй новый широкий аудит и не переоткрывай решения, уже явно принятые в Stage 2 decision record.

## Preflight

1. Подтверди текущую ветку `docs/project-baseline-001` и live HEAD.
2. Прочитай `AGENTS.md` и все обязательные документы из него.
3. Полностью прочитай:
   - все `PROJECT_BASELINE_001_*` Stage 1/Stage 2 файлы;
   - `docs/research/SPECIALIZED_WORKFLOW_BENCHMARK_20260729_v1_2.md`;
   - normative/product evidence CSV;
   - `docs/project/PRODUCT_UX_PRINCIPLES.md`;
   - `docs/ux/UX-001_v0.3/*`;
   - scripts/tests, которые проверяют документационные маркеры и canonical paths.
4. Проверь, что reference source содержит ровно 66 data rows с уникальными `REF-OD-001…REF-OD-066`.
5. Проверь marker/link consumers до архивирования или переименования существующих документов.

## Главный результат

Создать один непротиворечивый `DEMO-RELEASE BASELINE V1.0`, в котором:

- каждая из 66 строк референсного перечня имеет явное решение;
- каждый Demo-модуль имеет capability/depth/source/acceptance;
- product target и proven legal mode разделены;
- текущий код отражён без преувеличения;
- один machine-readable plan является источником статусов;
- human-readable checklist/map/sequence согласованы с ним;
- Codex получает готовый work-item contract без дополнительных уточнений;
- старые competing plans не остаются вторыми canonical owners.

## Обязательная canonical структура

Создай/обнови минимум:

```text
docs/project/CURRENT_STATE.md
docs/project/CURRENT_HANDOFF.md
docs/project/DEMO_RELEASE_PLAN.yaml
docs/project/DEMO_RELEASE_MASTER_CHECKLIST.md
docs/project/CHANGE_CONTROL.md
docs/project/REPOSITORY_STRUCTURE.md

docs/product/DEMO_RELEASE_SCOPE_V1.md
docs/product/MODULE_MAP.md
docs/product/IMPLEMENTATION_SEQUENCE.md
docs/product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv

docs/evidence/SOURCE_REGISTRY.csv
docs/evidence/PERSONNEL_AUTHORITY_MATRIX.csv
docs/evidence/COMPETITOR_CAPABILITY_MATRIX.csv
docs/evidence/DOCUMENT_LEGAL_MODE_MATRIX.csv

docs/ux/UX_UI_CONTRACT_V1.md
docs/ux/COMPONENT_CATALOG.md
docs/ux/ROUTE_REFERENCE_MATRIX.csv

docs/work-items/WORK_ITEM_TEMPLATE.md
docs/decisions/PROJECT_BASELINE_001_DECISIONS.md
```

Создай `docs/modules/<MODULE_ID>/MODULE_CONTRACT.md` для каждого из 27 Demo-модулей, перечисленных в Stage 2 decision record.

Каждый module contract обязан содержать:

```text
MODULE ID
НАЗНАЧЕНИЕ
ПОЛЬЗОВАТЕЛИ
КРИТИЧЕСКИЕ СЦЕНАРИИ
PRIMARY FACTS
DERIVED VIEWS
РОЛИ И ПОЛНОМОЧИЯ
ДОКУМЕНТЫ И LEGAL MODE
СВЯЗИ
SOURCE IDS
COMPETITOR BENCHMARK
DEMO DEPTH
POST-DEMO DEPTH
CURRENT CODE STATUS
CAPABILITIES
DEPENDENCIES
UX CONTRACT
ACCEPTANCE CRITERIA
OPEN VERIFY ITEMS
FORBIDDEN ASSUMPTIONS
```

## Machine-readable plan contract

`docs/project/DEMO_RELEASE_PLAN.yaml` — единственный machine-readable source release status.

Он должен содержать:

- plan version `1.0-candidate` до пользовательского утверждения;
- accepted main baseline;
- work-item/PR metadata;
- допустимые статусы;
- допустимые depth values;
- 27 Demo-модулей и Post-demo contours;
- capabilities с уникальными IDs;
- dependencies;
- source IDs;
- current code status;
- legal/product modes;
- acceptance criteria IDs;
- planned work items;
- blockers/verify items;
- presentation scenarios;
- generation/consistency metadata для human views.

Не использовать субъективные проценты.

## Coverage requirements

### Reference coverage

Canonical CSV содержит все 66 строк без слияния и потери source locator.

Для каждой строки добавь/нормализуй:

```text
reference_id
section_no
section_name
document_no
source_name
source_page
source_electronic_storage
source_review_period
normalized_document_class
coverage_class
module_id
capability_id
demo_depth
product_target_mode
normative_evidence_status
proven_legal_mode
source_ids
planned_work_item
implementation_status
acceptance_criteria_id
open_gap
```

### Personnel authority

Матрица должна включать не только gap list, но и target contract:

- organization/person/position/category;
- qualification/group;
- operational right;
- scope;
- validity;
- basis/revision;
- contractor/seconded semantics;
- substitution;
- action-time evaluation;
- immutable snapshot;
- evidence/PEP link;
- module actions that consume the right.

### Legal modes

Не выдавай product target за proven legal mode. Для каждого документа и evidence event сохрани отдельные поля target/evidence/local act/proven/gap.

### Competitors

Перенеси D-01…D-16 и добавь mapping к final module/capability/work item. Для нового implementation slice разрешён только targeted benchmark 2–4 источников, если он помечен required.

### UX

Зафиксируй Direction A, shared primitives, specialized workspace boundaries, desktop/mobile viewports, state matrix и отдельный `UX-THEME-001`.

## Documentation hygiene

1. Сначала инвентаризируй literal marker/link consumers.
2. `CURRENT_STATE.md` становится единственным owner текущего SHA/active item/runtime state.
3. `CURRENT_HANDOFF.md` становится навигатором без независимого volatile state.
4. `BASELINE_HISTORY.md` остаётся историей.
5. Старые root plans/workflows и preliminary module/roadmap files:
   - архивируй или преврати в compatibility pointer;
   - не удаляй без link/marker validation;
   - не переписывай исторические ADR/evidence SHA.
6. Обнови `docs/INDEX.md`, `AGENTS.md` и применимые process docs.
7. Добавь/усиль documentation contract, чтобы CI проверял:
   - уникальность module/capability/source IDs;
   - допустимые statuses/depth values;
   - parent/dependency references;
   - наличие acceptance/source для Demo capabilities;
   - ровно 66 reference rows;
   - согласованность YAML и human checklist/module map/sequence;
   - единственного owner volatile SHA/status;
   - отсутствие broken canonical links.

## Allowed files

```text
AGENTS.md
docs/**
scripts/check_documentation_contract.py
scripts/check_current_handoff.py
scripts/check_current_state.py
tests/**/test_*documentation*
tests/**/test_*contract*
.github/workflows/documentation-contract.yml
```

Изменение checker/tests/workflow допускается только для нового документационного контракта. Product/application/runtime code запрещён.

## Protected

Не изменять:

- `src/**`;
- models, migrations, services, routes, templates/static product code;
- Compose/deployment/controller/security/runtime;
- data/fixtures/presentation seed;
- preview/development runtime;
- historical ADR/evidence semantics.

## Commit strategy

Разрешены до трёх логических commit в существующей ветке:

1. source/canonical structure and decision records;
2. module contracts, plan, matrices and human views;
3. documentation checker/index/archive compatibility repair.

Не создавать новый issue, branch или PR. Не выполнять merge и не переводить PR в Ready for Review.

## Checks

Минимум:

```text
git diff --check
python -m compileall scripts
python scripts/check_documentation_contract.py
python scripts/check_current_state.py
python scripts/check_current_handoff.py
```

Запусти только профильные tests документационного контракта. Полный application suite не нужен для docs-only Stage 2, если CI запускает его автоматически.

## Stop conditions

Остановись и верни `BLOCKED` только если:

- 66 reference rows не удаётся сохранить без потери/дубликатов;
- решения Chat 0 внутренне противоречат друг другу;
- существующий checker требует изменения product/runtime code;
- marker consumers делают безопасное archive/compatibility решение невозможным;
- plan нельзя валидировать без нового предметного решения.

Незнание точной формы специализированного журнала не блокирует inclusion `DEMO-BOUNDED`: оставь field/lifecycle items `VERIFY` и запрети implementation до source-bound work item.

## Итоговый отчёт

```text
BASELINE
START HEAD
FINAL HEAD
COMMITS
FILES CREATED
FILES UPDATED
FILES ARCHIVED/POINTERS
66-ROW COVERAGE
MODULES/CAPABILITIES
CANONICAL OWNERS
OPEN VERIFY ITEMS
CHECKER CONTRACT
CHECKS
RUNTIME IMPACT
PREVIEW
VERDICT
```

Допустимые verdict:

```text
READY FOR CHAT 0 BASELINE REVIEW
BLOCKED — CANONICAL CONSOLIDATION INCOMPLETE
BLOCKED — DECISION CONFLICT
```
