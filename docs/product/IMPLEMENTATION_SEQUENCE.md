# Последовательность реализации

> Источник: `DEMO_RELEASE_PLAN.yaml`. Dependency order и execution queue имеют разные назначения.

## 1. Топологический порядок зависимостей

1. `PLATFORM` — зависимости: нет.
2. `MASTER-DATA` — зависимости: `PLATFORM`.
3. `DEFECT` — зависимости: `MASTER-DATA`.
4. `UX` — зависимости: `PLATFORM`.
5. `NORMATIVE-EVIDENCE` — зависимости: `PLATFORM`.
6. `PERSONNEL-AUTHORITY` — зависимости: `MASTER-DATA`, `NORMATIVE-EVIDENCE`.
7. `CROSS-DOC` — зависимости: `PLATFORM`.
8. `OPJ` — зависимости: `UX`, `PERSONNEL-AUTHORITY`, `MASTER-DATA`.
9. `SHIFT` — зависимости: `OPJ`, `PERSONNEL-AUTHORITY`.
10. `APPLICATION` — зависимости: `OPJ`, `CROSS-DOC`.
11. `GROUNDING` — зависимости: `MASTER-DATA`, `OPJ`, `CROSS-DOC`.
12. `OPERATIONAL-ORDERS` — зависимости: `OPJ`, `PERSONNEL-AUTHORITY`, `CROSS-DOC`.
13. `WORK-PERMIT` — зависимости: `PERSONNEL-AUTHORITY`, `MASTER-DATA`, `CROSS-DOC`.
14. `PERMIT-WORK-JOURNAL` — зависимости: `WORK-PERMIT`, `CROSS-DOC`.
15. `ORDER-WORK-JOURNAL` — зависимости: `PERSONNEL-AUTHORITY`, `CROSS-DOC`.
16. `CURRENT-OPERATION-WORKS` — зависимости: `PERSONNEL-AUTHORITY`, `MASTER-DATA`, `CROSS-DOC`.
17. `EQUIPMENT-INSPECTIONS` — зависимости: `MASTER-DATA`, `DEFECT`, `CROSS-DOC`.
18. `EQUIPMENT-COMMISSIONING` — зависимости: `MASTER-DATA`, `DEFECT`, `CROSS-DOC`.
19. `RZA-TM` — зависимости: `MASTER-DATA`, `CROSS-DOC`.
20. `BREAKER-INTERRUPTIONS` — зависимости: `MASTER-DATA`, `CROSS-DOC`.
21. `BATTERY-INSPECTION` — зависимости: `EQUIPMENT-INSPECTIONS`, `CROSS-DOC`.
22. `WORKPLACE-DOCS` — зависимости: `MASTER-DATA`, `PERSONNEL-AUTHORITY`.
23. `SCHEMES-DOCUMENTS` — зависимости: `WORKPLACE-DOCS`, `MASTER-DATA`.
24. `EMERGENCY-READINESS` — зависимости: `WORKPLACE-DOCS`, `OPJ`.
25. `SWITCHING-DOCUMENTS` — зависимости: `APPLICATION`, `SCHEMES-DOCUMENTS`, `PERSONNEL-AUTHORITY`, `CROSS-DOC`.
26. `DASHBOARD-REPORTING` — зависимости: `CROSS-DOC`, `OPJ`, `DEFECT`, `SHIFT`.
27. `DEMO-DATA` — зависимости: `DASHBOARD-REPORTING`.

## 2. Очередь work items после принятия baseline

1. `UX-THEME-001` / `UX` — Единая light/dark/system тема Direction A.
2. `MASTER-DATA-ALIGNMENT-001` / `MASTER-DATA` — Закрыть master-data gaps для authority.
3. `NORMATIVE-EVIDENCE-001` / `NORMATIVE-EVIDENCE` — Evidence taxonomy, legal modes и ПЭП.
4. `PERSONNEL-AUTHORITY-001` / `PERSONNEL-AUTHORITY` — Rights/scope/validity/action-time snapshot.
5. `OPJ-LIFECYCLE-001` / `OPJ` — Registration/correction/communication.
6. `SHIFT-HANDOVER-001` / `SHIFT` — Handover report and two-side evidence.
7. `CROSS-DOC-001` / `CROSS-DOC` — Typed links/provenance.
8. `APPLICATION-001` / `APPLICATION` — Оперативные заявки.
9. `GROUNDING-001` / `GROUNDING` — Inventory and placement/removal.
10. `OPERATIONAL-ORDERS-001` / `OPERATIONAL-ORDERS` — Paper journal mirror.
11. `WORK-PERMIT-001` / `WORK-PERMIT` — Hybrid permit authoring.
12. `PERMIT-WORK-JOURNAL-001` / `PERMIT-WORK-JOURNAL` — Electronic permit-work journal.
13. `ORDER-WORK-JOURNAL-001` / `ORDER-WORK-JOURNAL` — Paper order-work journal mirror.
14. `CURRENT-OPERATION-WORKS-001` / `CURRENT-OPERATION-WORKS` — List/schedule/execution/journal.
15. `EQUIPMENT-INSPECTIONS-001` / `EQUIPMENT-INSPECTIONS` — Schedule/checklist/deviation/defect.
16. `EQUIPMENT-COMMISSIONING-001` / `EQUIPMENT-COMMISSIONING` — Bounded commissioning journal.
17. `RZA-TM-001` / `RZA-TM` — Bounded RZA/TM contour.
18. `BREAKER-INTERRUPTIONS-001` / `BREAKER-INTERRUPTIONS` — Interruptions/resource.
19. `BATTERY-INSPECTION-001` / `BATTERY-INSPECTION` — Battery checklist/measurements.
20. `WORKPLACE-DOCS-001` / `WORKPLACE-DOCS` — Completeness/review/familiarization.
21. `SCHEMES-DOCUMENTS-001` / `SCHEMES-DOCUMENTS` — Scheme versions/viewer.
22. `EMERGENCY-READINESS-001` / `EMERGENCY-READINESS` — Emergency quick access.
23. `SWITCHING-DOCUMENTS-001` / `SWITCHING-DOCUMENTS` — Manual switching documents.
24. `DASHBOARD-REPORTING-001` / `DASHBOARD-REPORTING` — Derived operational views.
25. `DEMO-DATA-001` / `DEMO-DATA` — Final scenarios/reset.

Принятый `DEFECT-001` не открывается повторно; accepted foundations остаются prerequisites.

## 3. Граница ближайших OPJ / SHIFT / CROSS-DOC work items

### `OPJ-LIFECYCLE-001`

Завершает переход отдельной строки ОЖ из редактируемого сменного черновика в зарегистрированный неизменяемый чистовик. Включает внутреннюю связь черновой и зарегистрированной записи, исправление/отмену только в чистовике и фиксацию оперативно значимого результата переговоров внутри хронологии ОЖ. Не реализует сдачу смены и не создаёт универсальный междокументный relation engine.

### `SHIFT-HANDOVER-001`

Использует уже зарегистрированный журнал для подготовки отчёта передачи смены, снимка активных состояний и независимых подтверждений сдающей и принимающей сторон. Не подменяет регистрацию строк ОЖ и не превращает закрытие смены в скрытую массовую регистрацию черновика.

### `CROSS-DOC-001`

Реализует общесистемные горизонтальные и вертикальные связи между ОЖ, дефектами, заявками, работами, оборудованием и другими документами: typed relations, provenance, context snapshots, backlinks, source trail и relation graph. До него допускаются только узкие внутренние связи lifecycle конкретного модуля.
