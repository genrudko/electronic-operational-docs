# ЭОД — текущее состояние

**Дата factual check:** 02.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0
active work item: PERSONNEL-AUTHORITY-001
active issue: #42
active PR: #43 / OPEN / DRAFT / NOT MERGED
active branch: feature/personnel-authority-001
runtime impact: NONE
preview: UNTOUCHED
```

`MASTER-DATA-ALIGNMENT-001` принят пользователем и merged обычным merge commit `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb` из exact PR head `e507b63ab35a4767c25364d729accb9a741af874`. Issue #34 закрыт.

`NORMATIVE-EVIDENCE-001` принят пользователем 01.08.2026 и merged обычным merge commit `6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0` из exact PR head `24848d04984b61b0b183f3ed2b04117b3e05e5f9`. PR #41 закрыт как merged; issue #40 закрыт как completed.

`PERSONNEL-AUTHORITY-001` начат по issue #42 и Draft PR #43 после factual preflight. Модуль не создаётся с нуля: переиспользованы employee/qualification/imported operational-right foundations. Application role, должность, квалификация, site authorization, imported marker и operational grant разделены.

Реализованы:

- pure authority contract с `ALLOW / DENY / VERIFY`, stable reasons, structured scope, validity и basis;
- persistent `OperationalAuthorityGrant`, external engagement и bounded substitution поверх существующей модели персонала;
- server-side action-time evaluator и append-only `AuthorityEvaluationRecord` с correction link, immutable snapshot и SHA-256;
- controlled qualification codes без превращения русского free text в authorization token;
- read-only реестр полномочий, карточка сотрудника и detail сохранённой проверки;
- reversible conditional `DEMO` data migration и idempotent management command с четырьмя полностью синтетическими `DEMO-ONLY` сценариями.

Доказанные промежуточные gates:

```text
PURE CONTRACT HEAD: 0200a2be6dfc5e948eb27dbed77d9e2aa39c0d4d / 5 workflows SUCCESS
PERSISTENCE HEAD: 4c65f3ab1d6631fa661c9ffba94443620a30e71a / 5 workflows SUCCESS
```

Финальный implementation candidate проходит exact-head five-workflow gate перед trusted `vps-development-rebuild`. До успешного deployment runtime не изменён; accepted preview остаётся `UNTOUCHED`.

Merge, Ready for Review и preview write без отдельной команды пользователя запрещены.

С 01.08.2026 действует единый пользовательский контур: один активный чат ведёт work item от factual preflight до post-merge coordination. При технической смене чата новый исполнитель самостоятельно восстанавливает состояние из GitHub; пользователь не переносит между чатами handoff, SHA, CI-отчёты или команды.

Release/module/capability/work-item planning state остаётся в [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
