# UX-001 — статус и навигация

## Текущий статус

`UX-001 v0.3` принят **как предварительный проектный контракт для визуального прототипирования**.

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Это означает:

- структурные UI/UX-принципы, interaction/component contracts и reference-screen requirements можно использовать как основу проектирования;
- concrete palette, typography scale, density, radii, shadows, shell composition и внешний вид reference screens ещё не приняты визуально пользователем;
- пакет не разрешает менять domain model, lifecycle документов или начинать массовое внедрение по всем экранам;
- после визуального сравнения и runtime-прототипа допускается выпуск `UX-001 v0.4` с переработкой визуального языка.

## Пакет

- [`UX-001_v0.3/UX_001_INDEX.md`](UX-001_v0.3/UX_001_INDEX.md) — индекс и границы пакета.
- [`UX-001_v0.3/VISUAL_DIRECTION.md`](UX-001_v0.3/VISUAL_DIRECTION.md) — самостоятельное визуальное направление.
- [`UX-001_v0.3/UI_AUDIT.md`](UX-001_v0.3/UI_AUDIT.md) — консолидированный аудит.
- [`UX-001_v0.3/VIDEO_EVIDENCE_AUDIT.md`](UX-001_v0.3/VIDEO_EVIDENCE_AUDIT.md) — runtime evidence.
- [`UX-001_v0.3/UI_PRINCIPLES.md`](UX-001_v0.3/UI_PRINCIPLES.md) — проверяемые принципы.
- [`UX-001_v0.3/DESIGN_TOKENS.md`](UX-001_v0.3/DESIGN_TOKENS.md) — candidate tokens.
- [`UX-001_v0.3/COMPONENT_CONTRACT.md`](UX-001_v0.3/COMPONENT_CONTRACT.md) — component contract.
- [`UX-001_v0.3/INTERACTION_CONTRACT.md`](UX-001_v0.3/INTERACTION_CONTRACT.md) — keyboard/focus/overlay contract.
- [`UX-001_v0.3/PAGE_ARCHETYPES.md`](UX-001_v0.3/PAGE_ARCHETYPES.md) — page archetypes.
- [`UX-001_v0.3/REFERENCE_SCREENS.md`](UX-001_v0.3/REFERENCE_SCREENS.md) — textual reference-screen contracts.
- [`UX-001_v0.3/UX_IMPLEMENTATION_ROADMAP.md`](UX-001_v0.3/UX_IMPLEMENTATION_ROADMAP.md) — staged roadmap.
- [`UX-001_v0.3/manifest.json`](UX-001_v0.3/manifest.json) — integrity manifest исходного пакета.

## Целостность исходного пакета

Файлы `UX-001_v0.3/*.md` сохранены без содержательной нормализации, чтобы размеры и SHA-256 продолжали совпадать с `manifest.json`. Используемые в исходнике Markdown hard-break markers являются намеренными; для этого каталога действует узкое whitespace-исключение в `.gitattributes`. На остальную документацию стандартный запрет trailing whitespace продолжает распространяться.

## Следующий visual gate

1. Подготовить два компактных визуальных направления на application shell и одном показательном structured-journal screen.
2. Пользователь выбирает или отклоняет направление.
3. Выбранный вариант реализуется как ограниченный runtime-прототип в development contour.
4. Проверяются desktop density, длинные русские значения, states, focus, overlays и реальная рабочая читаемость.
5. Только после этого фиксируются accepted visual tokens и разрешается постепенное распространение на остальные reference families.

Журнал дефектов остаётся сильным кандидатом на reference vertical slice, но окончательный выбор выполняется PLAN-001.
