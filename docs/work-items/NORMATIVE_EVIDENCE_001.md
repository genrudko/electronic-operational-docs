# NORMATIVE-EVIDENCE-001 — final execution record

```text
work item: NORMATIVE-EVIDENCE-001
module: NORMATIVE-EVIDENCE
issue: #40 / CLOSED / COMPLETED
PR: #41 / MERGED
branch: feature/normative-evidence-001
starting main: c05ace785f054233aa878ddead491def47525140
accepted exact PR head: 24848d04984b61b0b183f3ed2b04117b3e05e5f9
merge commit: 6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0
merge method: ordinary merge commit
squash: NO
rebase: NO
user acceptance: ACCEPTED 01.08.2026
runtime deployment: NOT PERFORMED
accepted preview: UNTOUCHED
```

## Accepted capabilities

- `CAP-NORMATIVE-LEGAL-MODES` / `AC-NORMATIVE-LEGAL-MODES-001`;
- `CAP-NORMATIVE-EVENTS` / `AC-NORMATIVE-EVENTS-001`;
- `CAP-NORMATIVE-PEP` / `AC-NORMATIVE-PEP-001`.

## Accepted domain boundaries

1. `product_target_mode` and `proven_legal_mode` are separate fields and separate claims.
2. Unsupported legal conclusions remain `VERIFY`.
3. A non-`VERIFY` decision requires sufficient published normative evidence, a closed local-act gate and traceable basis.
4. `SIGNATURE`, `ACKNOWLEDGEMENT`, `INSTRUCTION`, `KNOWLEDGE_CHECK` and `ACTION_CONFIRMATION` are non-interchangeable event types.
5. Password re-authentication confirms the current account for the bounded prototype, stores no password and is not labelled УКЭП or УНЭП.
6. Historical legal-mode decisions and evidence events are append-only; corrections create linked records.
7. Existing `DocumentSignature`, canonical JSON, SHA-256 and identity snapshots are reused rather than duplicated.
8. Technical immutability, digest verification and successful CI do not by themselves establish legal significance.

## Implemented scope

### Domain contract

- product-target/proven-mode taxonomy;
- normative-evidence and local-act states;
- five evidence semantics with per-type payload requirements;
- immutable actor snapshots and payloads;
- canonical JSON and deterministic SHA-256;
- recursive secret-like field rejection;
- explicit confirmation methods and re-authentication semantics.

### Persistence and services

- append-only `LegalModeDecision`;
- append-only `EvidenceEvent`;
- organization/subject/actor snapshots and server time;
- published normative/local revision traceability;
- correlation idempotency and conflicting-reuse rejection;
- nested savepoint recovery for unique-key races;
- transactional rollback on invalid credentials, basis or contract;
- correction/supersedes links;
- tenant-bounded queries and tamper verification.

### Existing signature integration

A `post_save` projection creates exactly one `SIGNATURE` evidence event from an existing `DocumentSignature`, including snapshot digest, purpose and signature checksum. The existing document-signature subsystem remains the owner; no parallel cryptographic or authentication framework was introduced.

### Read-only acceptance surface

- tenant-bounded normative/evidence registry;
- legal-mode decision details;
- evidence-event details;
- Russian labels;
- explicit `VERIFY` explanation;
- integrity and traceability information;
- read-only admin surfaces.

## Migration

`src/apps/normatives/migrations/0002_normative_evidence.py` creates the two append-only tables, indexes and partial unique constraints for organization-scoped correlation IDs and one evidence projection per `DocumentSignature`.

Historical migrations were not rewritten.

## Changed-file boundary

The accepted PR changed 17 files limited to:

- `docs/project/CURRENT_STATE.md`;
- this work-item record;
- `src/apps/normatives/**`;
- `src/templates/normatives/**`.

No OPJ/SHIFT/DEFECT lifecycle, imports/master-data, equipment/dispatching, deployment, preview, print geometry or release-scope implementation was changed.

## Test coverage

Focused and full gates cover:

- target/proven separation and non-`VERIFY` basis gates;
- five-type semantic non-substitution;
- deterministic digest and deep immutability;
- recursive secret rejection;
- invalid-password rollback and absence of persisted credentials;
- append-only update/delete protection;
- tenant isolation;
- correlation idempotency, conflicting reuse and simulated race recovery;
- correction links;
- raw-database tamper detection;
- automatic `DocumentSignature → SIGNATURE EvidenceEvent` projection;
- Russian UI labels and read-only behavior.

## Final exact-head gate

```text
head: 24848d04984b61b0b183f3ed2b04117b3e05e5f9
AUTO-001A Foundation CI #500: SUCCESS
AUTO-001B Controller CI #484: SUCCESS
EOD Documentation Contract #586: SUCCESS
EOD Development Stack #589: SUCCESS
EOD CI #698: SUCCESS
```

EOD CI included Ruff, Python compilation, Django system checks, migration consistency, PostgreSQL migration chain, architectural gate, full Django suite, repository-clean verification and container preview smoke.

## Open VERIFY retained intentionally

- applicability of a specific consolidated official act to a concrete enterprise workflow;
- existence, content and applicability of concrete local acts;
- authority-at-action evaluation;
- УКЭП/УНЭП, external certificates and trusted timestamp services;
- production retention, security and HA;
- subject-module lifecycle integration beyond the accepted `DocumentSignature` projection.

These are downstream or evidence-dependent matters, not defects of the accepted bounded foundation.

## Final verdict

```text
TECHNICAL CANDIDATE: PASSED
USER ACCEPTANCE: ACCEPTED
PR: MERGED
ISSUE: CLOSED
MODULE RELEASE STATUS: ACCEPTED
MODULE CODE STATUS: IMPLEMENTED-ACCEPTED
RUNTIME: UNCHANGED
PREVIEW: UNTOUCHED
```

The next queued product work item is `PERSONNEL-AUTHORITY-001`; it requires a fresh factual preflight before issue, branch or PR activation.
