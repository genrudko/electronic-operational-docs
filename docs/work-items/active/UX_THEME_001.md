# UX-THEME-001 — execution package

## WORK ITEM ID

`UX-THEME-001` — единая `light / dark / system` тема Direction A.

**Статус:** `FACTUAL PREFLIGHT`.
**Issue:** #28.
**Branch:** `ux/ux-theme-001`.
**Draft PR:** создаётся после этого commit.

## PARENT RELEASE

`DEMO-RELEASE BASELINE V1.0 / ACCEPTED`.

## PARENT MODULE

`UX` — Direction A UX.

## CAPABILITY IDS

- `CAP-UX-THEME` — целевая capability;
- `CAP-UX-SHARED` — принятая capability, которую запрещено регрессировать;
- `CAP-UX-RESPONSIVE` — смежная capability, проверяемая на обязательных viewport.

## EXACT BASELINE SHA

```text
repository main:
a4fe7969fd3a4410aa29ebaaa4c01dd21ac5e283

accepted product baseline:
2a9b92362b90861501cf11d073668478655fd191
```

## GOAL

Ввести одну общесистемную тему `light / dark / system`, единый semantic token layer и применение темы до первого paint на всех маршрутах Direction A.

## USER SCENARIO

Пользователь выбирает светлую, тёмную или системную тему один раз. Выбор сохраняется, `system` следует настройке ОС, а shell и содержимое любого маршрута открываются сразу в правильной теме без смешанных поверхностей и вспышки другой темы.

## BUSINESS RESULT

ЭОД выглядит как единый продукт, а не как набор журналов с разными visual systems. Тема не меняет предметные процессы, legal mode, print и принятую геометрию специализированных workspace.

## IN SCOPE

1. Фактическая инвентаризация theme bootstrap, CSS variables, hardcoded colors и route-level overrides.
2. Единые semantic tokens: canvas, surface, border, text, control, status, overlay, focus и validation.
3. Переключатель `light / dark / system` и сохранение выбора.
4. Следование `prefers-color-scheme` для режима `system`.
5. Применение темы до первого paint без wrong-theme flash.
6. Shared shell и primitives: sidebar, topbar, buttons, fields, tables, cards, tabs, status markers, modal и drawer.
7. Проверка home, defect и OPJ.
8. Default/loading/empty/error/readonly/overlay/long-Russian-data states.
9. Viewports `1440×900`, `1024×768`, `390×844`.
10. Независимость print от экранной темы.

## OUT OF SCOPE

- новый редизайн Direction A;
- изменение принятой композиции `DEFECT-001` или `OPJ-UX-001`;
- отдельная design system для журнала;
- изменение моделей, миграций, services, предметных lifecycle или authorization;
- изменение legal mode, печатных форм или demo-data;
- native mobile apps и accessibility certification;
- preview activation.

## DEPENDENCIES

- `PLATFORM`;
- принятый `CAP-UX-SHARED`;
- фактический shared shell и существующие route assets на exact baseline.

## DOMAIN CONTRACT

UI не предоставляет предметное право, скрытие control не заменяет server authorization, а тема не создаёт и не меняет primary facts.

## LEGAL MODE / VERIFY OWNER

Экранная тема не влияет на legal mode. Print обязан оставаться theme-independent. Владелец VERIFY по status contrast и route inventory — `UX-THEME-001`.

## SOURCE IDS

- `SRC-DEC-STAGE2`;
- `SRC-UX-DIRECTION-A`.

## COMPETITOR BENCHMARK

Новый широкий benchmark не требуется. Основные ориентиры — принятый Direction A contract и фактические маршруты ЭОД. Внешнее наблюдение допускается только для конкретной проблемы theme switching или first-paint и не становится requirement автоматически.

## UX REFERENCES / LOCATORS

- `docs/modules/UX/MODULE_CONTRACT.md`;
- `docs/ux/UX_UI_CONTRACT_V1.md`, раздел `Theme contract`;
- `docs/ux/COMPONENT_CATALOG.md`;
- `docs/ux/ROUTE_REFERENCE_MATRIX.csv`, строки `home`, `defect`, `OPJ`, `all routes theme`;
- `docs/project/PRODUCT_UX_PRINCIPLES.md`.

## VIEWPORTS / STATES

```text
1440×900
1024×768
390×844

default
loading
empty
error
readonly
overlay
long-Russian-data
light
dark
system
first-paint
```

## ALLOWED FILES

- `src/templates/**`;
- `src/static/**`;
- применимые presentation tests;
- `docs/ux/**`;
- `docs/modules/UX/**`;
- `docs/work-items/**`;
- `docs/project/CURRENT_STATE.md`;
- минимальные documentation/test gates при доказанной необходимости.

## PROTECTED FILES

- models, migrations, services и domain rules;
- database/data seeds;
- Compose, runtime, secrets и VPS controller;
- accepted preview;
- специализированная геометрия ОЖ вне необходимой theme integration;
- утверждённые печатные формы.

## FORBIDDEN CHANGES

- mixed light/dark surfaces;
- hardcoded feature canvas/surface/text вместо semantic tokens;
- CSS `zoom` или `transform` как средство адаптации;
- копирование feature-specific visual layer под новым префиксом;
- изменение business lifecycle ради удобства UI;
- автоматический merge;
- изменение preview без отдельного разрешённого delivery шага.

## DATA / FIXTURES

Новые business fixtures не требуются. Для visual checks используются существующие presentation data и длинные русские значения; изменения seed/data запрещены без отдельного решения.

## ACCEPTANCE IDS

- `AC-UX-THEME-001`;
- сохранение `AC-UX-SHARED-001`;
- применимая проверка `AC-UX-RESPONSIVE-001`.

## REQUIRED CHECKS

1. `FACT` по фактическим templates/static/theme bootstrap.
2. `ROUTE/TOKEN INVENTORY`.
3. `HARDCODED THEME GAPS`.
4. `FIRST-PAINT PATH`.
5. Профильные tests и documentation contract.
6. Cross-route visual check на трёх viewport.
7. Проверка light/dark/system и first-paint.
8. Пять exact-head workflows перед merge.
9. Пользовательская визуальная приёмка.

## DELIVERY PROFILE

`PRESENTATION / SHARED UX`. Development delivery допускается только после зелёного exact head и без воздействия на preview. Preview остаётся `UNTOUCHED`.

## COMMIT / PR RULES

- один issue #28;
- одна ветка `ux/ux-theme-001`;
- один Draft PR на весь repair cycle;
- без rebase/squash внутри рабочего цикла;
- Ready for Review и merge только по отдельной команде пользователя.

## REPORT FORMAT

```text
FACT
ROUTE/TOKEN INVENTORY
HARDCODED THEME GAPS
FIRST-PAINT PATH
IMPLEMENTATION BOUNDARY
CHANGED FILE BOUNDARY
TESTS
CI
RUNTIME IMPACT
PREVIEW IMPACT
VERDICT
```

## STOP CONDITIONS

- фактический theme bootstrap не установлен;
- реализация требует изменения protected files;
- обнаружен конфликт с принятой композицией DEFECT/OPJ;
- невозможно исключить wrong-theme first-paint;
- route inventory или status contrast остаётся недоказанным;
- exact head изменился без повторной проверки.
