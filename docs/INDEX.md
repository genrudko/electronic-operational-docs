# Индекс документации ЭОД

**Актуализировано:** 30.07.2026

Этот индекс определяет canonical documents и порядок их использования. Он не дублирует volatile SHA, active work item или runtime state.

## Начать здесь

1. [`../AGENTS.md`](../AGENTS.md)
2. [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md)
3. [`project/DEMO_RELEASE_PLAN.yaml`](project/DEMO_RELEASE_PLAN.yaml)
4. [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md)
5. [`project/DOMAIN_INVARIANTS.md`](project/DOMAIN_INVARIANTS.md)
6. [`project/PRODUCT_UX_PRINCIPLES.md`](project/PRODUCT_UX_PRINCIPLES.md)
7. [`ux/UX_UI_CONTRACT_V1.md`](ux/UX_UI_CONTRACT_V1.md)
8. [`process/PROJECT_OPERATING_SYSTEM.md`](process/PROJECT_OPERATING_SYSTEM.md)
9. [`process/DEVELOPMENT_WORKFLOW.md`](process/DEVELOPMENT_WORKFLOW.md)
10. профильный module contract, ADR, starter и runbook.

## Владельцы истины

| Документ | Владеет |
|---|---|
| [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md) | accepted main SHA, active work item/PR, runtime state |
| [`project/DEMO_RELEASE_PLAN.yaml`](project/DEMO_RELEASE_PLAN.yaml) | release/module/capability/work-item status, depth, dependencies, sources и acceptance |
| [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md) | навигация к актуальным владельцам без независимого volatile state |
| [`project/BASELINE_HISTORY.md`](project/BASELINE_HISTORY.md) | история принятых baseline, но не текущий state |

## Demo-release baseline

| Документ | Назначение |
|---|---|
| [`product/DEMO_RELEASE_SCOPE_V1.md`](product/DEMO_RELEASE_SCOPE_V1.md) | Human-readable границы Demo/Post-demo |
| [`product/MODULE_MAP.md`](product/MODULE_MAP.md) | Проверяемая карта 27 Demo-модулей |
| [`product/IMPLEMENTATION_SEQUENCE.md`](product/IMPLEMENTATION_SEQUENCE.md) | Dependency order и очередь work items |
| [`project/DEMO_RELEASE_MASTER_CHECKLIST.md`](project/DEMO_RELEASE_MASTER_CHECKLIST.md) | Проверяемый master checklist |
| [`project/CHANGE_CONTROL.md`](project/CHANGE_CONTROL.md) | Порядок изменения принятого baseline |
| [`project/REPOSITORY_STRUCTURE.md`](project/REPOSITORY_STRUCTURE.md) | Canonical расположение документации |
| [`decisions/PROJECT_BASELINE_001_DECISIONS.md`](decisions/PROJECT_BASELINE_001_DECISIONS.md) | Decision record baseline-кандидата |

## Референсный перечень и evidence

| Документ | Назначение |
|---|---|
| [`product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv`](product/REFERENCE_OPERATIONAL_DOCUMENTATION_COVERAGE.csv) | Точная транскрипция 66 строк Референсного перечня |
| [`product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv`](product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISIONS.csv) | По одной assignment-строке на каждый `REF-OD-001…066` |
| [`product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISION_PROFILES.csv`](product/REFERENCE_OPERATIONAL_DOCUMENTATION_DECISION_PROFILES.csv) | Нормализованные решения, включая split legal modes |
| [`evidence/SOURCE_REGISTRY.csv`](evidence/SOURCE_REGISTRY.csv) | Реестр источников и ограничений доказательств |
| [`evidence/PERSONNEL_AUTHORITY_MATRIX.csv`](evidence/PERSONNEL_AUTHORITY_MATRIX.csv) | Target contract полномочий и gaps |
| [`evidence/DOCUMENT_LEGAL_MODE_MATRIX.csv`](evidence/DOCUMENT_LEGAL_MODE_MATRIX.csv) | Product target, evidence/local act и proven legal mode раздельно |
| [`evidence/COMPETITOR_CAPABILITY_MATRIX.csv`](evidence/COMPETITOR_CAPABILITY_MATRIX.csv) | D-01…D-16 и mapping к модулям/capabilities |

## Модульные контракты

Для каждого из 27 Demo-модулей действует отдельный файл:

```text
docs/modules/<MODULE_ID>/MODULE_CONTRACT.md
```

Module contract определяет primary facts, derived views, роли, legal mode, связи, sources, Demo/Post-demo depth, current code status, capabilities, dependencies, UX contract, acceptance и `VERIFY` items.

## UX/UI

| Документ | Назначение |
|---|---|
| [`project/PRODUCT_UX_PRINCIPLES.md`](project/PRODUCT_UX_PRINCIPLES.md) | Общесистемные продуктовые и UX-принципы |
| [`ux/UX_UI_CONTRACT_V1.md`](ux/UX_UI_CONTRACT_V1.md) | Direction A, shared primitives, viewport/state contract |
| [`ux/COMPONENT_CATALOG.md`](ux/COMPONENT_CATALOG.md) | Каталог общих компонентов |
| [`ux/ROUTE_REFERENCE_MATRIX.csv`](ux/ROUTE_REFERENCE_MATRIX.csv) | Reference locator, adopt/adapt/reject и acceptance viewport/state |
| [`ux/README.md`](ux/README.md) | Индекс исторических UX evidence |

## Проект и архитектура

| Документ | Назначение |
|---|---|
| [`project/MASTER_PLAN.md`](project/MASTER_PLAN.md) | Compatibility overview; не владеет release status |
| [`project/SCOPE_AND_BOUNDARIES.md`](project/SCOPE_AND_BOUNDARIES.md) | Границы независимого продукта |
| [`project/SYSTEM_ARCHITECTURE.md`](project/SYSTEM_ARCHITECTURE.md) | Архитектура приложения |
| [`project/DATA_AND_PRIVACY_POLICY.md`](project/DATA_AND_PRIVACY_POLICY.md) | Data/privacy |
| [`project/DECISION_LOG.md`](project/DECISION_LOG.md) | Хронология решений |
| [`project/BASELINE_HISTORY.md`](project/BASELINE_HISTORY.md) | История accepted baselines |
| [`project/ACCEPTANCE_HISTORY.md`](project/ACCEPTANCE_HISTORY.md) | Технические и пользовательские приёмки |

Compatibility pointers:

- [`project/ROADMAP.md`](project/ROADMAP.md)
- [`project/OPEN_ITEMS.md`](project/OPEN_ITEMS.md)
- [`project/MODULE_MAP.md`](project/MODULE_MAP.md)

Они не владеют статусами и обязаны указывать на canonical owners.

## Research

| Документ | Назначение |
|---|---|
| [`research/VERTICAL_PRODUCTS_RESEARCH_20260729.md`](research/VERTICAL_PRODUCTS_RESEARCH_20260729.md) | Принятый итог исследования вертикальных продуктов |
| [`research/VERTICAL_PRODUCTS_SOURCE_CATALOG_20260729.csv`](research/VERTICAL_PRODUCTS_SOURCE_CATALOG_20260729.csv) | Атрибутированные источники |
| [`research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv`](research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv) | Traceability решений к evidence |
| [`research/SPECIALIZED_WORKFLOW_BENCHMARK_20260729_v1_2.md`](research/SPECIALIZED_WORKFLOW_BENCHMARK_20260729_v1_2.md) | Specialized workflow benchmark v1.2 |
| [`research/SPECIALIZED_WORKFLOW_PRODUCT_EVIDENCE_20260729_v1_2.csv`](research/SPECIALIZED_WORKFLOW_PRODUCT_EVIDENCE_20260729_v1_2.csv) | Product evidence matrix |
| [`research/SPECIALIZED_WORKFLOW_NORMATIVE_EVIDENCE_20260729_v1_2.csv`](research/SPECIALIZED_WORKFLOW_NORMATIVE_EVIDENCE_20260729_v1_2.csv) | Normative evidence matrix |

Исходные внутренние PDF/XLSX/CSV, архивы предприятия и сторонние материалы без подтверждённого права публикации не коммитятся.

## Процесс разработки

| Документ | Назначение |
|---|---|
| [`process/PROJECT_OPERATING_SYSTEM.md`](process/PROJECT_OPERATING_SYSTEM.md) | Роли, контуры, lifecycle и инварианты |
| [`process/DEVELOPMENT_WORKFLOW.md`](process/DEVELOPMENT_WORKFLOW.md) | Factual preflight → repair loop → final gate |
| [`process/DEVELOPMENT_ACCELERATION.md`](process/DEVELOPMENT_ACCELERATION.md) | Tiered checks и automation backlog |
| [`process/CI_AND_QUALITY_GATES.md`](process/CI_AND_QUALITY_GATES.md) | Quality gates |
| [`process/DEFINITION_OF_DONE.md`](process/DEFINITION_OF_DONE.md) | Definition of Done |
| [`process/BRANCH_AND_PR_POLICY.md`](process/BRANCH_AND_PR_POLICY.md) | Branch/PR contract |
| [`process/RELEASE_PROCESS.md`](process/RELEASE_PROCESS.md) | Merge/deployment/baseline |
| [`process/PARALLEL_CHAT_WORKFLOW.md`](process/PARALLEL_CHAT_WORKFLOW.md) | Chat separation |

## Work items

- [`work-items/WORK_ITEM_TEMPLATE.md`](work-items/WORK_ITEM_TEMPLATE.md)
- `work-items/active/` — factual audit/source/decision inputs активного work item; не является вторым release owner.

## Runbooks

- [`runbooks/PREVIEW_RUNBOOK.md`](runbooks/PREVIEW_RUNBOOK.md)
- [`runbooks/DEVELOPMENT_RUNBOOK.md`](runbooks/DEVELOPMENT_RUNBOOK.md)
- [`runbooks/DATABASE_BACKUP_AND_RESTORE.md`](runbooks/DATABASE_BACKUP_AND_RESTORE.md)
- [`runbooks/PRESENTATION_DATA_RESET.md`](runbooks/PRESENTATION_DATA_RESET.md)
- [`runbooks/SSH_TUNNEL_ACCESS.md`](runbooks/SSH_TUNNEL_ACCESS.md)
- [`runbooks/POST_MERGE_DEPLOYMENT.md`](runbooks/POST_MERGE_DEPLOYMENT.md)
- [`runbooks/INCIDENT_AND_ROLLBACK.md`](runbooks/INCIDENT_AND_ROLLBACK.md)

## Приёмка

- [`acceptance/INTERNAL_PROTOTYPE_ACCEPTANCE.md`](acceptance/INTERNAL_PROTOTYPE_ACCEPTANCE.md)
- [`acceptance/DEMONSTRATION_SCENARIOS.md`](acceptance/DEMONSTRATION_SCENARIOS.md)
- [`acceptance/REGRESSION_CHECKLIST.md`](acceptance/REGRESSION_CHECKLIST.md)
- [`acceptance/KNOWN_LIMITATIONS.md`](acceptance/KNOWN_LIMITATIONS.md)

## Правило актуальности

- GitHub state сильнее описания в чате.
- `CURRENT_STATE.md` — единственный owner volatile state.
- `DEMO_RELEASE_PLAN.yaml` — единственный owner release status.
- Green CI не равен user acceptance.
- Draft PR не является baseline.
- Research evidence не является requirement без canonical decision.
- Documentation commit не повышает application baseline автоматически.
