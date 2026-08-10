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
| 2026-08-05 | `9d6d48ad25d45cd79673c7017980a8bd92fa961a` | PROJECT-STATE-RECONCILIATION-001 merge | accepted canonical-state and documentation-drift protection baseline |
| 2026-08-05 | `3c02c5c05cdf604bbf230d215b82ddd875ab1421` | INDUSTRIALIZATION-PROGRAM-EXECUTION-001 merge | accepted executable backlog and Phase 0 completion baseline |
| 2026-08-06 | `95b8dd6017745886f110f052ea0950b3d48173d8` | SECRET-HYGIENE-001 merge | accepted credential-hygiene and CI leak-prevention baseline |
| 2026-08-10 | `5b54446d632ef1839d530dc2945255b3033359fe` | DEPENDENCY-PROVENANCE-001 merge | accepted reproducible dependency/build provenance baseline |
| 2026-08-10 | `1f3296bcf3d0f57bd088241c81691c7f54b2ac25` | DEPLOYMENT-PROFILE-001 merge | accepted fail-closed pilot/production deployment-profile baseline |
| 2026-08-10 | `3e43422ba6000c2aa5f4bdc6abe0f95c7774454f` | MODULE-ACTIVATION-CONTRACT-001 merge | accepted module-activation architecture baseline |

## Reconciliation note — 2026-08-10 / Module Activation

`MODULE-ACTIVATION-CONTRACT-001` принят по exact head
`6025d7b405bc1d88543dc341757e5685bcf05b98` и merged в
`3e43422ba6000c2aa5f4bdc6abe0f95c7774454f`; issue #61 закрыт как `COMPLETED`,
owner acceptance — `PASSED`. Canonical planning state переведён в `ACCEPTED`
согласованно со стартом `BACKUP-RESTORE-DRILL-001`. Два последующих
документационных cleanup-коммита довели live `main` до
`071ac654ba6c10f5846052551024e8d24941e9e9`, при этом content diff относительно
accepted merge commit равен нулю. После перехода `SAFE-CONTINUATION` имеет 6 из
8 принятых элементов; предметная очередь остаётся paused, `SHIFT-HANDOVER-001`
не стартовал.

## Reconciliation note — 2026-08-10 / Deployment Profile

`DEPLOYMENT-PROFILE-001` принят по exact head
`323f4fb9162e84ca25a49556340078de81af2424` и merged в
`1f3296bcf3d0f57bd088241c81691c7f54b2ac25`. Canonical planning state переведён
в `ACCEPTED` согласованно со стартом `MODULE-ACTIVATION-CONTRACT-001`; история
предыдущих baseline не переписывалась. После этого `SAFE-CONTINUATION` имеет 5
из 8 принятых элементов, а предметная очередь остаётся paused.

## Reconciliation note — 2026-08-10

`DEPENDENCY-PROVENANCE-001` принят по exact head
`0f0e92522e7a2c5d43dd635ed661c65ed5021422` и merged в
`5b54446d632ef1839d530dc2945255b3033359fe`. Canonical planning state переведён
в `ACCEPTED` атомарно со стартом `DEPLOYMENT-PROFILE-001`; история не
переписывалась. После этого `SAFE-CONTINUATION` имеет 4 из 8 принятых элементов,
а предметная очередь остаётся paused.

## Reconciliation note — 2026-08-06

До `PROJECT-STATE-RECONCILIATION-001` release plan и derived views не отражали
часть уже принятых merge events. Эта запись сохраняет факт прежнего drift и не
делает вид, будто расхождения не существовало.

После принятия `PROJECT-STATE-RECONCILIATION-001` canonical release-plan data,
source/scenario/post-demo mappings, current-state contract и deterministic views
защищены постоянными fail-closed validators.

После принятия `INDUSTRIALIZATION-PROGRAM-EXECUTION-001` Phase 0 завершена,
industrial backlog стал исполнимым и проверяемым, а прогресс gates и residual
risks защищён постоянным Documentation Contract.

После принятия `SECRET-HYGIENE-001` reusable credentials удалены из актуального
repository/CI/artifact контура, canonical scanner и post-redaction verification
стали постоянными fail-closed gates. Это не означает достижения
`SAFE-CONTINUATION`: принято 3 из 8 его обязательных work items.

Canonical current state не выводится из последней строки таблицы: его всегда
нужно читать в `CURRENT_STATE.md`. Planning status и accepted work-item evidence
принадлежат `DEMO_RELEASE_PLAN.yaml`.
