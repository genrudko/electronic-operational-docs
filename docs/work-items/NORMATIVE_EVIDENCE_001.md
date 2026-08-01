# NORMATIVE-EVIDENCE-001 — execution package

**Issue:** #40
**Draft PR:** #41
**Branch:** `feature/normative-evidence-001`
**Starting main tip:** `c05ace785f054233aa878ddead491def47525140`
**Accepted application baseline:** `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb`

## WORK ITEM

```text
ID: NORMATIVE-EVIDENCE-001
PARENT RELEASE: DEMO-RELEASE BASELINE V1.0
PARENT MODULE: NORMATIVE-EVIDENCE
CAPABILITIES:
- CAP-NORMATIVE-LEGAL-MODES
- CAP-NORMATIVE-EVENTS
- CAP-NORMATIVE-PEP
```

## GOAL

Создать один bounded-контур, который:

1. хранит product target отдельно от доказанного legal mode;
2. различает подпись, ознакомление, инструктаж, проверку знаний и подтверждение действия;
3. связывает evidence event с subject, actor snapshot, серверным временем, confirmation method, payload digest и traceable basis;
4. переиспользует существующие `SignedSnapshot`, `DocumentSignature`, password re-authentication и integrity primitives;
5. не выдаёт техническую неизменяемость, SHA-256 или повторную аутентификацию за автоматически доказанную юридическую значимость.

## FACTUAL START

До work item существовали:

- `NormativeDocument`, immutable published `NormativeRevision`, `NormativeRequirement`, `RequirementTrace`;
- immutable `SignedSnapshot` и `DocumentSignature`;
- canonical JSON, SHA-256, password re-authentication и document integrity verification;
- identity, employee snapshots, roles и authentication audit foundations.

Не существовали:

- единая persisted taxonomy evidence-событий;
- append-only legal-mode decisions;
- единая read-only поверхность для target/proven mismatch и evidence history.

## DOMAIN CONTRACT

1. `product_target_mode` и `proven_legal_mode` — разные поля и разные утверждения.
2. `VERIFY` является честным состоянием, а не ошибкой или временным UI placeholder.
3. Non-`VERIFY` требует опубликованную нормативную редакцию с SHA-256 и закрытый local-act gate.
4. `ACKNOWLEDGEMENT` не доказывает `INSTRUCTION`, `KNOWLEDGE_CHECK` или `SIGNATURE`.
5. `SIGNATURE` не доказывает предметное право actor; authority-at-action остаётся downstream capability.
6. Password re-authentication не сохраняет пароль и не объявляется УКЭП или УНЭП.
7. Historical decisions/events append-only; изменение оформляется новой связанной записью.
8. Реальные локальные акты, персональные данные и enterprise evidence в Git не добавляются.

## IMPLEMENTED SLICE 1 — PURE CONTRACT

```text
src/apps/normatives/evidence.py
src/apps/normatives/tests/test_evidence_contract.py
```

Реализованы:

- `ProductTargetMode`, `ProvenLegalMode`;
- `NormativeEvidenceStatus`, `LocalActStatus`;
- `EvidenceEventType` для пяти раздельных semantics;
- `EvidenceConfirmationMethod`;
- required payload contract для каждого event type;
- deeply immutable actor snapshot/payload;
- deterministic canonical JSON/SHA-256;
- recursive secret-like field rejection;
- compatibility rules и запрет недоказанного повышения `VERIFY`.

Slice 1 прошёл все пять exact-head workflows на `5268b8266138d671ac2573a92e8ea18bef9fde84`.

## IMPLEMENTED SLICE 2 — PERSISTENCE AND SERVICES

Добавлены append-only модели:

### `LegalModeDecision`

- organization/global scope;
- target/proven/evidence/local-act states;
- published normative/local revision links и immutable basis-code snapshots;
- source IDs, decision basis, decision-maker snapshot, server time;
- supersedes link;
- canonical JSON, SHA-256 и tamper verification;
- запрет update/delete/bulk update через manager/model boundary.

### `EvidenceEvent`

- пять самостоятельных event types;
- organization, subject type/id, actor snapshot, server time;
- confirmation method и explicit re-auth requirement;
- normative revision/source IDs;
- correlation ID, correction link и idempotency;
- immutable payload, canonical JSON, SHA-256;
- optional verified link to existing `DocumentSignature`;
- tenant-bounded read access.

### Transactional services

- active actor row locking без `FOR UPDATE` на nullable outer joins;
- personal-session validation;
- password re-authentication with no password persistence;
- atomic rollback on invalid credentials/contract/basis;
- published-revision validation;
- correlation idempotency and conflicting reuse rejection;
- nested savepoint recovery for unique-key races;
- semantic equality check before returning a concurrent event;
- correction as a new linked event;
- integrity verification against canonical state.

### Existing signature integration

`DocumentSignature` остаётся владельцем системного подтверждения документа. `post_save` создаёт ровно одно отдельное `SIGNATURE` evidence-событие, содержащее:

- snapshot digest;
- purpose;
- signature checksum;
- honest confirmation method;
- actor snapshot and server time.

Новый модуль не создаёт параллельную signature/hash/authentication framework.

## IMPLEMENTED SLICE 3 — READ-ONLY ACCEPTANCE SURFACE

Добавлены tenant-bounded read-only страницы:

- registry legal-mode decisions;
- registry последних evidence events;
- legal-mode decision details;
- evidence event details;
- explicit `VERIFY` explanation;
- Russian labels instead of raw enum values;
- integrity status and technical traceability details.

Admin surfaces также read-only: add/change/delete запрещены.

## MIGRATION

```text
src/apps/normatives/migrations/0002_normative_evidence.py
```

Migration создаёт две новые таблицы, индексы и partial unique constraints:

- correlation ID уникален в организации, когда не пуст;
- один `SIGNATURE` evidence event на `DocumentSignature`.

Historical migrations не переписывались. PostgreSQL migration chain и `makemigrations --check` проходят.

## FINAL CHANGED-FILE BOUNDARY

```text
docs/project/CURRENT_STATE.md
docs/work-items/NORMATIVE_EVIDENCE_001.md
src/apps/normatives/apps.py
src/apps/normatives/evidence.py
src/apps/normatives/evidence_admin.py
src/apps/normatives/evidence_models.py
src/apps/normatives/evidence_services.py
src/apps/normatives/evidence_signals.py
src/apps/normatives/migrations/0002_normative_evidence.py
src/apps/normatives/tests/test_evidence_contract.py
src/apps/normatives/tests/test_evidence_persistence.py
src/apps/normatives/urls.py
src/apps/normatives/views.py
src/templates/normatives/evidence_event_detail.html
src/templates/normatives/evidence_registry.html
src/templates/normatives/legal_mode_decision_detail.html
src/templates/normatives/registry.html
```

`pyproject.toml` был временно изменён только для диагностики Ruff и полностью восстановлен; в итоговый PR diff не входит.

Не изменены:

- OPJ/SHIFT/DEFECT lifecycle;
- imports/master-data implementation;
- equipment/dispatching foundations;
- accepted print geometry;
- deployment/preview configuration;
- product release scope.

## FOCUSED TEST COVERAGE

Проверяются:

- target/proven separation;
- non-`VERIFY` basis gates;
- five-type taxonomy and semantic non-substitution;
- deterministic digest and deep immutability;
- recursive secret rejection;
- invalid password rollback and absence of password in stored corpus;
- append-only update/delete rejection;
- other-organization local act rejection;
- correlation idempotency and conflicting reuse;
- simulated unique race recovery after savepoint;
- correction link behavior;
- raw database tamper detection;
- automatic `DocumentSignature → SIGNATURE EvidenceEvent` projection;
- tenant isolation in read-only views;
- Russian `VERIFY`/event labels;
- prohibition of user-created `LEGACY_MIGRATION`.

## ACCEPTANCE MAPPING

### AC-NORMATIVE-LEGAL-MODES-001

- target/proven/evidence/local-act states persisted separately;
- unsupported decision remains `VERIFY`;
- non-`VERIFY` without sufficient published basis rejected;
- local act cannot substitute official/industry basis and vice versa.

### AC-NORMATIVE-EVENTS-001

- all five event types persisted separately;
- payload requirements enforced per type;
- subject/actor/time/method/basis/digest traceable;
- historical records append-only;
- correction creates a new linked event.

### AC-NORMATIVE-PEP-001

- password re-auth required where declared;
- wrong password creates no event;
- password/secret/token fields never enter payload/canonical storage;
- existing `DocumentSignature` reused rather than duplicated;
- mechanism is not labelled УКЭП/УНЭП.

## TECHNICAL GATE

Code candidate `6ea0f26bfeadd8ab22d67284fd2971b0565fe25a` passed:

```text
Ruff: SUCCESS
Python compile: SUCCESS
Django system check: SUCCESS
migration consistency: SUCCESS
PostgreSQL migration chain: SUCCESS
architectural gate: SUCCESS
full Django suite: SUCCESS
repository-clean gate: SUCCESS
```

Final exact-head workflow state after coordination changes is recorded in Draft PR #41. The execution package intentionally does not embed its own commit SHA.

## OPEN VERIFY

The following remain intentionally unresolved and are not defects of this work item:

- applicability of a specific consolidated official act to a concrete enterprise workflow;
- existence/content/applicability of a concrete local act;
- authority-at-action evaluation;
- УКЭП/УНЭП, external certificates, timestamp authority;
- production retention/security/HA;
- subject-module lifecycle integration beyond existing `DocumentSignature` projection.

These items cannot be inferred from SHA-256, immutable rows, password re-authentication or vendor claims.

## RUNTIME / PREVIEW

```text
runtime deployment: NOT PERFORMED
accepted preview: UNTOUCHED
runtime impact before merge: NONE
```

## ACCEPTANCE STATE

```text
PREFLIGHT: COMPLETE
DOMAIN CONTRACT: COMPLETE
PERSISTENCE/SERVICES: COMPLETE
READ-ONLY ACCEPTANCE SURFACE: COMPLETE
MIGRATION: COMPLETE
FOCUSED TESTS: COMPLETE
FULL CODE GATE: SUCCESS
FINAL EXACT-HEAD GATE: RECORDED IN PR #41
TECHNICAL CANDIDATE: PREPARED
USER ACCEPTANCE: REQUIRED
READY FOR REVIEW: NO
MERGE: FORBIDDEN WITHOUT EXPLICIT USER COMMAND
```

## USER ACCEPTANCE CHECK

До Ready/Merge пользователь отдельно подтверждает:

1. корректность границы `target mode ≠ proven legal mode`;
2. корректность пяти самостоятельных evidence semantics;
3. допустимость append-only/read-only foundation как основы downstream workflows;
4. отсутствие ложного утверждения о юридической значимости или виде электронной подписи.

## REPORT FORMAT

```text
BASE
BRANCH
ISSUE
PR
EXACT HEAD
IMPLEMENTED SLICES
CHANGED FILE BOUNDARY
MIGRATION
FOCUSED TESTS
FULL GATE
RUNTIME
PREVIEW
OPEN VERIFY
ACCEPTANCE STATE
NEXT ACTION
```
