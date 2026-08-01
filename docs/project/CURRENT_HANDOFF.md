# Chat 0 — current handoff navigator

Volatile state: [`CURRENT_STATE.md`](CURRENT_STATE.md). Release/module state: [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml).

Принятый application baseline:

```text
main / 0d9be8c360ca22fc504ce2b11a14b6bb82c77ea5
UX-THEME-001 / issue #28 / PR #30 / ACCEPTED
accepted PR head: 93e30896f70ccc4bb4eaf9b4b71513e4ef188893
```

Согласованный process hardening опубликован direct-to-main commit:

```text
324fe43d040d8c7dbeadfcd4337a8919ba18a63d
```

Он добавляет executable preflight, `MICRO / STANDARD / SYSTEM`, пропорциональные checks, выбор delivery до публикации, optimistic-lock atomic publisher, stable handoff и retry/stall rules. Runtime, schema, data и preview не изменены.

Release plan синхронизирован: `accepted_main` указывает на merge PR #30; `CAP-UX-THEME` принят. UX остаётся `IN_PROGRESS` только из-за незакрытого `CAP-UX-RESPONSIVE`.

Активного product issue/branch/PR нет. Следующий work item по утверждённой очереди — `MASTER-DATA-ALIGNMENT-001`.

Следующее действие: factual preflight фактических organization/workplace/equipment/dispatch models, routes, import contracts и источников `REF-OD-013`, `REF-OD-020`, `REF-OD-021`; затем один issue / branch / Draft PR при verdict `READY TO IMPLEMENT`.
