# INDUSTRIALIZATION-PROGRAM-EXECUTION-001

## Статус

`IN_PROGRESS` после открытия issue #52 и отдельного Draft PR. Финальная приёмка и merge требуют отдельной явной команды владельца продукта.

## Цель

Завершить Phase 0 принятой программы индустриализации: превратить принятые 8 фаз, 30 work items, risk register и два gates в исполнимый и проверяемый backlog без создания нового конкурирующего владельца текущего состояния.

## Основание

- `PROJECT-SUSTAINABILITY-001` — ACCEPTED / MERGED;
- `PROJECT-STATE-RECONCILIATION-001` — ACCEPTED / MERGED;
- risk `PSR-034`;
- обязательный элемент `SAFE-CONTINUATION` и `PILOT-READY`.

## Canonical ownership

- `docs/project/CURRENT_STATE.md` владеет только volatile project state;
- `docs/project/DEMO_RELEASE_PLAN.yaml` владеет текущими release/module/capability/work-item statuses;
- `docs/project/INDUSTRIALIZATION_PROGRAM.yaml` владеет принятой структурой фаз, dependencies, risks и gate boundaries;
- human-readable backlog/progress views являются только воспроизводимыми projections;
- GitHub evidence сильнее описаний в документации.

## Scope

1. Представить все 30 industrialization work items в исполнимом backlog.
2. Для каждого элемента зафиксировать:
   - phase;
   - priority;
   - type;
   - risk IDs;
   - dependencies;
   - owner role;
   - required acceptance evidence;
   - gate impact;
   - допустимые state transitions.
3. Определить однозначный порядок Phase 0 и допустимую параллельность Phase 1.
4. Формализовать residual-risk records: owner, compensating controls, due date, review condition и explicit acceptance.
5. Сделать progress/backlog/gate projections воспроизводимыми и fail closed.
6. Подготовить понятный product-owner/operator view прогресса к `SAFE-CONTINUATION`.
7. Сохранить domain queue в paused state до достижения gate и отдельного решения владельца.

## Обязательные проверки

Validator должен обнаруживать как минимум:

- missing owner role;
- invalid state transition;
- dependency bypass;
- accepted item без evidence;
- work item без risk/gate classification;
- gate projection drift;
- unowned residual risk;
- contradictory current status между GitHub evidence и canonical plan;
- ручное изменение generated progress view.

Диагностика должна содержать file, identifier, rule, expected и actual.

## Out of scope

Запрещено в этом work item:

- менять product code и предметное поведение;
- менять Django models, migrations или данные;
- менять runtime, VPS, Compose deployment или Preview;
- реализовывать module activation/registry;
- выполнять security/dependency/deployment/restore implementation последующих work items;
- начинать UX refactor;
- начинать `SHIFT-HANDOVER-001`;
- создавать новые журналы или модули;
- менять принятые границы `SAFE-CONTINUATION` и `PILOT-READY` без отдельного решения владельца;
- переводить PR в Ready for Review или выполнять merge без отдельной явной команды.

## Acceptance criteria

- все 30 work items имеют обязательные execution metadata;
- dependencies и допустимая параллельность однозначны;
- Phase 0 completion и Phase 1 start rules проверяются автоматически;
- statuses согласованы с GitHub evidence и canonical plan;
- residual-risk records fail closed при отсутствии обязательных полей;
- backlog/gate/progress views генерируются или побайтно проверяются;
- positive и negative fixtures покрывают перечисленные классы drift;
- Documentation Contract и применимые workflows зелёные на final exact head;
- changed-file boundary соответствует governance/documentation-automation scope;
- runtime/schema/data/Preview не затронуты;
- PR остаётся Draft до отдельной команды владельца.

## Stop condition

После завершения реализации и exact-head проверок остановиться на пользовательской приёмке. `SAFE-CONTINUATION` после этого work item всё ещё не достигнут: остаются обязательные Phase 1 работы.
