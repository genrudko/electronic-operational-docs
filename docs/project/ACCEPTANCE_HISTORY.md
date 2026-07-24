# ЭОД — история приёмок

Этот документ отделяет технический успех от предметной и визуальной приёмки.

## Patch 011.6.2 Repair 4

**Статус:** принят технически и визуально.

- equipment/personnel/workplace documentation importers;
- 485 tests, один skipped;
- baseline `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`.

## Patch 011.7 Repair 1 Revision 10

**Статус:** технически принят; затем потребовал продуктовый Repair 2.

- operational documentation core;
- 495 tests, один skipped;
- commit `fec8bd675f9565b0c4e398124cd22f8fabec02b4`.

Визуальная проверка выявила неверную границу: пользователь не должен конструировать произвольные формы журналов.

## Patch 011.7 Repair 2

**Статус:** технически и визуально принят.

Подтверждено:

- отсутствует кнопка ручного создания рабочего типа;
- technical schemas не допускают рабочих действий;
- каталог показывает source document/section/appendix;
- системные codes и hashes скрыты из обычного слоя;
- формы и переходы читаемы;
- обязательный transition comment имеет понятную подсказку;
- multiple selection работает с поиском и обычным click;
- пустые formset rows не создают ложных ошибок.

Baseline `bf986433ea33bf932f98925e7daf61b0199e23d0`.

## INFRA-001

**Статус:** принят как CI baseline.

- GitHub-hosted Linux;
- Python 3.13;
- PostgreSQL 18.4;
- полный актуальный test gate;
- VPS не используется как self-hosted runner.

## INFRA-002

**Статус:** принят и merged PR #2.

Подтверждено:

- preview checkout на `main`;
- app and db healthy;
- app only on `127.0.0.1:8765`;
- PostgreSQL port unpublished;
- presentation data imported to `eod_preview`;
- `operator.demo` and `supervisor.demo` authenticate;
- main page HTTP 200;
- visual walkthrough from recorded video accepted.

Merge commit `ded4571dcacd973184d3121b19c8db8c70e7b08a`.

## INFRA-003

**Статус:** принят и merged PR #3.

Подтверждено:

- development checkout on non-main branch;
- separate `eod-development` Compose project;
- separate `eod_development` database/user/volume/networks;
- app only on `127.0.0.1:8766`;
- development reset from preview succeeds without changing preview;
- both contours simultaneously healthy;
- exact database identities verified;
- both demo accounts authenticate;
- UI and presentation data work through SSH tunnel from PC;
- current head CI success for `EOD CI` and `EOD Development Stack`.

Merge commit `abd6066885b060e3e3d2c39098fcaf640bb70416`.

## DOCS-001

**Статус:** в работе.

Приёмка должна подтвердить:

- полное дерево канонических документов;
- отсутствие конфликтующих старых инструкций в активном слое;
- корректный baseline;
- рабочие internal links;
- documentation contract CI;
- README as entry point;
- AGENTS contract;
- handoff sufficient to continue work;
- explicit plan review as next stage.

## Шаблон будущей записи

```text
Change/PR:
Exact head:
Technical gates:
VPS gates:
User scenario:
Accepted defects/limitations:
Decision:
Merge commit:
Post-merge preview verification:
```