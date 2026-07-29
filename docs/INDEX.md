# Индекс документации ЭОД

**Актуализировано:** 30.07.2026

Этот индекс определяет canonical documents и порядок их использования. Фактические SHA и active work item проверяются в GitHub и `project/CURRENT_HANDOFF.md`; metadata-only documentation commit не является новым application baseline.

## Текущая контрольная точка

```text
accepted UX/application merge:
a880a632b750309c7fbfb918af15b49d99b5a93f

UX-FOUNDATION-001:
MERGED / ACCEPTED

active product work item:
OPJ-UX-001

active Draft PR:
#25 / ux/opj-ux-001 / OPEN / NOT MERGED

preview:
UNTOUCHED
```

## Начать здесь

1. [`../AGENTS.md`](../AGENTS.md)
2. [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md)
3. [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md)
4. [`project/DOMAIN_INVARIANTS.md`](project/DOMAIN_INVARIANTS.md)
5. [`project/PRODUCT_UX_PRINCIPLES.md`](project/PRODUCT_UX_PRINCIPLES.md)
6. [`process/PROJECT_OPERATING_SYSTEM.md`](process/PROJECT_OPERATING_SYSTEM.md)
7. [`process/DEVELOPMENT_WORKFLOW.md`](process/DEVELOPMENT_WORKFLOW.md)
8. [`process/DEVELOPMENT_ACCELERATION.md`](process/DEVELOPMENT_ACCELERATION.md)
9. профильный starter/ADR/runbook.

## Проект

| Документ | Назначение |
|---|---|
| [`project/CURRENT_STATE.md`](project/CURRENT_STATE.md) | Проверенные факты и baseline |
| [`project/CURRENT_HANDOFF.md`](project/CURRENT_HANDOFF.md) | Текущий active work и handoff |
| [`project/MASTER_PLAN.md`](project/MASTER_PLAN.md) | Общий продуктовый план |
| [`project/ROADMAP.md`](project/ROADMAP.md) | Очередность work items и gates |
| [`project/OPEN_ITEMS.md`](project/OPEN_ITEMS.md) | Открытые блокеры и backlog |
| [`project/DOMAIN_INVARIANTS.md`](project/DOMAIN_INVARIANTS.md) | Предметные инварианты |
| [`project/PRODUCT_UX_PRINCIPLES.md`](project/PRODUCT_UX_PRINCIPLES.md) | Принятые продуктовые и единые UX/UI-принципы |
| [`project/SCOPE_AND_BOUNDARIES.md`](project/SCOPE_AND_BOUNDARIES.md) | Границы независимого прототипа |
| [`project/SYSTEM_ARCHITECTURE.md`](project/SYSTEM_ARCHITECTURE.md) | Архитектура приложения |
| [`project/MODULE_MAP.md`](project/MODULE_MAP.md) | Карта модулей |
| [`project/DATA_AND_PRIVACY_POLICY.md`](project/DATA_AND_PRIVACY_POLICY.md) | Data/privacy |
| [`project/DECISION_LOG.md`](project/DECISION_LOG.md) | Хронология решений |
| [`project/BASELINE_HISTORY.md`](project/BASELINE_HISTORY.md) | Accepted baselines |
| [`project/ACCEPTANCE_HISTORY.md`](project/ACCEPTANCE_HISTORY.md) | Технические и пользовательские приёмки |

## Research

| Документ | Назначение |
|---|---|
| [`research/VERTICAL_PRODUCTS_RESEARCH_20260729.md`](research/VERTICAL_PRODUCTS_RESEARCH_20260729.md) | Принятый итог исследования вертикальных продуктов |
| [`research/VERTICAL_PRODUCTS_SOURCE_CATALOG_20260729.csv`](research/VERTICAL_PRODUCTS_SOURCE_CATALOG_20260729.csv) | 27 атрибутированных источников |
| [`research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv`](research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv) | Traceability решений к evidence и current work items |
| [`research/SPECIALIZED_WORKFLOW_BENCHMARK_20260729_v1_2.md`](research/SPECIALIZED_WORKFLOW_BENCHMARK_20260729_v1_2.md) | 20 ежедневных сценариев по 10 специализированным контурам; accepted research evidence v1.2 |
| [`research/SPECIALIZED_WORKFLOW_PRODUCT_EVIDENCE_20260729_v1_2.csv`](research/SPECIALIZED_WORKFLOW_PRODUCT_EVIDENCE_20260729_v1_2.csv) | PRODUCT EVIDENCE, locators, confidence, decision basis и acceptance benchmarks |
| [`research/SPECIALIZED_WORKFLOW_NORMATIVE_EVIDENCE_20260729_v1_2.csv`](research/SPECIALIZED_WORKFLOW_NORMATIVE_EVIDENCE_20260729_v1_2.csv) | Отдельная первичная NORMATIVE EVIDENCE matrix и явные evidence gaps |
| [`research/SPECIALIZED_WORKFLOW_CHANGELOG_v1_1_to_v1_2.md`](research/SPECIALIZED_WORKFLOW_CHANGELOG_v1_1_to_v1_2.md) | Узкие исправления SWB-04, N-05 и N-06 |

Исходный архив `eod_specialized_workflow_benchmark_20260729_v1_2.zip`: SHA-256 `ad043c8d0f65fc546403271bb6b1e9d5bc9377bb554d6c97a5bfb857b26687b6`. Архив не коммитится: canonical content хранится в текстовых MD/CSV.

Сторонние screenshots/PDF/video не коммитятся в публичный repository без подтверждённого права публикации.

## UX/UI

| Документ | Назначение |
|---|---|
| [`project/PRODUCT_UX_PRINCIPLES.md`](project/PRODUCT_UX_PRINCIPLES.md) | Canonical system-wide UX contract |
| [`ux/README.md`](ux/README.md) | Исторический UX-001 index |
| [`ux/UX-001_v0.3/UX_001_INDEX.md`](ux/UX-001_v0.3/UX_001_INDEX.md) | Provisional historical design package |
| [`project/UX_FOUNDATION_001_NEW_CHAT_STARTER.md`](project/UX_FOUNDATION_001_NEW_CHAT_STARTER.md) | Завершённый UX foundation starter |
| [`project/OPJ_UX_001_NEW_CHAT_STARTER.md`](project/OPJ_UX_001_NEW_CHAT_STARTER.md) | Active OPJ UX starter |

Direction A принят как общесистемный visual language. Feature-specific copies не являются design system.

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

## Автоматизация

| Контур | Статус |
|---|---|
| AUTO-001A/B trusted development controller | accepted |
| DEV-FAST-001 templates/static hot refresh | accepted |
| CI-OPT-001 duplicate full-suite removal | planned after OPJ-UX-001 |
| DEV-EVIDENCE-001 single candidate summary | planned |
| UI-CONTRACT-001 shared UI browser contract | planned |

Automatic merge и preview write отсутствуют.

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
- Green CI не равен user acceptance.
- Draft PR не является baseline.
- Research evidence не является requirement без canonical decision.
- Documentation commit не повышает application baseline автоматически.
