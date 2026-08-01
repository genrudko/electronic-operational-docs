# ЭОД — текущее состояние

**Дата factual check:** 01.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb
active work item: NORMATIVE-EVIDENCE-001
active issue: #40
active PR: #41 / OPEN / DRAFT / NOT MERGED
active branch: feature/normative-evidence-001
runtime impact: NONE
preview: UNTOUCHED
```

Current main tip at work-item start: `c05ace785f054233aa878ddead491def47525140`.

`MASTER-DATA-ALIGNMENT-001` принят пользователем и merged обычным merge commit `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb` из exact PR head `e507b63ab35a4767c25364d729accb9a741af874`. Issue #34 закрыт.

`NORMATIVE-EVIDENCE-001` восстановлен и выполнен непосредственно по фактическому GitHub. Issue #40 и Draft PR #41 остаются открыты. Реализованы pure domain contract, append-only persistence, transactional services, автоматическая проекция существующего `DocumentSignature` в отдельное `SIGNATURE` evidence-событие, tenant-bounded read-only registry/details и focused tests.

Кодовый candidate `6ea0f26bfeadd8ab22d67284fd2971b0565fe25a` прошёл Ruff, compile, Django system check, migration consistency, PostgreSQL migration chain, architectural gate, полный Django suite и repository-clean gate. Финальный exact-head workflow state после coordination-коммита хранится в PR #41, чтобы этот документ не содержал самоссылочный SHA.

Ни один non-`VERIFY` legal mode не считается доказанным только из-за immutable model, SHA-256, password re-authentication либо успешного CI. Non-`VERIFY` требует отдельной опубликованной нормативной редакции и закрытого local-act gate. Подпись, ознакомление, инструктаж, проверка знаний и подтверждение действия не взаимозаменяемы.

Пользовательская приёмка `NORMATIVE-EVIDENCE-001` ещё не выполнена. До явного принятия запрещены Ready for Review, auto-merge и merge. Runtime deployment не выполнялся; accepted preview остаётся `UNTOUCHED`.

С 01.08.2026 действует единый пользовательский контур: один активный чат ведёт work item от factual preflight до post-merge coordination. При технической смене чата новый исполнитель самостоятельно восстанавливает состояние из GitHub; пользователь не переносит между чатами handoff, SHA, CI-отчёты или команды.

Release/module/capability/work-item planning state остаётся в [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
