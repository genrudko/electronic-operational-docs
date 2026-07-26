# ЭОД — история принятых baseline

Baseline фиксируется после применимых technical gates, пользовательского
решения и post-merge/runtime verification.

| Дата | SHA | Содержание | Доказательства |
|---|---|---|---|
| 2026-07-23 | `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f` | Patch 011.6.2 Repair 4 | 485 tests, visual acceptance |
| 2026-07-24 | `fec8bd675f9565b0c4e398124cd22f8fabec02b4` | Patch 011.7 Repair 1 Revision 10 | 495 tests, technical acceptance |
| 2026-07-24 | `bf986433ea33bf932f98925e7daf61b0199e23d0` | Patch 011.7 Repair 2 | Source-bound boundary, technical/visual acceptance |
| 2026-07-24 | `ded4571dcacd973184d3121b19c8db8c70e7b08a` | INFRA-002 | PostgreSQL preview and demo auth |
| 2026-07-24 | `abd6066885b060e3e3d2c39098fcaf640bb70416` | INFRA-003 | Isolated development and DB separation |
| 2026-07-25 | `e18872face7f27f489056b72fed31e5586121b0c` | DOCS-001 | Project operating system |
| 2026-07-25 | `4237aadc2cfdee518567024c2b45b653f49c16e7` | QUALITY-001 | Full PostgreSQL suite restored |
| 2026-07-25 | `937d2cd2b187c17fac3088ccfc52079fc4608306` | AUTO-000 accepted application baseline | Contract accepted; preview post-merge verified |
| 2026-07-25 | `21e101f957808d744052da99709d63f1410b7bc3` | AUTO-001B merge | Restricted VPS controller implementation |
| 2026-07-26 | `37a2390a2a45e2abb73e60318d5429ed326efb53` | AUTO-001A/B accepted current main | Trusted controller practically verified; validator repair merged |

## Current main

```text
main / 37a2390a2a45e2abb73e60318d5429ed326efb53
```

## Accepted application baseline

```text
main history point / 937d2cd2b187c17fac3088ccfc52079fc4608306
```

AUTO-001A/B изменили infrastructure/workflow/runtime controller, но не
product behavior или domain schema. Поэтому accepted application baseline
остаётся `937d2cd…`, а current main history HEAD — `37a2390…`.

## PLAN-001 evidence

Evidence run принят, но PR #7 не является baseline:

```text
evidence exact head:
fb313f270254720b0f7d7815fffc2cb05d577901

evidence ZIP SHA-256:
58df47f83d1758d2e6aa8b32e1d5a70efb8c453454d8759e25d913e7f031619a

PR state:
OPEN / DRAFT / NOT MERGED
```

После narrow repair будет новый exact head и один последний evidence run.
Baseline изменится только после отдельного merge decision и post-merge gate.

## Правило нового baseline

1. exact PR head;
2. current-head CI;
3. профильные VPS gates;
4. user acceptance/decision;
5. explicit merge authorization;
6. merge commit;
7. preview sync if applicable;
8. health/database/migration/source checks;
9. canonical docs/history.

Metadata-only commit не создаёт application baseline только из-за собственного
SHA. Tag создаётся для устойчивого значимого рубежа.
