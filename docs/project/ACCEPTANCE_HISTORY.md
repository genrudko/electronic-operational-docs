# ЭОД — история приёмок

Этот документ разделяет technical success, runtime evidence, предметную,
визуальную и integration acceptance. Он является историческим ledger и не
владеет active work item, current main, runtime или Preview state.

## Factual reconciliation ledger — 2026-08-10

| Work item | PR | Accepted/final exact head | Merge commit | Acceptance |
|---|---:|---|---|---|
| `PLAN-001` | #7 | `fb313f270254720b0f7d7815fffc2cb05d577901` evidence head | `b75db8bc073e4b02a3254512e9b99d00f3e6e0e2` | evidence and integration accepted |
| `DEFECT-001` | #16 | `79f3db7e5c47e1ac8ab2568028d06e4043c2c70e` final PR head; accepted candidate `0692012d735447908ae2839f9d6254b8fac89b52` | `883a108c8be2a8cd075846fdd175916917911ef6` | product/UX accepted |
| `PROJECT-BASELINE-001` | #27 | `8c2b08f3c9e873640f8a4e6c5334294ccfce611d` | `2a9b92362b90861501cf11d073668478655fd191` | DEMO-RELEASE BASELINE V1.0 accepted |
| `UX-THEME-001` | #30 | `93e30896f70ccc4bb4eaf9b4b71513e4ef188893`; accepted candidate `8aeb5296d3d13338d79aec6fbb27b16c39325573` | `0d9be8c360ca22fc504ce2b11a14b6bb82c77ea5` | bounded theme slice accepted |
| `MASTER-DATA-ALIGNMENT-001` | #35 | `e507b63ab35a4767c25364d729accb9a741af874` | `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb` | bounded master-data slice accepted |
| `NORMATIVE-EVIDENCE-001` | #41 | `24848d04984b61b0b183f3ed2b04117b3e05e5f9` | `6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0` | module accepted |
| `PERSONNEL-AUTHORITY-001` | #43 | `d659ab949db2942c064eec3c298d031a9684c67d` | `2a2013a51bfdc9de602b095adcb28a51b8d4487e` | module accepted |
| `POST-MERGE-DEPLOY-VERIFY-001` | #45 | `e8b053f5fda51f23e2506a1a45a405f5c2ee3b6c` | `2db8947062434861d2336eb474cd762e11aabb44` | development deployment carrier accepted; Preview untouched |
| `OPJ-LIFECYCLE-001` | #47 | `65997a9d51de4d066ec07277d4c660bfc307650e` | `c4e344342b647ce59a390a04329d2cadb1f34d7c` | module accepted in Microsoft Edge development profile |
| `PROJECT-SUSTAINABILITY-001` | #49 | `cdf3238ca986761dbecc61a60bd28941ff8219ac` | `916a6d708ff4bd8433218068a204547b4a9abf84` | audit and industrialization program accepted |
| `PROJECT-STATE-RECONCILIATION-001` | #51 | `a6534a5fb2e5ae59bfba6cd36e9e80ebc69801d6` | `9d6d48ad25d45cd79673c7017980a8bd92fa961a` | canonical state reconciliation and fail-closed documentation drift protection accepted |
| `INDUSTRIALIZATION-PROGRAM-EXECUTION-001` | #53 | `9eec9b94392df45b44e7ad4165e8c76d06d05b36` | `3c02c5c05cdf604bbf230d215b82ddd875ab1421` | executable backlog, gate ownership and residual-risk contract accepted; Phase 0 completed |
| `SECRET-HYGIENE-001` | #56 | `cd7dc07a9c77a71a5b1166aa7a57ee4d3afa93da` | `95b8dd6017745886f110f052ea0950b3d48173d8` | credential hygiene, CI leak prevention and fail-closed publication contract accepted |
| `DEPENDENCY-PROVENANCE-001` | #58 | `0f0e92522e7a2c5d43dd635ed661c65ed5021422` | `5b54446d632ef1839d530dc2945255b3033359fe` | reproducible dependency/build provenance and exact-head Sigstore/OIDC evidence accepted |
| `DEPLOYMENT-PROFILE-001` | #60 | `323f4fb9162e84ca25a49556340078de81af2424` | `1f3296bcf3d0f57bd088241c81691c7f54b2ac25` | fail-closed pilot/production deployment profile accepted; Preview untouched |
| `MODULE-ACTIVATION-CONTRACT-001` | #62 | `6025d7b405bc1d88543dc341757e5685bcf05b98` | `3e43422ba6000c2aa5f4bdc6abe0f95c7774454f` | modular-monolith activation architecture contract accepted; Preview untouched |

### Why two heads appear for some historical PRs

For `DEFECT-001` and `UX-THEME-001`, user acceptance occurred on a bounded
candidate before later branch synchronization/coordination. The ledger retains
both the accepted candidate and the actual final PR head instead of collapsing
them into one misleading SHA.

### Corrected historical snapshot

The older acceptance document contained a period snapshot where PR #7 was still
`OPEN / DRAFT / NOT MERGED`. That statement was true at the time of the snapshot
but became stale after the later accepted merge. It is superseded by the ledger
above; the existence of the earlier contradiction is explicitly preserved here.

## MODULE-ACTIVATION-CONTRACT-001 exact-head evidence

```text
EOD CI:                      31374071063 / SUCCESS
AUTO-001A Foundation CI:     31374071062 / SUCCESS
AUTO-001B Controller CI:     31374071036 / SUCCESS
EOD Documentation Contract: 31374071030 / SUCCESS
EOD Development Stack:      31374071025 / SUCCESS
EOD Secret Hygiene:          31374071050 / SUCCESS
EOD Dependency Provenance:   31374071027 / SUCCESS
```

Accepted exact head `6025d7b405bc1d88543dc341757e5685bcf05b98` was merged as
`3e43422ba6000c2aa5f4bdc6abe0f95c7774454f`; issue #61 is `CLOSED / COMPLETED`
and owner acceptance is `PASSED`. Accepted scope: canonical module manifest,
lifecycle, scoped precedence, dependency/integration semantics, universal access
decision, retained history/reactivation, migration boundary and activation audit.
Runtime and Preview were untouched. Two later main cleanup commits have zero
content diff relative to the accepted merge tree and are not reinterpreted here.

## DEPLOYMENT-PROFILE-001 exact-head evidence

```text
EOD CI:                      31362143450 / SUCCESS
AUTO-001A Foundation CI:     31362143473 / SUCCESS
AUTO-001B Controller CI:     31362143425 / SUCCESS
EOD Documentation Contract: 31362143445 / SUCCESS
EOD Development Stack:      31362143454 / SUCCESS
EOD Dependency Provenance:   31362143446 / SUCCESS
EOD Deployment Profile:      31362143422 / SUCCESS
EOD Secret Hygiene:          31362143415 / SUCCESS
```

Accepted exact head `323f4fb9162e84ca25a49556340078de81af2424` was merged as
`1f3296bcf3d0f57bd088241c81691c7f54b2ac25`. Accepted scope: fail-closed
pilot/production configuration, PostgreSQL-only pilot/production semantics,
operator preflight, secure TLS/reverse-proxy/session settings and separated
liveness/readiness checks. Runtime and Preview were untouched.

## DEPENDENCY-PROVENANCE-001 exact-head evidence

```text
EOD CI:                      31338914564 / SUCCESS
AUTO-001A Foundation CI:     31338914521 / SUCCESS
AUTO-001B Controller CI:     31338914515 / SUCCESS
EOD Documentation Contract: 31338914511 / SUCCESS
EOD Development Stack:      31338914549 / SUCCESS
EOD Secret Hygiene:          31338914517 / SUCCESS
EOD Dependency Provenance:   31338914527 / SUCCESS
```

Accepted exact head `0f0e92522e7a2c5d43dd635ed661c65ed5021422` was merged as
`5b54446d632ef1839d530dc2945255b3033359fe`. Accepted scope: five hashed lock
projections, pinned OCI/action inputs, SPDX 2.3 JSON SBOM, in-toto/SLSA
provenance and GitHub OIDC/Sigstore identity evidence. Runtime and Preview were
untouched. This ledger records immutable acceptance evidence and does not
re-audit the accepted supply-chain architecture.

## SECRET-HYGIENE-001 exact-head evidence

```text
EOD CI:                      31078274329 / SUCCESS
AUTO-001A Foundation CI:     31078274333 / SUCCESS
AUTO-001B Controller CI:     31078274321 / SUCCESS
EOD Documentation Contract: 31078274328 / SUCCESS
EOD Development Stack:      31078274307 / SUCCESS
EOD Secret Hygiene:          31078274346 / SUCCESS
full Django suite:           720 tests / OK
focused regressions:         17 tests / OK
tracked scan:                854 files / 0 findings / allowlist 0
clean tree:                  CLEAN_TREE=PASS porcelain_entries=0
bounded history:             250 commits / 18 unique findings
```

Accepted: removal of broad test/fixture exemptions, process-local generated test
credentials, one canonical scanner engine, exact allowlist semantics,
post-redaction verification before log/summary/artifact publication, verified
artifact gating, exact-head checkout checks and fail-closed clean-tree
verification. Blind VPS/external rotation was not performed and live Preview was
untouched.

## INDUSTRIALIZATION-PROGRAM-EXECUTION-001 exact-head evidence

```text
AUTO-001A Foundation CI:     31042144285 / SUCCESS
AUTO-001B Controller CI:     31042144940 / SUCCESS
EOD Documentation Contract: 31042145190 / SUCCESS
EOD Development Stack:      31042145205 / SUCCESS
EOD CI:                      31042145787 / SUCCESS
focused regressions:         23 tests / OK
```

Accepted: executable metadata for all 30 work items, coverage of all 34 risks,
state transitions, dependency and parallelization controls, deterministic gate
progress, residual-risk ownership/expiry contract, one positive and 20 negative
fixtures, and permanent Documentation Contract enforcement. Phase 0 is complete;
`SAFE-CONTINUATION` is not achieved and the domain queue remains paused.

## PROJECT-STATE-RECONCILIATION-001 exact-head evidence

```text
EOD Documentation Contract: 31028053053 / SUCCESS
AUTO-001A Foundation CI:     31028054968 / SUCCESS
AUTO-001B Controller CI:     31028054494 / SUCCESS
EOD Development Stack:      31028054190 / SUCCESS
EOD CI:                      31028053507 / SUCCESS
focused regressions:         21 tests / OK
```

Accepted: schema-2 compatible superset of the canonical release plan, preserved
source/scenario/post-demo data, restored schema-1 guarantees, strict current-state
contract, global single-owner scan, generated planning views, industrialization
gate/dependency checks and all-module status projection. Runtime and Preview were
untouched.

## PROJECT-SUSTAINABILITY-001 exact-head evidence

```text
EOD Documentation Contract: 31002573221 / SUCCESS
AUTO-001B Controller CI:     31002572719 / SUCCESS
AUTO-001A Foundation CI:     31002572760 / SUCCESS
EOD Development Stack:      31002573298 / SUCCESS
EOD CI:                      31002573388 / SUCCESS
full suite:                  716 tests / OK
```

Accepted: 34-risk register, 8 phases, 30 work items, `SAFE-CONTINUATION`,
`PILOT-READY`, mandatory core of 21 work items, scope-triggered UX foundation
and page templates, and browser gates without a hidden general UX dependency.
This acceptance does not mean either gate has been achieved.

## OPJ-LIFECYCLE-001 exact-head evidence

```text
AUTO-001A Foundation CI:     30986956669 / SUCCESS
AUTO-001B Controller CI:     30986956714 / SUCCESS
EOD Development Stack:      30986956637 / SUCCESS
EOD Documentation Contract: 30986956684 / SUCCESS
EOD CI:                      30986956738 / SUCCESS
```

Accepted: immutable registration, historical correction/cancellation, OPJ
communication facts, accepted PZ/ZN chronology, stable screen/print form,
reference previews, Edge actions menu and upper-aligned first column.

## Earlier infrastructure/process acceptances

| Этап | Статус | Ключевое доказательство |
|---|---|---|
| Patch 011.6.2 Repair 4 | Technical + visual accepted | 485 tests |
| Patch 011.7 Repair 1 Revision 10 | Technical accepted, then repaired | 495 tests |
| Patch 011.7 Repair 2 | Technical + visual accepted | source-bound forms boundary |
| INFRA-001 | Accepted | Linux/Python/PostgreSQL CI |
| INFRA-002 | Accepted | healthy preview, `eod_preview`, HTTP 200 |
| INFRA-003 | Accepted | isolated `eod-development`, `eod_development` |
| DOCS-001 | Accepted | canonical project operating system |
| DOCS-002 | Accepted | baseline metadata |
| DOCS-003 | Provisional accepted | UX v0.3, no visual acceptance |
| QUALITY-001 | Technical accepted | `497/497 OK` |
| AUTO-000 | Accepted | automation contract and security boundary |
| AUTO-001A/B | Accepted/practically verified | exact-SHA development controller, no automatic merge |

## Interpretation rule

Technical success, user acceptance, merge and post-merge deployment are distinct
events. Historical records may contain earlier candidate snapshots; current
status must never be inferred from them. Use `CURRENT_STATE.md` for volatile
coordination and `DEMO_RELEASE_PLAN.yaml` for planning status.
