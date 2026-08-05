# ЭОД — история принятых baseline

Baseline фиксируется после применимых technical gates, пользовательского решения
и merge. История не владеет текущим active state; volatile state находится
только в [`CURRENT_STATE.md`](CURRENT_STATE.md).

## Chronological baseline ledger

| Дата | Merge/baseline SHA | Содержание | Статус |
|---|---|---|---|
| 2026-07-23 | `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f` | Patch 011.6.2 Repair 4 | accepted historical |
| 2026-07-24 | `fec8bd675f9565b0c4e398124cd22f8fabec02b4` | Patch 011.7 Repair 1 Revision 10 | accepted historical |
| 2026-07-24 | `bf986433ea33bf932f98925e7daf61b0199e23d0` | Patch 011.7 Repair 2 | accepted historical |
| 2026-07-24 | `ded4571dcacd973184d3121b19c8db8c70e7b08a` | INFRA-002 | accepted historical |
| 2026-07-24 | `abd6066885b060e3e3d2c39098fcaf640bb70416` | INFRA-003 | accepted historical |
| 2026-07-25 | `e18872face7f27f489056b72fed31e5586121b0c` | DOCS-001 | accepted historical |
| 2026-07-25 | `4237aadc2cfdee518567024c2b45b653f49c16e7` | QUALITY-001 | accepted historical |
| 2026-07-25 | `937d2cd2b187c17fac3088ccfc52079fc4608306` | AUTO-000 | accepted historical |
| 2026-07-26 | `b75db8bc073e4b02a3254512e9b99d00f3e6e0e2` | PLAN-001 merge | accepted evidence baseline |
| 2026-07-27 | `883a108c8be2a8cd075846fdd175916917911ef6` | DEFECT-001 merge | accepted product slice |
| 2026-07-28 | `a880a632b750309c7fbfb918af15b49d99b5a93f` | UX-FOUNDATION-001 merge | accepted UX foundation |
| 2026-07-30 | `50d96842e8700540832210990993e64fc2e3636d` | OPJ-UX-001 merge | accepted product/UX baseline |
| 2026-07-30 | `2a9b92362b90861501cf11d073668478655fd191` | PROJECT-BASELINE-001 merge | accepted DEMO-RELEASE BASELINE V1.0 |
| 2026-08-01 | `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb` | MASTER-DATA-ALIGNMENT-001 merge | accepted bounded master-data slice |
| 2026-08-01 | `6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0` | NORMATIVE-EVIDENCE-001 merge | accepted normative/evidence module |
| 2026-08-02 | `2a2013a51bfdc9de602b095adcb28a51b8d4487e` | PERSONNEL-AUTHORITY-001 merge | accepted personnel/authority module |
| 2026-08-02 | `2db8947062434861d2336eb474cd762e11aabb44` | POST-MERGE-DEPLOY-VERIFY-001 carrier merge | accepted deployment verification carrier |
| 2026-08-04 | `c4e344342b647ce59a390a04329d2cadb1f34d7c` | OPJ-LIFECYCLE-001 merge | accepted OPJ lifecycle module |
| 2026-08-05 | `916a6d708ff4bd8433218068a204547b4a9abf84` | PROJECT-SUSTAINABILITY-001 merge | accepted industrialization evidence/program baseline |

## Reconciliation note — 2026-08-05

До `PROJECT-STATE-RECONCILIATION-001` release plan и derived views не отражали
часть уже принятых merge events. Эта запись сохраняет факт прежнего drift и не
делает вид, будто расхождения не существовало.

Canonical current state не выводится из последней строки таблицы: его всегда
нужно читать в `CURRENT_STATE.md`. Planning status и accepted work-item evidence
принадлежат `DEMO_RELEASE_PLAN.yaml`.
