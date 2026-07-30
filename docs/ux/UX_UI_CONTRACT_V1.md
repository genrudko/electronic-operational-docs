# UX/UI contract V1 — Direction A

Direction A является единственной общесистемной visual system ЭОД.

## Shared layer

Общие для всех маршрутов:

- shell, sidebar, topbar и навигационная плотность;
- semantic tokens canvas/surface/border/text/control/status/overlay;
- buttons, fields, tables, cards, tabs, status markers, modal и drawer;
- keyboard, focus, validation, disabled и readonly behaviour;
- loading, empty, error и long-Russian-data states.

Специализированный workspace допускается только там, где предметная форма требует собственной геометрии: ОЖ, switching authoring и source-bound forms. Он не создаёт отдельную design system.

## Acceptance viewports

- desktop `1440×900`;
- compact desktop/tablet `1024×768`;
- mobile `390×844`.

## Theme contract

`UX-THEME-001` вводит одну настройку `light / dark / system`, единые semantic tokens и одинаковое переключение shell/content на всех маршрутах. Смешанные светлые и тёмные поверхности, hardcoded feature canvas/surface/text и first-paint flash другой темы запрещены. Print не зависит от экранной темы.

## Evidence boundary

UI не предоставляет предметное право, не меняет legal mode документа и не создаёт несуществующий lifecycle. Green visual/source check не заменяет пользовательскую приёмку реального маршрута.
