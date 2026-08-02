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

`PERSONNEL-AUTHORITY-001` выполняется в issue #42 и Draft PR #43. Проверенные
этапы:

```text
PURE CONTRACT HEAD: 0200a2be6dfc5e948eb27dbed77d9e2aa39c0d4d / 5 workflows SUCCESS
PERSISTENCE HEAD: 4c65f3ab1d6631fa661c9ffba94443620a30e71a / 5 workflows SUCCESS
MATRIX HEAD: 60460f1d213e5a5afb080402a8efff16feec0af7 / 5 workflows SUCCESS
MANAGEMENT HEAD: d141313ac6e56fc442f08683a510e52df484564c / 5 workflows SUCCESS / DEVELOPMENT DEPLOYED
REPAIR IMPLEMENTATION HEAD: 41bb2c1ba99decedf19fbc22dd2f25eed187dd2d / 5 workflows SUCCESS / 664 TESTS OK
```

На development сейчас остаётся management head
`d141313ac6e56fc442f08683a510e52df484564c`. Он подтверждён trusted controller
run `30730304940`, миграциями `0011/0012`, 659 VPS tests, health-check и exact
live SHA match.

После пользовательской проверки management candidate принят не был. В единый
обязательный acceptance repair включены:

- выровненные и более читаемые grouped/right headers матрицы;
- встроенная под деревом цветовая легенда АТП/ОП/ОРП/РП/АТП-ОП;
- semantic icons для руководства, оперативного персонала, ТОиР, РЗА, ВЭУ,
  подстанций и технических подразделений;
- `OperationalRightConditionDetail` с точным текстом, пунктом и источником;
- `+1` → пункт 5.4, `+2` → пункт 5.13 Правил по охране труда при эксплуатации
  электроустановок, приказ Минтруда России от 15.12.2020 № 903н;
- explicit unresolved state для любого неизвестного условия вместо выдуманной
  расшифровки;
- exact condition tooltip в матрице и полный condition block в «Кто имеет
  право» и карточке сотрудника;
- RZA categories and scope как отдельная special qualification;
- синтетические справочники ОДУ Юга, Северокавказского РДУ, СК ПМЭС/ЦУС,
  ПС 500 кВ Невинномысск и КДЦ ВЭС;
- отдельные вкладки ОДУ/РДУ, ЦУС/смежные объекты и подрядный персонал;
- новый Direction A management workspace `/organization/`;
- сохранённые эксплуатационные факты: отдельное подразделение, руководство
  центра, immediate operational reporting и energy-site service relations;
- одиночное добавление без тупиковых dropdowns: существующее значение либо
  ручное создание подразделения, должности и рабочего места;
- canonical typography layer для всех Direction A screens при сохранении
  document typography операционного журнала.

Новые migrations:

```text
0013_operational_right_condition_detail
0014_seed_demo_external_operational_directories
0015_stabilize_demo_external_directory_codes
```

Pre-coordination repair head
`41bb2c1ba99decedf19fbc22dd2f25eed187dd2d` доказал:

```text
AUTO-001A Foundation CI:       run 30732608756 / SUCCESS
AUTO-001B Controller CI:       run 30732608770 / SUCCESS
EOD Development Stack:        run 30732608775 / SUCCESS
EOD Documentation Contract:   run 30732608749 / SUCCESS
EOD CI:                        run 30732608754 / SUCCESS
Django/PostgreSQL tests:       664 / OK / skipped=1
migration apply and drift:     SUCCESS
container preview smoke:       SUCCESS
```

Canonical coordination docs обновлены после этого proof, поэтому получившийся
финальный exact head обязан заново пройти все пять workflows до trusted
full-development rebuild. Новый repair runtime пока не подтверждён. Preview
остаётся `UNTOUCHED`.

Merge, Ready for Review и preview write без отдельной команды пользователя
запрещены.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
