# ЭОД — текущее состояние

**Дата factual check:** 10.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch
и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 1f3296bcf3d0f57bd088241c81691c7f54b2ac25
active work item: MODULE-ACTIVATION-CONTRACT-001
active issue: #61
active PR: #62 / OPEN / DRAFT / NOT MERGED
active branch: architecture/module-activation-contract-001
runtime impact: NONE
preview: UNTOUCHED
```

## Active MODULE-ACTIVATION-CONTRACT-001 execution

`MODULE-ACTIVATION-CONTRACT-001` выполняется только в issue #61, ветке
`architecture/module-activation-contract-001` и Draft PR #62.

Work item является архитектурным: он фиксирует canonical manifest, lifecycle,
scope-resolution, dependency/integration semantics, universal access-decision
contract, history/reactivation, migration boundary и activation audit до
реализации `MODULE-REGISTRY-001`. Registry/control-plane tables, product/domain
migrations, массовая wiring runtime guards, UX и новые журналы в этот PR не входят.
Runtime impact — `NONE`; live VPS и Preview не изменяются.

`SAFE-CONTINUATION` после принятия Deployment Profile имеет 5 из 8 обязательных
work items со статусом `ACCEPTED`; сам `MODULE-ACTIVATION-CONTRACT-001` имеет
`IN_PROGRESS`. Предметная очередь сохраняется в состоянии
`PAUSED_PENDING_SAFE_CONTINUATION_AND_EXPLICIT_OWNER_DECISION`.
`SHIFT-HANDOVER-001` не стартовал.

## Accepted DEPLOYMENT-PROFILE-001 baseline

`DEPLOYMENT-PROFILE-001` принят пользователем и merged обычным merge commit:

```text
accepted PR: #60 / CLOSED / MERGED
accepted exact head: 323f4fb9162e84ca25a49556340078de81af2424
merge commit / accepted main: 1f3296bcf3d0f57bd088241c81691c7f54b2ac25
issue: #59 / CLOSED / COMPLETED
user acceptance: PASSED
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
runtime impact: NONE
preview: UNTOUCHED
```

Принятый baseline включает fail-closed pilot/production configuration contract,
PostgreSQL-only production/pilot semantics, operator preflight, secure
TLS/reverse-proxy/session settings и разделённые liveness/readiness checks.
Все применимые exact-head workflows завершились успешно:

```text
EOD CI:                      31362143450 / SUCCESS
AUTO-001A Foundation CI:     31362143473 / SUCCESS
AUTO-001B Controller CI:     31362143425 / SUCCESS
EOD Documentation Contract: 31362143445 / SUCCESS
EOD Development Stack:      31362143454 / SUCCESS
EOD Dependency Provenance:   31362143446 / SUCCESS
EOD Deployment Profile:      31362143422 / SUCCESS
EOD Secret Hygiene:          31362143415 / SUCCESS
```

`SAFE-CONTINUATION` после merge достигнут на 5 из 8 обязательных work items.
`MODULE-ACTIVATION-CONTRACT-001` канонически переведён в `IN_PROGRESS`.
Это не означает достижения `SAFE-CONTINUATION` или готовности к пилоту.

## Accepted DEPENDENCY-PROVENANCE-001 baseline

`DEPENDENCY-PROVENANCE-001` принят пользователем и merged обычным merge commit:

```text
accepted PR: #58 / CLOSED / MERGED
accepted exact head: 0f0e92522e7a2c5d43dd635ed661c65ed5021422
merge commit / accepted main: 5b54446d632ef1839d530dc2945255b3033359fe
issue: #57 / CLOSED / COMPLETED
user acceptance: PASSED
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
runtime impact: NONE
preview: UNTOUCHED
```

Принятый baseline включает пять hashed lock projections, immutable OCI/action
inputs, SPDX 2.3 JSON SBOM, in-toto Statement v1 / SLSA Provenance v1,
Sigstore/GitHub OIDC signing identity evidence и fail-closed dependency
provenance gates. Все применимые exact-head workflows завершились успешно:

```text
EOD CI:                      31338914564 / SUCCESS
AUTO-001A Foundation CI:     31338914521 / SUCCESS
AUTO-001B Controller CI:     31338914515 / SUCCESS
EOD Documentation Contract: 31338914511 / SUCCESS
EOD Development Stack:      31338914549 / SUCCESS
EOD Secret Hygiene:          31338914517 / SUCCESS
EOD Dependency Provenance:   31338914527 / SUCCESS
```

`SAFE-CONTINUATION` после merge достигнут на 4 из 8 обязательных work items.
`DEPLOYMENT-PROFILE-001` больше не заблокирован `DEPENDENCY-PROVENANCE-001` и
канонически переведён в `IN_PROGRESS`. Это не означает достижения
`SAFE-CONTINUATION` или готовности к пилоту.

## Accepted SECRET-HYGIENE-001 baseline

`SECRET-HYGIENE-001` принят пользователем и merged обычным merge commit:

```text
accepted PR: #56 / CLOSED / MERGED
accepted exact head: cd7dc07a9c77a71a5b1166aa7a57ee4d3afa93da
merge commit / accepted main: 95b8dd6017745886f110f052ea0950b3d48173d8
issue: #54 / CLOSED / COMPLETED
user acceptance: PASSED
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
```

Принятый baseline включает единый canonical scanner, отсутствие broad
test/fixture exemptions, process-local test credentials, exact allowlist,
post-redaction verification, verified artifact publication, exact-head
checkout gates и фактический clean-tree check.

Все шесть обязательных exact-head workflows завершились успешно;
полный suite — `720 tests / OK`, focused regressions — `17 / OK`,
current scan — `854 files / 0 findings / allowlist 0`.

`SAFE-CONTINUATION` после merge достигнут на 3 из 8 обязательных work
items. Следующий зависимый элемент — `DEPENDENCY-PROVENANCE-001`.

## Accepted INDUSTRIALIZATION-PROGRAM-EXECUTION-001 baseline

`INDUSTRIALIZATION-PROGRAM-EXECUTION-001` принят пользователем и merged обычным merge commit:

```text
accepted PR: #53 / CLOSED / MERGED
accepted exact head: 9eec9b94392df45b44e7ad4165e8c76d06d05b36
merge commit / accepted main: 3c02c5c05cdf604bbf230d215b82ddd875ab1421
issue: #52 / CLOSED / COMPLETED
user acceptance: PASSED
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
runtime impact: NONE
preview: UNTOUCHED
```

Принятый baseline включает:

- исполнимый backlog всех 30 industrialization work items;
- owner roles, acceptance-evidence requirements, risks, dependencies и gate impact;
- fail-closed state transitions, dependency closure и parallelization limits;
- residual-risk contract с owner, controls, due/review и explicit acceptance evidence;
- deterministic backlog, phase, gate, dependency и risk projections;
- positive baseline и 20 negative fail-closed fixtures;
- постоянный Documentation Contract для execution backlog;
- 23 focused regression tests и зелёные exact-head workflows;
- отсутствие product/runtime/schema/data/Preview изменений.

Phase 0 завершена. `SAFE-CONTINUATION` после этого merge ещё не достигнут:
приняты 2 из 8 обязательных work items. Предметная очередь остаётся paused,
`SHIFT-HANDOVER-001` не стартовал. Следующий work item Phase 1 должен быть
открыт отдельным issue/branch/Draft PR и не становится активным автоматически.

## Accepted PROJECT-STATE-RECONCILIATION-001 baseline

`PROJECT-STATE-RECONCILIATION-001` принят пользователем и merged обычным merge commit:

```text
accepted PR: #51 / CLOSED / MERGED
accepted exact head: a6534a5fb2e5ae59bfba6cd36e9e80ebc69801d6
merge commit / accepted main: 9d6d48ad25d45cd79673c7017980a8bd92fa961a
issue: #50 / CLOSED / COMPLETED
user acceptance: PASSED
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
runtime impact: NONE
preview: UNTOUCHED
```

Принятый baseline включает:

- factual reconciliation GitHub, canonical release plan и обязательных derived views;
- сохранение schema 2 как совместимого superset принятого schema-1 contract;
- сохранение source IDs, coverage mappings, post-demo contours и presentation scenarios;
- fail-closed проверку release identity, 27-модульного каталога и evidence matrices;
- strict `CURRENT_STATE.md` parser и сверку PR context с GitHub event;
- общий single-owner scan всего применимого Markdown-контура;
- deterministic projections module map, implementation sequence, master checklist и industrialization program;
- fail-closed industrialization dependency, gate и mandatory-core checks;
- status projection всех 27 module contracts из canonical plan;
- 21 focused regression tests и зелёные exact-head workflows;
- отсутствие product/runtime/schema/data/Preview изменений.

`SAFE-CONTINUATION` после этого merge ещё не достигнут. `INDUSTRIALIZATION-PROGRAM-EXECUTION-001` канонически переведён в `IN_PROGRESS` в issue #52, ветке `governance/industrialization-program-execution-001` и Draft PR #53. Предметная очередь остаётся paused; `SHIFT-HANDOVER-001` не стартовал.

## Accepted PROJECT-SUSTAINABILITY-001 baseline

`PROJECT-SUSTAINABILITY-001` принят пользователем и merged обычным merge commit:

```text
accepted PR: #49 / CLOSED / MERGED
accepted exact head: cdf3238ca986761dbecc61a60bd28941ff8219ac
merge commit / accepted main: 916a6d708ff4bd8433218068a204547b4a9abf84
issue: #48 / CLOSED / COMPLETED
user acceptance: PASSED
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
runtime impact: NONE
preview: UNTOUCHED
```

Принятый baseline включает:

- factual audit репозитория, архитектуры, UX, данных, security, deployment и operations;
- risk register: 34 риска — 7 CRITICAL, 22 HIGH и 5 MEDIUM;
- программу из 8 фаз и 30 work items;
- gates `SAFE-CONTINUATION` и `PILOT-READY`;
- обязательный `PILOT-READY` core из 21 work item;
- browser gates для фактических critical pilot routes без скрытой обязательности
  общего UX-рефакторинга;
- trigger-based обязательность UX foundation и page-template library;
- прямую и транзитивную замкнутость mandatory core;
- сохранение modular Django monolith и phased migration без big-bang rewrite;
- NOTES как будущий optional product module;
- MAIL-INTEGRATION как post-pilot wishlist последней очереди.

Все пять обязательных exact-head workflows завершились успешно на
`cdf3238ca986761dbecc61a60bd28941ff8219ac`; полный suite — `716 tests / OK`.

Принятие программы не означает достижения `SAFE-CONTINUATION` или готовности к
пилоту. Первый обязательный последующий work item —
`PROJECT-STATE-RECONCILIATION-001`.

Дополнительные accepted baseline markers:

```text
accepted OPJ exact head: 65997a9d51de4d066ec07277d4c660bfc307650e
accepted OPJ merge commit: c4e344342b647ce59a390a04329d2cadb1f34d7c
user acceptance: PASSED ON DEVELOPMENT IN EDGE
merge method: ORDINARY MERGE COMMIT
squash / rebase: NOT USED
```

## Accepted OPJ-LIFECYCLE-001 baseline

`OPJ-LIFECYCLE-001` принят пользователем после проверки development-кандидата
в штатном профиле Microsoft Edge и merged обычным merge commit:

```text
accepted PR: #47 / CLOSED / MERGED
accepted exact head: 65997a9d51de4d066ec07277d4c660bfc307650e
merge commit / accepted main: c4e344342b647ce59a390a04329d2cadb1f34d7c
issue: #46 / CLOSED / COMPLETED
preview: UNTOUCHED
```

Принятый baseline включает:

- переход отдельной строки ОЖ из редактируемого сменного черновика в зарегистрированный неизменяемый чистовик;
- исправления и отмены только новыми зарегистрированными строками без переписывания оригинала;
- принятую хронологию и геометрию отметок ПЗ/ЗН;
- устойчивую трёхграфную экранную и печатную форму;
- цветовые аварийные отметки и печатное представление;
- reference previews и композицию статусов зарегистрированных строк;
- работающее меню `Действия` в штатном Microsoft Edge;
- дату, время и номер записи у верхней границы первой графы;
- обход устаревших assets в цикле пользовательской приёмки.

Все пять обязательных exact-head workflows завершились успешно на
`65997a9d51de4d066ec07277d4c660bfc307650e`:

```text
AUTO-001A Foundation CI:     30986956669 / SUCCESS
AUTO-001B Controller CI:     30986956714 / SUCCESS
EOD Development Stack:      30986956637 / SUCCESS
EOD Documentation Contract: 30986956684 / SUCCESS
EOD CI:                      30986956738 / SUCCESS
```

### Канонические границы OPJ / SHIFT / CROSS-DOC

Каноническая документация `main` ранее дополнена прямыми documentation-only
commits без удаления исторического материала:

```text
0da9ef412ec25001c9fa49c4f8f395d151c28137  OPJ draft-to-clean boundary
593aed366df08cfff34bd6ab94f6580b2c448e9a  SHIFT boundary against OPJ registration
042d5f7902e625bd75dc091469b1d4e46c285153  horizontal and vertical CROSS-DOC relations
7f9e47bc97ae1ed5cc037d45c5e71e41ae7c7070  nearest work-item boundaries
b77b7911f41ec6c3d1e7e5019558362a058ce237  decision-log additions
```

Принятые границы:

- принятый `shift_workspace`, редактор, autosave и revisions сохраняются;
- редактирование существует только в черновике;
- регистрация подготовленной строки создаёт неизменяемую запись чистовика;
- зарегистрированная строка остаётся видимой и становится read-only;
- исправление и отмена выполняются только новой зарегистрированной строкой;
- результат оперативных переговоров фиксируется в хронологии ОЖ;
- отдельная lifecycle page отсутствует;
- общий relation engine относится к `CROSS-DOC-001`;
- handover report и двустороннее подтверждение относятся к `SHIFT-HANDOVER-001`;
- action-time authority evaluation/snapshot сохраняется в системном контуре;
- `DENY` блокирует создание предметного факта;
- Preview защищён.

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
