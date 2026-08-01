# MASTER-DATA-ALIGNMENT-001 — factual preflight

**Issue:** #34  
**Branch:** `feature/master-data-alignment-001`  
**Starting main:** `49964f2dcaf7e4659a99a240dcd899d42a7dfe15`  
**Accepted application baseline:** `0d9be8c360ca22fc504ce2b11a14b6bb82c77ea5`

## FACT

### Organization structure

`apps.organizations` уже содержит:

- `Organization`;
- иерархический `Division`;
- `Workplace`;
- `OperationalArea`;
- принадлежность сотрудников, должностей и рабочих мест организации;
- directory view с подразделениями, рабочими местами, энергообъектами и связями обслуживания.

Это существующий foundation. Переписывание organization model не требуется.

### Equipment registry

`apps.equipment` уже содержит:

- `EnergySite`;
- `EquipmentType`;
- иерархический `EquipmentAsset`;
- stable code и public UUID;
- aliases и revisioned dispatcher names;
- equipment relations;
- document links/snapshots;
- immutable published revisions и audit.

`CAP-MASTER-EQUIPMENT` считается принятым foundation и не открывается повторно.

### Dispatching structure

`apps.dispatching` уже содержит независимые:

- `ManagementObject` / `ManagementRevision`;
- `SupervisionObject` / `SupervisionRevision`;
- `DispatchLevel`;
- `DispatchSubject`;
- effective windows, publication state, digest и history.

Управление и ведение не объединяются. Информационное ведение остаётся характеристикой ведения.

### Import staging

`apps.imports` уже поддерживает:

- CSV/XLSX parsing;
- file/hash/profile metadata;
- column mapping;
- staged rows;
- review statuses;
- explicit publication;
- registry-admin authorization;
- current-password confirmation;
- audit/publication records.

Текущий target `ORGANIZATION` фактически импортирует сотрудников. Отдельного staged profile для organization/division/workplace/site нет.

Текущий target `EQUIPMENT` не переносит parent hierarchy, aliases, source designation/variant и полную source provenance.

## SOURCE BOUNDARY

| Source ID | Роль в work item | Решение |
|---|---|---|
| `REF-OD-020` | распределение ЛЭП, оборудования и устройств по способу управления | основной source-bound contract текущего slice |
| `REF-OD-013` | перечень защитных средств | не расширять текущий authority prerequisite; отдельный follow-up |
| `REF-OD-021` | допустимые токовые нагрузки | отдельный equipment-validation slice, кроме минимального proven field requirement |

Исходные XLSX/PDF, реальные персональные данные и внутренние материалы предприятия не коммитятся.

## DOMAIN DECISIONS

1. ЩПТ и ШОТ относятся к одной technical family системы оперативного постоянного тока.
2. `ЩПТ`/`ШОТ` сохраняются как source designation/variant/execution.
3. Отдельные equipment types только из-за обозначения не создаются.
4. Management и supervision остаются независимыми revisioned registries.
5. Importer является staging/publishing mechanism, а не самостоятельным предметным модулем.
6. Любая unresolved/conflicting row остаётся `REVIEW` или `BLOCKED`; automatic publication запрещена.

## GAP MATRIX

| Gap | Required result |
|---|---|
| organization target смешан с personnel | отдельный structure target или явно отдельный profile для organization/division/workplace/site |
| equipment import плоский | parent hierarchy и deterministic parent resolution |
| исходное обозначение теряется | source designation/variant сохраняются отдельно от technical family |
| aliases не входят в import | controlled alias staging с scope и conflict check |
| provenance частичная | source batch/row/publication identity воспроизводимо доступна из опубликованной записи |
| dispatch import зависит только от кода | deterministic resolution и стабильные причины unresolved/conflict |
| publication boundary размыта | только reviewed rows, explicit user confirmation, authorization, immutable publication and audit |

## FIRST IMPLEMENTATION SLICE

1. Ввести machine-readable master-data import profiles и field contracts без публикации данных.
2. Разделить organization structure и personnel targets.
3. Расширить equipment staged row schema: parent, family, source designation, variant, aliases, provenance.
4. Добавить deterministic validation/status reasons и tests.
5. Не выполнять migration/publication до прохождения focused schema/import checks.

## CHANGE CLASS / RISK

```text
change class: STANDARD
risk profile: SCHEMA_DATA
candidate delivery: FULL_DEVELOPMENT
final gate: one exact-head full gate before merge
browser evidence: targeted import/equipment/dispatching routes
```

## PROTECTED BOUNDARY

- accepted equipment and dispatching history не переписывается;
- no preview write;
- no real enterprise source files/data;
- no automatic publication;
- no automatic merge;
- OPJ/DEFECT lifecycle и print geometry не меняются;
- full suite не запускается после каждого малого repair.

## ACCEPTANCE ROUTE

1. Загрузить безопасный synthetic organization-structure XLSX/CSV.
2. Проверить staged hierarchy и conflicts до публикации.
3. Загрузить equipment rows с ЩПТ/ШОТ, parent и aliases.
4. Убедиться, что technical family общая, а source designation сохранено.
5. Загрузить management/supervision rows по `REF-OD-020` contract.
6. Проверить independent management/supervision revisions и information-only supervision.
7. Подтвердить, что unresolved rows не публикуются.
8. Опубликовать reviewed synthetic rows уполномоченным пользователем и проверить immutable history/audit.

## VERDICT

```text
READY TO IMPLEMENT
```
