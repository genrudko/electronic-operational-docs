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
runtime impact: DEVELOPMENT
preview: UNTOUCHED
```

`MASTER-DATA-ALIGNMENT-001` принят и merged commit
`b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb`.

`NORMATIVE-EVIDENCE-001` принят и merged commit
`6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0`.

`PERSONNEL-AUTHORITY-001` выполняется в issue #42 и Draft PR #43. Проверенные
этапы:

```text
PURE CONTRACT HEAD: 0200a2be6dfc5e948eb27dbed77d9e2aa39c0d4d / 5 workflows SUCCESS
PERSISTENCE HEAD: 4c65f3ab1d6631fa661c9ffba94443620a30e71a / 5 workflows SUCCESS
MATRIX HEAD: 60460f1d213e5a5afb080402a8efff16feec0af7 / 5 workflows SUCCESS
MANAGEMENT HEAD: d141313ac6e56fc442f08683a510e52df484564c / 5 workflows SUCCESS
REPAIR IMPLEMENTATION HEAD: 41bb2c1ba99decedf19fbc22dd2f25eed187dd2d / 5 workflows SUCCESS / 664 TESTS OK
DEPLOYED REPAIR HEAD: 9b7ede3a78997ebdbe7d68b750f024857369d4ea / DEVELOPMENT DEPLOYED / USER REJECTED VISUALLY
IDENTITY FOUNDATION HEAD: 645c0dc7b520a6f091f5d266a0bc3390f26dbfbd / 5 workflows SUCCESS
BRAND AND DOMAIN ICON HEAD: ed2b5ef8cd9cd9f248da9b4d16fc6bf1ad7aa395 / 5 workflows SUCCESS
```

Trusted controller run `30733195542` deployed exact head
`9b7ede3a78997ebdbe7d68b750f024857369d4ea` to development with 664 VPS tests,
health-check and exact live SHA match. Preview remained `UNTOUCHED`.

После пользовательской проверки прежний repair candidate принят не был. Для
нового identity candidate зафиксированы следующие решения:

- Onest Variable является фирменным шрифтом всего пользовательского интерфейса,
  включая экранную форму оперативного журнала;
- используются контролируемые веса `400 / 500 / 600 / 700 / 800`;
- там, где семантически нужен курсив, применяется контролируемый oblique Onest,
  а не другая гарнитура;
- технические идентификаторы и машинные значения используют Consolas с
  платформенными monospace fallback;
- создан детерминированный SVG-знак ЭОД: документ, последовательность
  зарегистрированных событий и строки записей; генеративный растр и
  сгенерированный текст отсутствуют;
- на светлой теме основной текст логотипа остаётся тёмным, синий используется
  для знака и акцентов;
- EOD Outline 24 остаётся единым 24 px / 2 px round-stroke языком иконок;
- оперативная служба и внешний диспетчерский центр имеют разные символы;
- дерево персонала получает отдельные уровни организации, центра эксплуатации,
  подразделения, должности и сотрудника;
- canonical sprite дополнен процессами передачи смены, заземлений,
  распоряжений, текущих работ, осмотров, ввода оборудования, отключений
  выключателей, аварийной готовности, междокументных связей и отчётности;
- добавлены типы оборудования: линия, кабель, трансформатор, шины, выключатель,
  разъединитель, заземляющий нож, переносное заземление, РЗА, телемеханика,
  ЩПТ/ШОТ и аккумуляторная батарея;
- выравнивание иконок с текстом закреплено через flex/grid alignment slots,
  integer sizing и центрирование icon-only controls;
- категории АТП/ОП/ОРП/РП, квалификация, напряжение, lifecycle и матричные
  значения остаются text-first markers, а не пиктограммами;
- canonical refinement хранится в
  `docs/ux/BRAND_IDENTITY_CONTRACT_V1.md`.

Новые migrations отсутствуют. Product/domain models and lifecycle remain
untouched.

Следующий обязательный шаг — пять mandatory workflows на текущем exact head,
затем trusted full-development rebuild и пользовательская визуальная приёмка.
До прямого exact-live-SHA evidence прежний deployed repair остаётся фактическим
состоянием development.

Merge, Ready for Review и preview write без отдельной команды пользователя
запрещены.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
