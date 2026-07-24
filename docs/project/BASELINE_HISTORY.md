# ЭОД — история принятых baseline

Baseline фиксируется только после технической и пользовательской приёмки соответствующего изменения.

| Дата | Baseline | Содержание | Доказательства |
|---|---|---|---|
| 2026-07-23 | `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f` | Patch 011.6.2 Repair 4 | 485 tests, один skipped, visual acceptance |
| 2026-07-24 | `fec8bd675f9565b0c4e398124cd22f8fabec02b4` | Patch 011.7 Repair 1 Revision 10 | 495 tests, один skipped, technical acceptance |
| 2026-07-24 | `bf986433ea33bf932f98925e7daf61b0199e23d0` | Patch 011.7 Repair 2 | source-bound forms boundary, technical and visual acceptance; tag `eod-baseline-011.7-repair2` |
| 2026-07-24 | `ded4571dcacd973184d3121b19c8db8c70e7b08a` | INFRA-002 accepted preview | PR #2, PostgreSQL preview, health and demo auth; tag `eod-baseline-infra-002` |
| 2026-07-24 | `abd6066885b060e3e3d2c39098fcaf640bb70416` | INFRA-003 isolated development | PR #3, CI, simultaneous preview/development health, database isolation, SSH tunnel acceptance |
| 2026-07-25 | `e18872face7f27f489056b72fed31e5586121b0c` | DOCS-001 project operating system | PR #4 squash merge, exact-head CI, user approval, preview main/health/HTTP/database identity/migration checks |

## Текущий accepted application baseline

```text
main / e18872face7f27f489056b72fed31e5586121b0c
```

Он включает INFRA-001–003 и принятый DOCS-001.

## Working branch

```text
docs/002-docs001-baseline-finalization
```

Ветка является metadata-only follow-up. Она фиксирует уже доказанный baseline и не меняет application behavior, schema, migrations or runtime data.

## Разделение application baseline и metadata follow-up

Accepted application baseline — merge commit изменения, которое прошло post-merge preview verification.

Последующий документационный commit, который только записывает уже известный merge SHA в history/current-state/release notes:

- не создаёт новый application baseline;
- не требует бесконечного follow-up для записи собственного SHA;
- остаётся частью `main` history;
- должен пройти documentation CI и обычный documentation-only post-merge health gate.

Новый application baseline появляется только после следующего принятого изменения, затрагивающего application, schema, data, runtime behavior или значимый operating-system milestone, для которого принято отдельное решение о baseline.

## Правило фиксации нового baseline

Нужны:

1. PR с известным exact head SHA;
2. зелёный актуальный CI;
3. профильные VPS checks, если меняется runtime;
4. пользовательская приёмка;
5. явное разрешение merge;
6. merge commit SHA;
7. синхронизация `/srv/eod/repository`;
8. preview health check;
9. database/migration/profile smoke по риску;
10. обновление `CURRENT_STATE.md`, `CURRENT_HANDOFF.md`, `ACCEPTANCE_HISTORY.md` и release notes.

Tag создаётся для значимого устойчивого рубежа, а не для каждого мелкого изменения.