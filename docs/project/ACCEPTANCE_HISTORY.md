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

### Exact evidence

```text
accepted PR head: 1f0b71b927fbee0ef08957eac157b2480d2e9a8c
merge commit: e18872face7f27f489056b72fed31e5586121b0c
merge method: squash
```

### CI exact head

- EOD Documentation Contract — success;
- EOD Development Stack — success;
- EOD CI — success.

Django test command обнаружил `0 test(s)`. Этот факт принят как technical debt, а не как доказательство регрессионной защиты; DOCS-001 не менял application behavior, models, migrations or runtime data.

### Принято содержательно

- репозиторий является главным онлайн-источником истины;
- канонический documentation tree и index;
- README and AGENTS entry contracts;
- GitHub-first/VPS-first development workflow;
- preview/development/database/tunnel/rollback runbooks;
- PR template and documentation contract gate;
- migration from legacy `docs/project_state/`;
- последовательная журнальная стратегия;
- paper-first scope журнала ключей;
- UX-001 parallel workstream;
- обязательная DOCS-актуализация после принятых изменений;
- PLAN-001 как следующий обязательный этап.

### Post-merge preview verification

На `/srv/eod/repository` подтверждено:

- branch `main`;
- HEAD `e18872face7f27f489056b72fed31e5586121b0c`;
- clean worktree;
- documentation contract OK, 43 required files;
- preview containers healthy;
- health endpoint `{"status": "ok"}`;
- main page HTTP 200;
- database identity `eod_preview`;
- `migrate --check` success, pending migrations отсутствуют.

### Решение

DOCS-001 принят без блокирующих дефектов. Accepted application baseline: `e18872face7f27f489056b72fed31e5586121b0c`.

Открытые follow-up:

- PLAN-001 evidence audit;
- минимальный automated smoke/integration suite;
- UX-001 design system workstream;
- backup retention policy.

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