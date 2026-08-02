# ЭОД — текущее состояние

**Дата factual check:** 03.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch
и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted application baseline: main / 2db8947062434861d2336eb474cd762e11aabb44
canonical documentation tip: main / b77b7911f41ec6c3d1e7e5019558362a058ce237
coordination tip at work-item start: 17663cf67d12c02d24177e554d6eb7d364e405e4
active work item: OPJ-LIFECYCLE-001 / REWORK IN PROGRESS
active issue: #46
active PR: #47 / OPEN / DRAFT / NOT MERGED
active branch: feature/opj-lifecycle-001
user acceptance: ABSENT / FIRST CANDIDATE REJECTED
runtime impact: DEVELOPMENT CANDIDATE STALE
preview: UNTOUCHED
```

## Active OPJ-LIFECYCLE-001

Следующий work item открыт по канонической очереди после принятых
`UX-THEME-001`, `MASTER-DATA-ALIGNMENT-001`, `NORMATIVE-EVIDENCE-001` и
`PERSONNEL-AUTHORITY-001`.

### Пользовательское решение 03.08.2026

Первый development-кандидат полностью отклонён. Отдельная lifecycle page, технический presentation layer и ручная карточка разговора не принимаются и не подлежат косметическому repair.

Каноническая документация `main` дополнена прямыми documentation-only commits по явной команде пользователя:

```text
0da9ef412ec25001c9fa49c4f8f395d151c28137  OPJ draft-to-clean boundary
593aed366df08cfff34bd6ab94f6580b2c448e9a  SHIFT boundary against OPJ registration
042d5f7902e625bd75dc091469b1d4e46c285153  horizontal and vertical CROSS-DOC relations
7f9e47bc97ae1ed5cc037d45c5e71e41ae7c7070  nearest work-item boundaries
b77b7911f41ec6c3d1e7e5019558362a058ce237  decision-log additions
```

Исторические положения не удалялись; добавлены уточняющие границы.

### Исправленная граница active work item

- принятый `shift_workspace`, редактор, autosave и revisions сохраняются;
- редактирование существует только в черновике;
- регистрация подготовленной строки создаёт неизменяемую запись чистовика;
- зарегистрированная строка не исчезает из сменного workspace, остаётся видимой и становится read-only;
- исправление и отмена выполняются только в зарегистрированном журнале новой строкой;
- результат оперативных переговоров фиксируется в хронологии ОЖ, а не отдельной карточкой звонка;
- основной UI не показывает digest, raw authority decision и append-only internals как предметную функцию;
- отдельная lifecycle page отсутствует;
- узкая внутренняя связь OPJ допустима; общий relation engine относится к `CROSS-DOC-001`;
- handover report и двустороннее подтверждение относятся к `SHIFT-HANDOVER-001`;
- action-time authority evaluation/snapshot сохраняется в системном контуре;
- `DENY` блокирует создание предметного факта;
- Preview защищён;
- Ready for Review и merge запрещены без отдельной команды пользователя.

### Текущее rework-состояние ветки

- rejected standalone lifecycle template удалён;
- rejected feature-global lifecycle CSS/JS удалены;
- shared Direction A base возвращён к принятому состоянию;
- регистрация больше не вызывает `remove_draft_entry`;
- duplicate registration блокируется;
- зарегистрированная строка показывается в shift workspace как строка чистовика;
- autosave/move/remove/restore зарегистрированной строки блокируются на маршрутах;
- correction/cancellation/communication встроены в зарегистрированный журнал;
- communication model сокращена до оперативно значимого результата;
- focused regression contract переписан;
- final exact-head CI и trusted development delivery ещё не завершены;
- визуальная приёмка нового кандидата ещё не начиналась.

Текущий development до новой trusted delivery не является доказательством rework-кандидата. Предыдущее exact-head evidence для `9d04b2a...` относится к полностью отклонённой реализации и считается superseded.

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

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
