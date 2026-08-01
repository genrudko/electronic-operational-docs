# Модульная карта Demo-релиза

> Проверяемое представление `docs/project/DEMO_RELEASE_PLAN.yaml`. Статус поставки и фактическое состояние кода разделены.

| # | Модуль | Назначение | Depth | Release | Code | Work item |
|---:|---|---|---|---|---|---|
| 1 | `PLATFORM` | Платформенные механизмы | `DEMO-FUNCTIONAL` | `IN_PROGRESS` | `IMPLEMENTED-PARTIAL` | `PLATFORM-AUDIT-001` |
| 2 | `UX` | Direction A UX | `DEMO-FUNCTIONAL` | `IN_PROGRESS` | `IMPLEMENTED-PARTIAL` | `UX-CONTRACT-001` |
| 3 | `NORMATIVE-EVIDENCE` | Нормативные режимы и evidence-события | `DEMO-BOUNDED` | `IN_PROGRESS` | `IMPLEMENTED-PARTIAL` | `NORMATIVE-EVIDENCE-001` |
| 4 | `MASTER-DATA` | Организации, объекты и оборудование | `DEMO-FUNCTIONAL` | `IN_PROGRESS` | `IMPLEMENTED-PARTIAL` | `MASTER-DATA-ALIGNMENT-001` |
| 5 | `PERSONNEL-AUTHORITY` | Персонал и оперативные полномочия | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `PERSONNEL-AUTHORITY-001` |
| 6 | `WORKPLACE-DOCS` | Документация рабочего места | `DEMO-REFERENCE` | `IN_PROGRESS` | `IMPLEMENTED-PARTIAL` | `WORKPLACE-DOCS-001` |
| 7 | `SCHEMES-DOCUMENTS` | Утверждённые и оперативные схемы | `DEMO-REFERENCE` | `NOT_STARTED` | `FOUNDATION-ONLY` | `SCHEMES-DOCUMENTS-001` |
| 8 | `OPJ` | Оперативный журнал и переговоры | `DEMO-BOUNDED` | `IN_PROGRESS` | `IMPLEMENTED-PARTIAL` | `OPJ-LIFECYCLE-001` |
| 9 | `SHIFT` | Начало и передача смены | `DEMO-BOUNDED` | `IN_PROGRESS` | `IMPLEMENTED-PARTIAL` | `SHIFT-HANDOVER-001` |
| 10 | `APPLICATION` | Оперативные заявки | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `APPLICATION-001` |
| 11 | `OPERATIONAL-ORDERS` | Журнал распоряжений | `DEMO-PAPER-MIRROR` | `NOT_STARTED` | `ABSENT` | `OPERATIONAL-ORDERS-001` |
| 12 | `DEFECT` | Журнал дефектов оборудования | `DEMO-FUNCTIONAL` | `ACCEPTED` | `IMPLEMENTED-ACCEPTED` | `DEFECT-001` |
| 13 | `GROUNDING` | Переносные заземления | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `GROUNDING-001` |
| 14 | `SWITCHING-DOCUMENTS` | Бланки и программы переключений | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `SWITCHING-DOCUMENTS-001` |
| 15 | `WORK-PERMIT` | Наряд-допуск | `DEMO-HYBRID` | `NOT_STARTED` | `ABSENT` | `WORK-PERMIT-001` |
| 16 | `PERMIT-WORK-JOURNAL` | Журнал работ по нарядам | `DEMO-FUNCTIONAL` | `NOT_STARTED` | `ABSENT` | `PERMIT-WORK-JOURNAL-001` |
| 17 | `ORDER-WORK-JOURNAL` | Журнал работ по распоряжениям | `DEMO-PAPER-MIRROR` | `NOT_STARTED` | `ABSENT` | `ORDER-WORK-JOURNAL-001` |
| 18 | `CURRENT-OPERATION-WORKS` | Работы текущей эксплуатации | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `CURRENT-OPERATION-WORKS-001` |
| 19 | `EQUIPMENT-INSPECTIONS` | Осмотры оборудования | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `EQUIPMENT-INSPECTIONS-001` |
| 20 | `EQUIPMENT-COMMISSIONING` | Ввод оборудования в работу | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `EQUIPMENT-COMMISSIONING-001` |
| 21 | `RZA-TM` | РЗА и телемеханика | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `RZA-TM-001` |
| 22 | `BREAKER-INTERRUPTIONS` | Отключения токов КЗ выключателями | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `BREAKER-INTERRUPTIONS-001` |
| 23 | `BATTERY-INSPECTION` | Осмотр аккумуляторных батарей | `DEMO-BOUNDED` | `NOT_STARTED` | `ABSENT` | `BATTERY-INSPECTION-001` |
| 24 | `EMERGENCY-READINESS` | Аварийная и пожарная готовность | `DEMO-REFERENCE` | `NOT_STARTED` | `ABSENT` | `EMERGENCY-READINESS-001` |
| 25 | `CROSS-DOC` | Междокументные связи | `DEMO-BOUNDED` | `NOT_STARTED` | `FOUNDATION-ONLY` | `CROSS-DOC-001` |
| 26 | `DASHBOARD-REPORTING` | Оперативные представления и отчётность | `DEMO-BOUNDED` | `NOT_STARTED` | `PRESENTATION-ONLY` | `DASHBOARD-REPORTING-001` |
| 27 | `DEMO-DATA` | Детерминированные данные и сценарии | `DEMO-FUNCTIONAL` | `IN_PROGRESS` | `PRESENTATION-ONLY` | `DEMO-DATA-001` |

## Принцип

- `status` показывает готовность модуля к Demo.
- `code` показывает только доказанное Stage 1 состояние.
- `accepted` slices не открываются повторно обычным work item.
- Generic primitives не превращают отсутствующий предметный модуль в реализованный.
