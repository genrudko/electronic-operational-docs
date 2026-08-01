# ЭОД — текущее состояние

**Дата factual check:** 02.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0
active work item: PERSONNEL-AUTHORITY-001
active issue: #42
active PR: PENDING
active branch: feature/personnel-authority-001
runtime impact: NONE
preview: UNTOUCHED
```

`MASTER-DATA-ALIGNMENT-001` принят пользователем и merged обычным merge commit `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb` из exact PR head `e507b63ab35a4767c25364d729accb9a741af874`. Issue #34 закрыт.

`NORMATIVE-EVIDENCE-001` принят пользователем 01.08.2026 и merged обычным merge commit `6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0` из exact PR head `24848d04984b61b0b183f3ed2b04117b3e05e5f9`. PR #41 закрыт как merged; issue #40 закрыт как completed. Финальный post-merge coordination tip до старта нового work item: `b209f3ed56dc86fa0250434fdc7b7ed802b9270f`.

Финальный exact-head gate PR #41 завершён успешно:

```text
AUTO-001A Foundation CI #500: SUCCESS
AUTO-001B Controller CI #484: SUCCESS
EOD Documentation Contract #586: SUCCESS
EOD Development Stack #589: SUCCESS
EOD CI #698: SUCCESS
```

Принятый normative/evidence контур разделяет product target и proven legal mode, хранит пять самостоятельных evidence semantics, использует append-only decisions/events, password re-authentication без сохранения секрета и существующий `DocumentSignature` без параллельного signature framework. Ни immutable model, ни SHA-256, ни re-auth сами по себе не доказывают юридическую значимость; неподтверждённые режимы остаются `VERIFY`.

`PERSONNEL-AUTHORITY-001` начат по issue #42 после factual preflight. Установлено, что модуль не создаётся с нуля: уже существуют employee/qualification/imported operational-right foundations. Текущий work item ограничен структурированными grants, external/seconded personnel semantics, authority-at-action evaluation и immutable authority snapshot; application role или должность сами по себе не разрешают controlled action.

До создания Draft PR runtime deployment не выполнялся; accepted preview остаётся `UNTOUCHED`. Merge, Ready for Review и preview write без отдельной команды пользователя запрещены.

С 01.08.2026 действует единый пользовательский контур: один активный чат ведёт work item от factual preflight до post-merge coordination. При технической смене чата новый исполнитель самостоятельно восстанавливает состояние из GitHub; пользователь не переносит между чатами handoff, SHA, CI-отчёты или команды.

Release/module/capability/work-item planning state остаётся в [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
