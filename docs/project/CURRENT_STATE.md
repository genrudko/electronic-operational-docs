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
SMALL-ASSET REPAIR HEAD: b307bab6145f31dd08fde36b8869417eba059012 / 5 workflows SUCCESS
ICONOGRAPHY REFINEMENT HEAD: 3eb93429405dcbcd88836e3647e9a307b29bcc42 / 5 workflows SUCCESS / USER PARTIALLY ACCEPTED
NARROW ICON REPAIR IMPLEMENTATION HEAD: d051f4aca14a26c42c004f04a66959afa87adc6e / VALIDATION PENDING
```

Trusted controller run `30733195542` deployed exact head
`9b7ede3a78997ebdbe7d68b750f024857369d4ea` to development with 664 VPS tests,
health-check and exact live SHA match. Preview remained `UNTOUCHED`.

Для identity candidate зафиксированы следующие решения:

- Onest Variable является фирменным шрифтом всего пользовательского интерфейса,
  включая экранную форму оперативного журнала;
- используются контролируемые веса `400 / 500 / 600 / 700 / 800`;
- там, где семантически нужен курсив, применяется контролируемый oblique Onest,
  а не другая гарнитура;
- технические идентификаторы и машинные значения используют Consolas с
  платформенными monospace fallback;
- создан детерминированный SVG-знак ЭОД и отдельный упрощённый favicon;
- на светлой теме основной текст логотипа остаётся тёмным, синий используется
  для знака и акцентов;
- EOD Outline 24 остаётся единым 24 px / 2 px round-stroke языком иконок;
- оперативная служба и внешний диспетчерский центр имеют разные символы;
- дерево персонала получает отдельные уровни организации, центра эксплуатации,
  подразделения, должности и сотрудника;
- категории АТП/ОП/ОРП/РП, квалификация, напряжение, lifecycle и матричные
  значения остаются text-first markers, а не пиктограммами.

После просмотра полного каталога пользователь принял основной набор и запросил
узкий финальный repair четырёх символов. В implementation head
`d051f4aca14a26c42c004f04a66959afa87adc6e` изменены только:

- `icon-shift-handover`: две отдельные фигуры сотрудников и одна явная
  двусторонняя стрелка между ними;
- `icon-equipment-breaker`: простая вертикальная схемная форма выключателя без
  декоративных внутренних полос;
- `icon-equipment-ground-switch`: отдельный подвижный контакт, неподвижный
  контакт и непосредственный вывод на знак заземления;
- `icon-equipment-portable-ground`: три фазных зажима, гибкие проводники, общая
  точка и спуск на заземление.

Остальные 62 canonical symbols не менялись. Все symbol IDs сохранены.

Интерфейсные пиктограммы оборудования основаны на узнаваемой семантике
ГОСТ Р 56303-2014 в редакции с Изменением № 1, но не объявляются нормативными
УГО и не заменяют обозначения приложения Б на инженерной схеме. Граница
закреплена в `docs/ux/EQUIPMENT_PICTOGRAM_GOST_BASIS_V1.md` и contract-тесте.

Новые migrations отсутствуют. Product/domain models and lifecycle remain
untouched.

Следующий обязательный шаг — пять mandatory workflows на итоговом exact head,
затем trusted full-development rebuild и пользовательская визуальная приёмка.
До прямого exact-live-SHA evidence прежний deployed repair остаётся фактическим
состоянием development.

Merge, Ready for Review и preview write без отдельной команды пользователя
запрещены.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
