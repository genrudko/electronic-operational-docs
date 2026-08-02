# UX/UI contract V1 — Direction A

Direction A является единственной общесистемной visual system ЭОД.

Связанные обязательные контракты:

- [`COMPONENT_CATALOG.md`](COMPONENT_CATALOG.md);
- [`ICONOGRAPHY_TYPOGRAPHY_CONTRACT_V1.md`](ICONOGRAPHY_TYPOGRAPHY_CONTRACT_V1.md).

## Shared layer

Общие для всех маршрутов:

- shell, sidebar, topbar и навигационная плотность;
- semantic tokens canvas/surface/border/text/control/status/overlay;
- фирменная интерфейсная типографика Onest и технический monospace-контур;
- единая локальная SVG-иконография EOD Outline 24;
- buttons, fields, tables, cards, tabs, status markers, modal и drawer;
- keyboard, focus, validation, disabled и readonly behaviour;
- loading, empty, error и long-Russian-data states.

Специализированный workspace допускается только там, где предметная форма требует собственной геометрии: ОЖ, switching authoring и source-bound forms. Он не создаёт отдельную design system, не подключает собственный icon pack и не переопределяет общесистемный интерфейсный шрифт.

Документная типографика зарегистрированного ОЖ и утверждённых печатных форм может быть source-bound. Это не разрешает менять шрифт shell, навигации, форм, фильтров и служебных карточек.

## Icon and typography boundary

- одинаковая сущность или действие имеют один symbol ID во всех модулях;
- иконка не заменяет доменный текст и не является единственным носителем статуса;
- категории персонала, квалификации, voltage scope и authority markers остаются текстовыми;
- именованные ОДУ/РДУ/ЦУС/ДЦ различаются текстом и relation kind, а не случайными логотипами;
- dense table/tree использует bare outline icon без декоративной цветной плитки;
- произвольные emoji, icon fonts, feature-owned SVG sprites и ad hoc font stacks запрещены.

## Acceptance viewports

- desktop `1440×900`;
- compact desktop/tablet `1024×768`;
- mobile `390×844`.

## Theme contract

`UX-THEME-001` вводит одну настройку `light / dark / system`, единые semantic tokens и одинаковое переключение shell/content на всех маршрутах. Смешанные светлые и тёмные поверхности, hardcoded feature canvas/surface/text и first-paint flash другой темы запрещены. Print не зависит от экранной темы.

Один и тот же icon glyph используется в светлой и тёмной теме; меняются только semantic color tokens.

## Evidence boundary

UI не предоставляет предметное право, не меняет legal mode документа и не создаёт несуществующий lifecycle. Green visual/source check не заменяет пользовательскую приёмку реального маршрута.

Acceptance evidence обязано показывать реальную загрузку Onest, а не только наличие `font-family` в CSS, и проверять общий symbol mapping на реальных маршрутах.
