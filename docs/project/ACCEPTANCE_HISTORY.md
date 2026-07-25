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
- актуальные architecture/profile gates;
- VPS не используется как ordinary self-hosted runner.

## INFRA-002

**Статус:** принят и merged PR #2.

Подтверждено:

- preview checkout on `main`;
- app and db healthy;
- app only on `127.0.0.1:8765`;
- PostgreSQL port unpublished;
- presentation data imported to `eod_preview`;
- demo accounts authenticate;
- main page HTTP 200;
- visual walkthrough accepted.

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
- demo accounts authenticate;
- UI and presentation data work through SSH tunnel;
- current-head CI success.

Merge commit `abd6066885b060e3e3d2c39098fcaf640bb70416`.

## DOCS-001

**Статус:** принят пользователем, squash-merged PR #4, post-merge verified.

```text
accepted PR head: 1f0b71b927fbee0ef08957eac157b2480d2e9a8c
merge commit: e18872face7f27f489056b72fed31e5586121b0c
merge method: squash
```

Принято:

- GitHub как главный онлайн-источник истины;
- canonical documentation tree and index;
- README/AGENTS entry contracts;
- GitHub-first/VPS-first workflow;
- preview/development/database/tunnel/rollback runbooks;
- PR template and documentation contract gate;
- последовательная журнальная стратегия;
- paper-first scope журнала ключей;
- UX-001 parallel workstream;
- PLAN-001 как обязательная продуктовая ревизия.

DOCS-001 baseline: `e18872face7f27f489056b72fed31e5586121b0c`.

## DOCS-002

**Статус:** принят и squash-merged PR #5.

- merge commit `a2d686b0061fac513c02540a2176850640496884`;
- metadata-only фиксация DOCS-001 baseline и перехода к PLAN-001;
- application behavior/schema/runtime data не менялись;
- собственный SHA не создавал новый application baseline.

## DOCS-003

**Статус:** принят и squash-merged PR #6 как provisional UX contract.

- merge commit `62ce0a611b0d36a4c0f1f28ac6083cac5d305fb5`;
- UX-001 v0.3 сохранён в репозитории;
- visual acceptance отсутствует;
- implementation authorization отсутствует;
- runtime/domain lifecycle/data не менялись.

## QUALITY-001

**Статус:** технически принят пользователем и squash-merged PR #8.

```text
accepted PR head: 4bf055d681ef35a881c8bf5dc28e8945c1948e0d
merge commit: 4237aadc2cfdee518567024c2b45b653f49c16e7
merge method: squash
```

### Exact-head technical evidence

- EOD Documentation Contract — success;
- EOD Development Stack — success;
- EOD CI — success;
- full PostgreSQL suite: `497/497 OK`;
- database identity: `eod_development`;
- development worktree clean;
- current exact head tested.

### Принято содержательно

- реальный Django test label `apps` используется в CI/development runner;
- test discovery больше не равен нулю;
- concurrency/database/staticfiles/test fixtures repaired;
- следующий product slice обязан сохранять full suite и добавлять профильные gates.

QUALITY-001 не получил отдельную visual acceptance, поскольку не менял пользовательский UX.

## AUTO-000

**Статус:** принят пользователем, squash-merged PR #9, post-merge verified.

```text
accepted PR head: 3a4b4770e1fce41405813efa1e931288bf1a26b8
merge commit: 937d2cd2b187c17fac3088ccfc52079fc4608306
merge method: squash
change type: documentation-only operating-system milestone
```

### Exact-head CI

- EOD Documentation Contract — success;
- EOD Development Stack — success;
- EOD CI — success;
- container preview smoke — success;
- development VPS full suite: `497/497 OK`;
- development database identity: `eod_development`;
- development exact SHA/worktree clean;
- preview isolation preserved.

### Принято содержательно

- automation master plan;
- exact-SHA development deployment contract;
- restricted gateway boundary;
- fail-closed behavior;
- GitHub/VPS concurrency requirements;
- sanitised evidence contract;
- automatic merge forbidden;
- preview write forbidden for AUTO-001;
- ordinary self-hosted runner with sudo/Docker socket rejected;
- AUTO-001 limited to MVP eliminating manual PR→VPS bridge;
- AUTO-002+ not product blockers.

### Post-merge preview verification

На `/srv/eod/repository` подтверждено:

- branch `main`;
- exact HEAD `937d2cd2b187c17fac3088ccfc52079fc4608306`;
- clean worktree;
- app image rebuilt from current checkout;
- app container recreated and healthy;
- preview DB container preserved and healthy;
- health endpoint OK;
- main page HTTP 200 on `127.0.0.1:8765`;
- database identity `eod_preview`;
- migrations clean;
- host/container source match after excluding generated `electronic_operational_docs.egg-info/*`;
- final marker `FINAL PREVIEW GATE PASSED`.

### Решение

AUTO-000 принят без блокирующих дефектов. Accepted application baseline повышен до:

```text
main / 937d2cd2b187c17fac3088ccfc52079fc4608306
```

AUTO-001 implementation ещё отсутствует и требует отдельного work-item chat, branch, Draft PR, gap analysis, CI/VPS acceptance и явного пользовательского merge decision.

## DOCS-005

**Статус:** текущий Draft PR #10, не принят и не merged.

Цель — metadata-only запись уже доказанного baseline, AUTO-000 acceptance и handoff для нового Chat 0. Application behavior, schema, migrations, runtime data, workflows, VPS и secrets не меняются. Собственный будущий merge SHA DOCS-005 не создаёт новый application baseline.

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
