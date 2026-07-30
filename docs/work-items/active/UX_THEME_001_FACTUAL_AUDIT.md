# UX-THEME-001 — factual theme audit

## EXACT STATE

```text
repository main at branch start:
a4fe7969fd3a4410aa29ebaaa4c01dd21ac5e283

accepted product baseline:
2a9b92362b90861501cf11d073668478655fd191

issue / Draft PR:
#28 / #29

branch:
ux/ux-theme-001
```

Аудит выполнен по фактическим templates, static assets, preference model и presentation tests. Продуктовый код не изменялся.

# FACT

## F-01. Доменная настройка темы уже существует

`InterfacePreference.Theme` содержит три значения:

```text
DARK
LIGHT
SYSTEM
```

Поле `InterfacePreference.theme` сохраняется в базе, входит в `InterfacePreferenceForm`, а `ui_preferences` передаётся во все templates через context processor.

**Следствие:** новая модель, миграция или второй механизм хранения не требуются.

## F-02. Сервер уже выводит preference в корневой HTML

`src/templates/base.html` устанавливает:

```html
<html data-theme="{{ ui_preferences.theme|lower }}">
```

Но значение `system` остаётся именно `system`; до загрузки JavaScript оно не преобразуется в фактические `light` или `dark`.

## F-03. Общего theme bootstrap до первого paint нет

В `<head>` последовательно загружаются:

1. `system/app.css`;
2. `system/direction_a.css`;
3. `operational_log/opj_ux_001.css`;
4. feature assets через `extra_head`;
5. `system/direction_a_shell_final.css`.

Все JavaScript-файлы темы/рабочего пространства загружаются с `defer`. Отдельного blocking bootstrap, который до CSS/paint разрешает `system`, нет.

**Следствие:** для `SYSTEM` первый paint не имеет доказанного правильного resolved theme.

## F-04. Базовый shell остаётся отдельной тёмной системой

`src/static/system/app.css` объявляет в `:root`:

```css
color-scheme: dark;
--bg: #0a0f17;
--panel: #111a26;
--text: #edf4fb;
```

`data-theme` в этом файле не используется. Главная страница наследует `base.html`, но не активирует shared Direction A shell; при этом она использует отдельные `.da-*` primitives поверх базового тёмного canvas.

## F-05. Shared Direction A foundation жёстко светлый

`src/static/system/direction_a.css` объявляет только светлые `--da-*` tokens и задаёт:

```css
.da-shell {
    color-scheme: light;
}
```

В файле нет общих правил `html[data-theme="light"]`, `html[data-theme="dark"]` или system-resolution contract. Значительная часть surfaces, hover, controls, tables и overlays задана прямыми `#fff`, светлыми hex и `rgba(255, 255, 255, ...)`.

## F-06. DEFECT имеет отдельный принудительно светлый token layer

`registry.html` и `detail.html` загружают восемь последовательных CSS-слоёв DEFECT перед final shell layer.

`ux_foundation.css` объявляет в глобальном `:root`:

```css
color-scheme: light;
--ux-canvas: #f3f6fa;
--ux-surface: #ffffff;
...
--defect-* aliases
```

Последующие repair-файлы добавляют отдельные status/lifecycle tokens и многочисленные прямые светлые значения с `!important`.

**Следствие:** DEFECT не может корректно следовать `DARK` или `SYSTEM` без адаптации существующих tokens; добавление ещё одного feature override запрещено.

## F-07. OPJ реализует тему локально и поздно

Рабочий экран ОЖ имеет собственные кнопки `system / light / dark`. `draft_workspace.js`:

- читает `data-initial-theme`;
- разрешает `system` через `matchMedia`;
- после загрузки устанавливает `document.documentElement.dataset.theme`;
- сохраняет значение через существующий server endpoint;
- реагирует на изменение системной темы.

Это рабочий механизм сохранения, но он запускается только на shift workspace и только после deferred JavaScript.

## F-08. Тёмная тема shared shell ограничена только OPJ workspace

`direction_a_shell_final.css` содержит selector:

```css
html[data-theme="dark"] body.da-active.opj-workspace-page
```

То есть тёмные shared shell tokens применяются только при наличии `opj-workspace-page`. Registry/detail OPJ, DEFECT и другие Direction A routes не покрыты.

## F-09. Даже внутри тёмного OPJ сохраняются светлые content surfaces

`opj_ux_001.css` содержит прямые светлые backgrounds для toolbar, editor, rows, drawers, dialogs, inputs и registered tables. Dark block final shell меняет в основном shell, а не полный content layer.

Это и создаёт принятый долг `UX-THEME-001`: тёмный shell рядом со светлым workspace.

## F-10. Текущие tests закрепляют локальные, а не глобальные контракты

- DEFECT test требует `color-scheme: light` и порядок feature repair layers.
- OPJ first-paint test проверяет server-rendered shell и OPJ-only dark selectors.
- Глобальной проверки `light / dark / system` для home + defect + OPJ нет.
- Нет проверки resolved theme до первого paint.

# ROUTE / TOKEN INVENTORY

| Контур | Template / CSS owner | Текущее поведение | Gap |
|---|---|---|---|
| Общий legacy shell и home | `base.html` + `app.css` | фактически dark | `LIGHT` и `SYSTEM` не управляют палитрой |
| Shared Direction A shell | `shared/direction_a/base.html` + `direction_a.css` | фактически light | unconditional `color-scheme: light` |
| DEFECT registry/detail | shared shell + 8 feature CSS layers | принудительно light | отдельные `--ux-*`, `--defect-*`, status tokens |
| OPJ registry/detail | shared shell + `opj_ux_001.css` | в основном light | нет полного dark content contract |
| OPJ shift workspace | shared shell + OPJ workspace assets | JS-resolved local theme; dark shell + light document surfaces | late resolution и mixed surfaces |
| Account settings | `InterfacePreferenceForm` | сохраняет LIGHT/DARK/SYSTEM | нет общего live/runtime controller |
| Print | feature print CSS / `@media print` | светлая утверждённая форма | должно остаться независимо от screen theme |

## Existing token families

```text
app.css:              --bg / --panel / --text / --accent / ...
direction_a.css:      --da-canvas / --da-surface / --da-text / ...
defect foundation:    --ux-* + --defect-*
defect repair 5:      --da-status-* + --da-lifecycle-*
OPJ:                  --opj-grid / --opj-editor-surface / ...
```

Токены частично дублируют одинаковые semantic roles и не имеют одного light/dark owner.

# HARDCODED THEME GAPS

## H-01 — Critical: competing root palettes

`app.css`, `direction_a.css` и DEFECT foundation объявляют разные root assumptions. Порядок CSS, route и body class определяют итоговую тему сильнее сохранённого preference.

## H-02 — Critical: `SYSTEM` разрешается после первого paint

Server HTML содержит `data-theme="system"`; фактический resolved theme появляется только после deferred OPJ JavaScript и только на OPJ shift workspace.

## H-03 — High: OPJ-only dark selector

Dark shared tokens требуют `.opj-workspace-page`, поэтому одинаковый shell меняет тему не на всех routes.

## H-04 — High: direct light colors in shared primitives

Sidebar, topbar, fields, buttons, tables, cards, hierarchy, overlays и scrims содержат прямые light values вместо semantic tokens.

## H-05 — High: DEFECT local visual system

Несмотря на shared shell DOM, DEFECT сохраняет независимый root token layer и repair stack. Его нельзя исправлять добавлением `ux_foundation_repair6.css`; требуется adapter к global semantic tokens при сохранении geometry.

## H-06 — High: OPJ content remains light in dark shell

Toolbar, controls, drawer, overlays и screen ledger используют `#fff`/light grays. Print обязан остаться белым, но screen surfaces должны иметь отдельные semantic tokens.

## H-07 — Medium: tests protect obsolete theme assumptions

Tests справедливо защищают geometry и composition, но одновременно требуют принудительно светлый DEFECT и OPJ-only dark shell. Их следует заменить contract tests без ослабления accepted UX assertions.

# FIRST-PAINT PATH

## Current path

```text
server preference
→ <html data-theme="dark|light|system">
→ app.css assumes dark
→ Direction A CSS assumes light
→ route feature CSS may override root again
→ first paint
→ deferred OPJ workspace JS resolves system only on shift route
```

## Required path

```text
server preference in data-theme-preference
→ minimal inline bootstrap before theme-dependent styles
→ resolve light|dark from preference + prefers-color-scheme
→ set html[data-theme] and color-scheme
→ load one semantic token layer
→ first paint
→ deferred global controller subscribes to system changes
→ account/OPJ controls persist the same server preference
```

Для `LIGHT` и `DARK` server value может применяться напрямую. Для `SYSTEM` inline bootstrap обязан разрешить media query до первого theme-dependent stylesheet paint.

# PROPOSED IMPLEMENTATION BOUNDARY

## 1. Global theme bootstrap

Изменить `src/templates/base.html`:

- хранить исходное значение как `data-theme-preference`;
- до theme-dependent styles выполнить минимальный inline bootstrap;
- установить resolved `data-theme` и `color-scheme`;
- сохранить отсутствие generated shell и принятую server DOM composition.

Добавить один deferred runtime controller в `src/static/system/`:

- нормализация `system / light / dark`;
- подписка на `prefers-color-scheme`;
- единое API/event для route controls;
- без отдельной client database и без competing localStorage theme preference.

## 2. One semantic token owner

Ввести общие semantic tokens для:

```text
canvas
surface / elevated / subtle
border / strong border
text / secondary / muted / inverse
primary / primary-hover / primary-soft
success / warning / danger / neutral
control background / readonly / disabled
focus ring
overlay backdrop
shadow
```

`app.css`, `direction_a.css`, DEFECT и OPJ должны ссылаться на эти roles. Feature tokens допустимы только как aliases для предметной семантики или geometry.

## 3. Shared and legacy shell integration

- theme-enable legacy `base.html` shell/home без миграции его композиции;
- удалить unconditional light ownership из `.da-shell`;
- расширить dark/light Direction A rules на все `body.da-active`, а не только OPJ workspace;
- сохранить final shell geometry и responsive rules.

## 4. DEFECT adapter without redesign

- сохранить templates, layout, sizes, lifecycle geometry и accepted status distinctions;
- заменить root light ownership на aliases к global semantic tokens;
- перевести status/lifecycle backgrounds, borders, dots, text и overlays на theme-aware semantic pairs;
- не создавать следующий repair CSS layer;
- не переписывать business templates и JavaScript.

## 5. OPJ adapter without editor rewrite

- сохранить ledger geometry, toolbar hierarchy, keyboard semantics и editor core;
- перевести screen toolbar, rows, inputs, drawer, dialogs и registered context на semantic tokens;
- отделить screen document surface от print surface;
- `@media print` остаётся белым и theme-independent;
- заменить локальную реализацию theme resolution вызовом global controller, сохранив существующий server persistence endpoint.

## 6. Tests

Добавить/обновить contract tests, которые проверяют:

- bootstrap расположен до theme-dependent styles;
- `SYSTEM` имеет pre-paint resolution и runtime listener;
- global semantic palette имеет light и dark branches;
- home, defect registry/detail, OPJ registry/detail/workspace используют один contract;
- отсутствуют OPJ-only ownership и unconditional feature `color-scheme: light`;
- accepted templates, classes, geometry and print selectors сохранены;
- protected Python/domain files не изменены.

# CHANGED FILE BOUNDARY

Ожидаемая реализация ограничивается:

```text
src/templates/base.html
src/templates/organizations/account.html                 only if live control contract needs attributes
src/templates/operational_log/_shift_workspace_drawer.html
src/static/system/app.css
src/static/system/direction_a.css
src/static/system/direction_a_shell_final.css
src/static/system/theme.js                               new global runtime controller
src/static/equipment_defects/ux_foundation*.css          token adaptation only
src/static/operational_log/opj_ux_001.css
src/static/operational_log/draft_workspace.js            delegate theme only
applicable presentation/contract tests
docs/work-items/active/UX_THEME_001*.md
docs/ux/**                                                if contract detail changes
```

Фактический список может быть уже после implementation inventory; расширение за `src/templates/**`, `src/static/**`, tests и UX docs требует stop/review.

# PROTECTED / UNCHANGED

```text
models:                 UNCHANGED
migrations:             NONE
services/domain:        UNCHANGED
data/seeds:             UNCHANGED
DEFECT composition:     PRESERVE
OPJ composition/editor: PRESERVE
print forms:            PRESERVE
runtime/Compose/VPS:    UNCHANGED
preview:                UNTOUCHED
```

# RISKS

1. **CSS cascade risk:** feature repair layers loaded before final shell can silently retain direct light values.
2. **Regression risk:** changing token ownership may alter accepted status contrast; needs route/state matrix, not screenshots of one page.
3. **First-paint risk:** external deferred script alone is insufficient for `SYSTEM`; bootstrap must execute in `<head>` before styles.
4. **Print risk:** screen theme selectors must not leak into print.
5. **Scope risk:** theme work must not become another layout refactor.

# VERDICT

```text
READY TO IMPLEMENT
```

Обоснование:

- storage and legal preference model already exist;
- no schema or domain change is required;
- root cause is fully inside templates/static/tests;
- first-paint path is identifiable and repairable;
- accepted DEFECT/OPJ composition can be preserved;
- implementation boundary is controlled and reversible.
