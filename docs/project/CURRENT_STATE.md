# ЭОД — текущее состояние

**Дата factual check:** 02.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch
и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 2db8947062434861d2336eb474cd762e11aabb44
active work item: NONE
active issue: NONE
active PR: NONE
active branch: NONE
runtime impact: DEVELOPMENT / LIVE e8b053f5fda51f23e2506a1a45a405f5c2ee3b6c
preview: UNTOUCHED
```

## Accepted PERSONNEL-AUTHORITY-001 baseline

`PERSONNEL-AUTHORITY-001` принят и merged обычным merge commit:

```text
accepted PR: #43 / CLOSED / MERGED
accepted exact head: d659ab949db2942c064eec3c298d031a9684c67d
merge commit: 2a2013a51bfdc9de602b095adcb28a51b8d4487e
issue: #42 / CLOSED / COMPLETED
```

Принятый baseline включает:

- structured personnel authority grants и action-time `ALLOW / DENY / VERIFY`;
- организационную структуру, матрицу прав и карточки сотрудников;
- ручное создание, редактирование, versioned rights/qualifications и деактивацию;
- controlled XLSX preview/publish;
- внешние оперативные справочники и contractor semantics;
- Onest Variable как фирменную интерфейсную гарнитуру;
- принятый логотип ЭОД и canonical EOD Outline 24 iconography;
- узкий принятый repair выключателя, заземляющего разъединителя, переносного
  заземления и приёма/передачи смены.

## Accepted POST-MERGE-DEPLOY-VERIFY-001 result

Post-merge deployment carrier завершён и принят пользователем после визуальной
проверки:

```text
issue: #44 / CLOSED / COMPLETED
PR: #45 / CLOSED / MERGED
accepted carrier head: e8b053f5fda51f23e2506a1a45a405f5c2ee3b6c
merge commit / accepted main: 2db8947062434861d2336eb474cd762e11aabb44
merge method: merge commit
squash / rebase: NOT USED
```

Exact-head validation и trusted development delivery:

```text
AUTO-001A Foundation CI:     run 30763218721 / SUCCESS
AUTO-001B Controller CI:     run 30763218758 / SUCCESS
EOD Development Stack:      run 30763218767 / SUCCESS
EOD Documentation Contract: run 30763218748 / SUCCESS
EOD CI:                      run 30763218732 / SUCCESS
repository suite:            675 tests / OK
trusted run:                 30763517233 / SUCCESS
validation job:              91538153706 / SUCCESS
VPS job:                     91538172254 / SUCCESS
VPS suite:                   675 tests / OK / 2 expected repository-only skips
live migrations:             no migrations to apply
Django system check:         no issues
live SHA:                    e8b053f5fda51f23e2506a1a45a405f5c2ee3b6c
rollback:                    NOT EXECUTED
preview:                     UNTOUCHED
```

Development продолжает работать на точном carrier head `e8b053f5...`; его дерево
включено в accepted main merge commit `2db8947...`. Product behavior, schema,
migrations, workflow и controller в carrier repair не изменялись.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
