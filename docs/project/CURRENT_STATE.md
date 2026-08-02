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
MATRIX HEAD: 60460f1d213e5a5afb080402a8efff16feec0af7 / 5 workflows SUCCESS / DEVELOPMENT DEPLOYED
```

Первый presentation candidate был отклонён как technical grant list. Матричный
candidate на `60460f1d213e5a5afb080402a8efff16feec0af7` восстановил принятую
информационную архитектуру: hierarchy tree, employee × rights matrix, «Кто имеет
право», полный профиль сотрудника, отдельные external and evaluation views.
Оформление, общая концепция и тёмная тема приняты пользователем; оставлены
точечные замечания по типографике заголовков и терминологии квалификаций.

Текущий personnel management candidate расширяет этот контур:

- ручное создание и редактирование существующей карточки сотрудника;
- перенос между подразделениями без дублирования;
- контакты и режим доступности;
- деактивация вместо физического удаления;
- versioned edit групп по электробезопасности, специальных квалификаций и прав;
- отдельные qualification types для РЗА, работ на высоте и иных допусков;
- operational profiles организаций: собственная, ДЦ, ЦУС/сетевая, смежный
  энергообъект, коммерческий ДЦ и подрядчик;
- внешний оперативный справочник отдельно от contractor engagement;
- два XLSX-шаблона: штатная матрица и внешний оперативный справочник;
- upload → validate → duplicate match → CREATE/UPDATE/ERROR preview → выбор
  строк/подразделений/объектов → explicit publish;
- SHA-256 файла и append-only change history;
- отсутствие лица в новом файле не деактивирует карточку автоматически;
- улучшенная типографика matrix headers, легенда АТП/ОП/ОРП/РП/АТП-ОП и явная
  подпись «группа по электробезопасности».

Новый create/edit/import head проходит exact-head validation. До успешного
trusted full-development rebuild development runtime остаётся на matrix head
`60460f1d213e5a5afb080402a8efff16feec0af7`; новый runtime не подтверждён.
Preview остаётся `UNTOUCHED`.

Merge, Ready for Review и preview write без отдельной команды пользователя
запрещены.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
