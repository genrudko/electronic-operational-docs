# ADR-011-3-5 — Compact journal workspace and global overlay layering

## Status

Accepted for Patch 011.3.5.

## Context

The operational journal workspace used five vertically stacked surfaces: the global header, a separate journal title card, a command row, the editor Ribbon and an independent sticky pagination row. On a standard desktop viewport this displaced the journal paper far below the top edge and reduced the number of visible records.

Global navigation dropdowns were also rendered inside the header stacking context while the journal command bar used a higher sibling stacking context. Raising only the dropdown panel z-index could not cross that parent boundary, so the directory and user menus appeared below the journal Ribbon.

Patch 011.3.4 Repair 4 already stabilised editor completion and viewport restoration. This decision must not change save, chronology, pagination or viewport-anchor semantics.

## Decision

1. The journal title becomes a non-sticky one-line summary bar containing the title, shift period, record count, autosave capability and draft status.
2. View mode, search, filter, pagination, add-entry, panel and clean-copy actions are combined in one primary command row.
3. Pagination remains functionally unchanged but is no longer an independent sticky surface. Its measured offset variables and ResizeObserver are removed.
4. The editor Ribbon belongs to the same sticky command surface. Compact mode is the default; expanded mode is a local browser preference stored under `eod.operationalJournal.ribbonMode` and never becomes official operational data.
5. A named CSS layer contract orders journal sticky UI, editor overlays, drawer, notifications, global header and global menus.
6. The global header is above all journal layers. Directory and user menus are viewport-clamped, height-limited, mutually exclusive, closed by outside click or Escape, and return focus to their trigger after Escape.
7. Runtime resources remain local, case-correct and revisioned. No external CDN, package or database migration is introduced.

## Consequences

- The journal paper begins materially higher on desktop screens.
- Only the global header and unified journal command surface remain sticky.
- Global navigation menus cannot be hidden by editor or journal stacking contexts.
- Mobile navigation keeps its existing in-flow dropdown behaviour.
- The implementation remains platform-independent and suitable for later Linux and PostgreSQL readiness work.
- Tests that asserted the obsolete independent sticky pagination contract are replaced by the unified-surface contract.

## Explicit non-goals

- No changes to models, migrations, autosave API, editor payload schema, semantic references, normative markers, chronology or clean-copy business logic.
- No Linux deployment profile, PostgreSQL migration or connected-event architecture in this patch.

## Repair 2 — переключатель режима ленты

После визуальной проверки отдельная квадратная кнопка в правой колонке Ribbon
признана ошибочной компоновкой. Она была визуально оторвана от действий журнала,
соприкасалась с полосой прокрутки и зависела от системного глифа стрелки.

Решение Repair 2:

- переключатель перенесён в основной ряд действий между «Панель» и «Чистовик»;
- пользовательская подпись сокращена до «Лента»;
- направление раскрытия показывается CSS-chevron без шрифтового символа;
- `aria-expanded` и динамический `aria-label` сохранены;
- браузерный `title` удалён, чтобы не показывать тяжёлую системную подсказку;
- третья колонка Ribbon удалена, поэтому его прокрутка больше не сталкивается с переключателем.

Изменение остаётся локальным UI-ремонтом и не затрагивает данные, autosave,
хронологическую перестройку или восстановление viewport-anchor.
