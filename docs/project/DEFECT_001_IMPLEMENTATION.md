# DEFECT-001 — Source-bound Equipment Defect Journal

**Work item:** `DEFECT-001`  
**Branch:** `feature/defect-001-equipment-defect-journal`  
**Draft PR:** `#16`  
**Base:** `main / b75db8bc073e4b02a3254512e9b99d00f3e6e0e2`  
**Accepted application baseline:** `937d2cd2b187c17fac3088ccfc52079fc4608306`

## 1. Status

```text
implementation: IN PROGRESS
focused tests: ADDED / CI PENDING
full PostgreSQL suite: PENDING
five exact-head workflows: PENDING
VPS development deployment: NOT STARTED
preview: UNTOUCHED
user acceptance: PENDING
merge authorization: ABSENT
```

The work item is not accepted merely because source code or CI exists. Product and
visual acceptance require an exact-SHA development deployment and a separate user
review.

## 2. Source authority

The implementation is bound to:

```text
И-00-007-ОР-2025 версия 2
«Инструкция о порядке работы с документацией,
необходимой для осуществления оперативно-технологического управления
объектами электроэнергетики
АО „Росатом Возобновляемая энергия“»

section: 11
appendix: 8
```

The electronic prototype is a reference/control and demonstration layer with a
browser-printable representation of the approved paper form. It does not claim
paperless legal equivalence, УКЭП or industrial readiness.

## 3. Exact six-column presentation contract

The registry and print view preserve this order:

1. `Дата обнаружения дефекта`.
2. `Наименование ЛЭП, оборудования, устройства, содержание дефекта, Ф.И.О., подпись лица, обнаружившего дефект`.
3. `Срок устранения, Ф.И.О., подпись ответственного лица за эксплуатацию ЛЭП, оборудования, устройства, сооружения, здания`.
4. `Дата устранения дефекта, Ф.И.О., подпись ответственного лица за его устранение`.
5. `Содержание выполненных работ по устранению дефекта`.
6. `Ф.И.О., подписи оперативного персонала`.

No priority, criticality, temperature, probability, cost, arbitrary category or
user-defined schema field is added to the approved working form. The internal
registration number is shown only as a compact navigation attribute and is not a
seventh print column.

## 4. Reused generic core

`apps.operational_documents` remains the authoritative mechanism for:

- source-bound type and immutable published revision;
- PostgreSQL-safe numbering;
- record revisions and canonical snapshots;
- SHA-256 integrity;
- participant and equipment projections;
- dispatcher-name snapshots;
- append-only audit;
- organization isolation;
- terminal lock and no physical delete.

`apps.equipment_defects` adds only the specialized subject layer and does not
reimplement the generic record core.

## 5. Specialized subject contract

### Data

```text
DETECTED_AT
DEFECT_DESCRIPTION
ELIMINATION_DEADLINE
RESOLVED_AT
RESOLUTION_WORK_SUMMARY
```

Equipment is a mandatory structured link. The dispatcher name is frozen in the
record snapshot at registration time.

### Participants

```text
DISCOVERED_BY
OPERATIONS_RESPONSIBLE
RESOLUTION_RESPONSIBLE
OPERATIONAL_ACKNOWLEDGER
```

`created_by` is separate from `DISCOVERED_BY` because administrative/technical
personnel may discover a defect while operational personnel register it.

### Lifecycle

```text
REGISTERED
→ IN_PROGRESS
→ RESOLVED
→ CLOSED
```

The only working actions are:

```text
Подтвердить срок
Продлить срок
Подтвердить устранение
Ознакомиться
Закрыть дефект
```

The generic schema-driven create/edit/transition routes redirect defect records to
the dedicated journal.

### Deadline extension

An extension is a separate versioned action. It stores:

- previous deadline;
- new deadline;
- actor and position snapshots;
- server timestamp;
- reason/comment;
- record version and revision;
- canonical action snapshot and SHA-256.

The subject history and print representation contain the exact text:

```text
Срок устранения продлен
```

The previous deadline is never silently overwritten.

### Confirmed actions

Actions requiring a signature in the paper source are represented by authenticated,
personal confirmations containing employee, position, timestamp, exact record
version, canonical snapshot and SHA-256. The UI does not call them legally
significant electronic signatures.

## 6. Volume rule

`EquipmentDefectVolume` provides the minimum source-bound volume contract:

- records remain attached to their original volume;
- opening a new volume does not clone or move unresolved records;
- the old volume remains open for completion history;
- its end date becomes the resolution date of its last unresolved defect;
- no broader archive subsystem is introduced in DEFECT-001.

## 7. Operational journal link

`EquipmentDefectOperationalLogLink` explicitly links a defect record to one
registered `OperationalLogEntry` and stores immutable snapshots of the source entry
number, time, content and digest.

The operational-journal detail provides `Создать дефект` for registered entries and
shows linked defect numbers and states. The unfinished shift-draft and shift-handover
lifecycles are untouched.

## 8. Presentation data

The idempotent `seed_equipment_defects` command creates five safe examples:

1. registered without deadline;
2. in progress;
3. deadline extended;
4. resolved and awaiting acknowledgement/closure;
5. closed.

Stable `presentation_key` values prevent duplicates. No real enterprise personal or
operational data is committed.

## 9. Focused gates

The focused suite covers:

- exact published schema and immutable revision;
- mandatory equipment and dispatcher-name snapshot;
- `created_by != DISCOVERED_BY`;
- lifecycle guards;
- extension history and exact extension wording;
- acknowledgement before close;
- terminal lock and no physical delete;
- organization isolation;
- operational-log snapshot/digest link;
- dedicated Russian routes and absence of a user-facing constructor;
- exact six-column print order;
- idempotent presentation seed;
- PostgreSQL concurrent numbering.

Final acceptance still requires one green full PostgreSQL suite on the final exact
head, all five exact-head workflows, trusted development deployment, healthy runtime
and user visual review.

## 10. Non-negotiable process controls

- User manual VPS commands: `ZERO`.
- Preview writes: `ZERO`.
- Automatic merge: `DISABLED`.
- Merge without a separate user command: `FORBIDDEN`.
- All repairs remain in branch and PR `#16`.
