# ЭОД — текущее состояние

**Дата factual check:** 02.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch
и runtime state.

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

`MASTER-DATA-ALIGNMENT-001` принят и merged commit
`b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb`.

`NORMATIVE-EVIDENCE-001` принят и merged commit
`6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0`.

`PERSONNEL-AUTHORITY-001` выполняется в issue #42 и Draft PR #43. Pure authority
contract, persistence, external engagement, bounded substitution and immutable
action-time evaluation implemented. Intermediate proven gates:

```text
PURE CONTRACT HEAD: 0200a2be6dfc5e948eb27dbed77d9e2aa39c0d4d / 5 workflows SUCCESS
PERSISTENCE HEAD: 4c65f3ab1d6631fa661c9ffba94443620a30e71a / 5 workflows SUCCESS
```

Первый presentation candidate был отклонён: он показывал technical grant list и
не воспроизводил рабочую информационную модель утверждённого списка лиц с
предоставлением прав. Direction A оформление принято, информационная архитектура
не принята.

Принята и реализуется domain correction:

- утверждённая положительная ячейка матрицы является предоставленным правом;
- `+1`, `+2`, `+3` являются правом с дополнительным условием;
- source right материализуется в linked evaluator projection, а не требует
  повторного ручного назначения;
- основной UX — дерево подразделений + матрица прав;
- отдельный view отвечает на вопрос «кто имеет выбранное право»;
- employee card показывает полный профиль квалификации, прав, условий, scope и
  basis;
- внешний персонал остаётся отдельным контуром.

Новый matrix candidate проходит implementation и exact-head validation. До его
успешного trusted rebuild runtime state для нового head не подтверждён. Preview
остаётся `UNTOUCHED`.

Merge, Ready for Review и preview write без отдельной команды пользователя
запрещены.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
