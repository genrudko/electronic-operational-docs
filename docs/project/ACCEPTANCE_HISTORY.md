# ЭОД — история приёмок

Этот документ разделяет technical success, runtime evidence, предметную,
визуальную и integration acceptance. Он является историческим ledger и не
владеет active work item, current main, runtime или Preview state.

## Factual reconciliation ledger — 2026-08-05

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
