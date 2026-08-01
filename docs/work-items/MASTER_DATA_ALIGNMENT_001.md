# MASTER-DATA-ALIGNMENT-001 — factual preflight

**Issue:** #34
**PR:** #35
**Branch:** `feature/master-data-alignment-001`
**Starting main:** `49964f2dcaf7e4659a99a240dcd899d42a7dfe15`
**Accepted application baseline:** `0d9be8c360ca22fc504ce2b11a14b6bb82c77ea5`

## FACT

### Organization structure

`apps.organizations` уже содержит organization/division/workplace/operational-area и проверки принадлежности. Foundation переиспользуется.

### Equipment registry

`apps.equipment` уже содержит energy sites, equipment types/assets, hierarchy, aliases, revisioned dispatcher names, relations, document snapshots и audit. `CAP-MASTER-EQUIPMENT` не открывается повторно.

### Dispatching structure

`apps.dispatching` уже содержит независимые revisioned management и supervision registries. Information-only остаётся характеристикой ведения.

### Import staging

`apps.imports` уже поддерживает CSV/XLSX staging, mapping, review, explicit publication, authorization, password confirmation и audit.

Текущие gaps:

- organization import ориентирован на personnel;
- equipment staging не покрывает parent/family/source designation/variant/aliases/provenance;
- cross-registry conflict reasons недостаточно детерминированы.

## SOURCE BOUNDARY

| Source ID | Роль | Решение |
|---|---|---|
| `REF-OD-020` | распределение по способу управления | основной source-bound contract |
| `REF-OD-013` | перечень защитных средств | отдельный follow-up |
| `REF-OD-021` | допустимые нагрузки | отдельный equipment-validation slice |

Исходные XLSX/PDF, реальные персональные данные и внутренние материалы предприятия не коммитятся.

## DOMAIN DECISIONS

1. ЩПТ и ШОТ относятся к одной technical family.
2. Source designation/execution сохраняются.
3. Management и supervision остаются независимыми.
4. Unresolved/conflicting rows остаются REVIEW/BLOCKED.
5. Automatic publication запрещена.

## FIRST IMPLEMENTATION SLICE

Commit:

```text
3c9269347410da52e519c1009aefa976f8717f2c
MASTER-DATA-ALIGNMENT-001: add staged row contracts
```

Подготовлены:

- machine-readable structure/personnel/equipment/dispatching row contracts;
- deterministic READY/REVIEW/BLOCKED validation;
- общая `dc_distribution_board` family для ЩПТ/ШОТ;
- stable alias normalization;
- provenance requirement;
- запрет information-only management;
- focused tests.

Следующий slice подключает contracts к существующему staged importer без публикации данных.

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

## VERDICT

```text
READY TO IMPLEMENT
```
