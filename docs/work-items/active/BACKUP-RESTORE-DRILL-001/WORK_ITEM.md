# BACKUP-RESTORE-DRILL-001

This file is a non-canonical work-item brief. Mutable execution state remains owned by `docs/project/DEMO_RELEASE_PLAN.yaml`; volatile project state remains owned by `docs/project/CURRENT_STATE.md`.

## Purpose

Prove that an EOD PostgreSQL backup is a usable recovery point rather than merely a dump file. The acceptance result must be reproducible, fail closed, non-secret and suitable for `SAFE-CONTINUATION` evidence without modifying live Preview/VPS data.

## Starting baseline

`MODULE-ACTIVATION-CONTRACT-001` has been accepted and merged from PR #62.

Accepted module-activation exact head: `6025d7b405bc1d88543dc341757e5685bcf05b98`.
Accepted merge commit: `3e43422ba6000c2aa5f4bdc6abe0f95c7774454f`.
Issue #61 is closed/completed.

A transient documentation-only placeholder was accidentally created and immediately removed after that merge. Current `main` at contour creation is `071ac654ba6c10f5846052551024e8d24941e9e9`; compare from the accepted merge commit to that `main` has zero changed files, so the repository tree is identical to the accepted PR #62 baseline.

The canonical state inherited from `main` still describes `MODULE-ACTIVATION-CONTRACT-001` as active. The first substantive change in this work item must atomically record its acceptance and move this work item to `IN_PROGRESS` in the canonical owners and regenerated projections.

## Risks addressed

### PSR-015 / CRITICAL / Backup & DR

The repository has a backup/restore runbook, but there is no accepted periodic restore certificate and no approved retention/RPO/RTO/off-host recovery contract. A backup may exist yet be unusable when needed.

Required treatment: controlled restore, explicit off-host copy/encryption/retention policy, measurable RPO/RTO targets and a repeatable verification schedule.

### PSR-013 / HIGH boundary / Migrations

CI proves migrations on a clean PostgreSQL database but does not rehearse upgrades of accepted database snapshots. This work item establishes a trustworthy accepted backup/restore substrate for later migration rehearsal. It must not expand into `MIGRATION-SAFETY-001` or claim N-1/N/N-2 upgrade compatibility.

## Required first atomic canonical transition

Before claiming disaster-recovery execution evidence:

1. independently verify live GitHub state for current `main`, PR #62, issue #61 and this work item contour;
2. change `MODULE-ACTIVATION-CONTRACT-001` from `IN_PROGRESS` to `ACCEPTED` in the canonical execution owner with immutable acceptance evidence:
   - PR #62;
   - accepted exact head `6025d7b405bc1d88543dc341757e5685bcf05b98`;
   - accepted merge commit `3e43422ba6000c2aa5f4bdc6abe0f95c7774454f`;
   - owner acceptance PASSED;
   - final exact-head applicable GitHub workflow evidence;
3. move `BACKUP-RESTORE-DRILL-001` from `NOT_STARTED` to `IN_PROGRESS`;
4. update `CURRENT_STATE.md` to the current accepted-main baseline and this issue/PR/branch without creating a second state owner;
5. append immutable acceptance/baseline history for PR #62 while preserving older entries;
6. regenerate every deterministic planning/progress view using repository generators;
7. preserve the paused domain queue and keep `SHIFT-HANDOVER-001` not started.

Expected post-transition projection: `SAFE-CONTINUATION` has 6/8 accepted items and this work item is in progress.

## Architecture and operational boundaries

### PostgreSQL backup identity

Use the accepted PostgreSQL deployment model. Every recovery point used by the drill must carry enough non-secret evidence to prevent restoring an arbitrary similarly named file: source profile/class, database identity, timestamp, application/ref identity where applicable, file size and SHA-256 checksum.

### Explicit restore target

Restore must always target a newly created/disposable recovery database or another explicitly approved isolated target. Wrong, ambiguous or live Preview/pilot/production target identity must fail closed before destructive restore operations. The drill must prove target-identity checks rather than rely on operator memory.

### Isolation

The acceptance drill must not require destructive operations against live Preview/VPS. CI or another disposable PostgreSQL target is preferred. An isolated development recovery contour is acceptable only when target identity is explicitly guarded.

### Representative data and invariants

The source backup must contain deterministic representative EOD data sufficient to prove more than an empty-schema restore. Verification must include at minimum:

- `pg_restore --list` or equivalent structural readability;
- successful restore into a clean target;
- migrations/system check on the restored target where appropriate;
- database identity verification;
- representative object counts;
- accepted integrity/domain checks that are safe and already available;
- application health/readiness against the restored target where feasible;
- proof that source backup and restored evidence correspond to the same recovery point.

Do not introduce a fake domain model solely for the drill.

### Restore certificate

Produce a machine-readable, non-secret restore certificate from the exact acceptance run. It must capture at minimum:

- certificate schema/version;
- source backup identity without credentials;
- source/ref/commit identity where applicable;
- dump checksum and size;
- PostgreSQL/tool versions relevant to recovery;
- recovery-target class, never secrets;
- measured restore duration;
- restore result;
- migration/system-check result;
- representative counts/integrity result;
- owner-level RPO/RTO targets plus measured drill duration;
- evidence that checksum verification occurred before restore;
- evidence that target identity guard passed;
- overall PASS/FAIL;
- deterministic certificate verification/checksum evidence where appropriate.

A certificate must not contain database passwords, Django secret keys, tokens, raw dump bytes or sensitive production data.

### RPO/RTO

Define explicit owner-level RPO and RTO targets for future pilot/production-capable operation. They must be realistic for the current single-product PostgreSQL architecture and clearly distinguished from measured CI/drill duration. Do not present a CI restore time as a guaranteed production RTO.

### Retention, off-host copies and encryption

Replace the current "retention not yet approved" gap with an explicit policy suitable for the current maturity stage. Define:

- which recovery points are retained and for how long;
- minimum number/frequency of recent backups;
- off-host requirement so server loss does not destroy all backups;
- encryption-at-rest and encryption-in-transit expectations;
- who may access, restore or delete backup material;
- deletion rules preventing removal of the last verified recovery point;
- restore-verification cadence;
- how pilot/production storage credentials and locations remain external to Git.

Repository work may define and test the contract without provisioning a real external backup provider. Any external-storage property not actually tested must remain an explicit operational deployment requirement rather than being reported as proven.

### Repeatability and fail-closed behavior

Prefer one canonical repository entry point for the drill/verification instead of several divergent scripts. Negative evidence must cover at least:

- missing backup;
- empty/truncated/unreadable backup;
- checksum mismatch;
- wrong or ambiguous restore-target identity;
- restore command failure;
- missing expected representative data/counts;
- failed integrity/system check;
- attempted certificate publication containing prohibited secret material or raw dump content;
- stale or invalid certificate evidence where applicable.

Do not weaken existing secret-hygiene or provenance gates to publish disaster-recovery evidence.

### Schedule boundary

Define the intended recurring backup and restore-verification cadence for pilot/production operation. Do not introduce heavyweight external orchestration merely to satisfy this work item. A scheduled GitHub workflow for a non-secret synthetic restore drill is acceptable only if it remains risk-based and never requires production secrets or data.

## Acceptance criteria

The work item is technically ready for owner acceptance only when all are true:

1. the first canonical transition is internally consistent and generated views are deterministic;
2. there is one documented canonical backup/restore drill path;
3. a real PostgreSQL backup containing representative EOD data is created in an isolated acceptance environment;
4. its checksum is verified before restore;
5. restore into an explicitly identified clean target succeeds;
6. post-restore application/data/integrity checks succeed;
7. a machine-readable non-secret restore certificate is generated and independently validated;
8. negative tests fail closed for corrupted, wrong-target and invalid-evidence cases;
9. RPO/RTO, retention, off-host and encryption policy boundaries are explicit;
10. the work does not claim migration compatibility, release rollback, production external-storage provisioning or live-disaster recovery that was not actually tested;
11. live Preview/VPS remains untouched unless separately and explicitly authorised;
12. one final common exact head has `behind_by: 0` and all applicable exact-head gates are green;
13. the PR remains Draft and unmerged until explicit product-owner acceptance.

## Evidence expected at final acceptance

- exact final head and current main;
- compare / `behind_by`;
- changed-file boundary;
- final exact-head workflow run IDs/results;
- canonical restore-drill entry point;
- restore certificate and verifier result;
- dump checksum/size represented only as safe evidence;
- measured drill duration plus separately stated RPO/RTO targets;
- representative pre/post restore counts/invariants;
- negative fail-closed test results;
- confirmation that no raw dump or secret was committed/published;
- confirmation that live Preview/VPS was untouched;
- residual limitations handed to `MIGRATION-SAFETY-001`, `RELEASE-ROLLBACK-001` and later pilot/support work.

## Risk-based test policy

During implementation use focused backup/restore/contract checks. Do not repeatedly run the full heavy suite after every small edit. Existing repository workflows remain enabled. Require one final common exact head with all applicable gates green.

## Out of scope

- `SECURITY-BASELINE-001` beyond controls directly necessary to protect backup evidence;
- `MIGRATION-SAFETY-001` upgrade matrix/rehearsal;
- `MODULE-MIGRATION-COMPATIBILITY-001`;
- `RELEASE-ROLLBACK-001`;
- `DATA-PORTABILITY-001`;
- provisioning a production object-storage vendor/account;
- high-availability PostgreSQL, streaming replication or Kubernetes;
- destructive restore of live Preview/pilot/production;
- product/domain feature changes, UX work or new journals;
- Ready for Review or merge before explicit owner acceptance.

## Stop condition

Stop at a technically complete Draft PR with deterministic restore evidence and all applicable exact-head gates green. Do not merge.