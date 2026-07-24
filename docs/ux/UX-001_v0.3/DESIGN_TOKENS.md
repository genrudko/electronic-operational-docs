# DESIGN_TOKENS — candidate visual tokens ЭОД

> **Пакет:** UX-001 v0.3  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Статус:** все конкретные значения — candidate, не final standard.

## 1. Правило принятия

Token становится accepted только после применения на трёх reference families, runtime-проверки, contrast measurement, long Russian data test, user visual acceptance и фиксации в основном интеграционном контуре.

## 2. Candidate light palette

| Token | Candidate | Назначение | Контраст/ограничение | Где проверить | Acceptance | Диапазон |
|---|---:|---|---|---|---|---|
| `color.canvas` | `#F4F8FB` | общий background | text `#152A3A`: ~13.8:1 | shell, detail, registry | нет серой «админки», glare приемлем | L ±3% |
| `color.surface` | `#FFFFFF` | form, document, table | primary text: ~14.8:1 | все references | clear separation без тяжёлой тени | L 97–100% |
| `color.surface.subtle` | `#EAF2F7` | filters, quiet grouping | text: ~13.0:1 | registry/form | не выглядит disabled | L ±4% |
| `color.text.primary` | `#152A3A` | основной текст | ≥7:1 на surfaces | все | читаем в длинной смене | L ±5% |
| `color.text.secondary` | `#607483` | captions/metadata | ~4.86:1 on white | table/detail | ≥4.5:1 normal text | L до -6% |
| `color.action.primary` | `#1267A5` | primary action, active nav | white: ~5.98:1 | shell/form | AA normal text, not overused | H ±8°, L ±5% |
| `color.brand.deep` | `#123E61` | deep hierarchy, optional shell | white: ~11.1:1 | shell | shell не становится тяжёлым | H ±8°, L +0…8% |
| `color.accent.cyan` | `#14A7C2` | focus/supporting accent | white only ~2.86:1 | focus/relation | не использовать как text-on-white | H ±10°, L ±6% |
| `color.accent.teal` | `#3AB9AD` | noncritical positive accent | white only ~2.41:1 | progress/graphic | не использовать как small text fill | H ±10°, L -8…+4% |
| `color.border` | `#D4E0E7` | selective divider | decorative only | table/form | structure survives without overboxing | L ±4% |
| `color.danger` | `#C23B4A` | destructive/error | white: ~5.23:1 | integrity/error | text + icon, not color-only | H ±5°, L ±4% |
| `color.warning` | `#A85B10` | warning/check | white: ~5.04:1 | banner/status | distinguishable from danger | H ±6°, L ±5% |

`accent.cyan` и `accent.teal` не предназначены для маленького белого текста на заливке. Они применяются как border, focus ring, icon или indicator после проверки контраста.

## 3. Candidate dark palette

| Token | Candidate | Назначение | Контраст/ограничение | Где проверить | Acceptance | Диапазон |
|---|---:|---|---|---|---|---|
| `dark.canvas` | `#0E1D28` | outer shell/background | text ~15.5:1 | shell/journal | не чёрный, без glow | L ±4% |
| `dark.surface` | `#152B39` | cards/panels | text ~13.2:1 | detail/drawer | hierarchy различима | L ±4% |
| `dark.surface.elevated` | `#1D394A` | overlays | runtime check | popover/modal | отделяется без heavy shadow | L ±5% |
| `dark.text.primary` | `#ECF5F9` | main text | ≥13:1 | all | no glare | L -0…6% |
| `dark.text.secondary` | `#A9BBC5` | metadata | ≥7.3:1 | table/detail | ≥4.5:1 | L ±6% |
| `dark.action.primary` | `#55B7E9` | action/focus | dark canvas ~7.6:1 | shell/form | clear, not neon | H ±8°, L ±6% |
| `dark.accent.cyan` | `#4DD0DB` | relation/focus | ~9.3:1 | journal | no large glow | H ±10°, L ±6% |
| `dark.success` | `#5EC6A7` | success | ~8.3:1 | statuses | text/icon pair | H ±8°, L ±5% |
| `dark.warning` | `#F0B35A` | warning | ~9.2:1 | banners | distinct | H ±6°, L ±5% |
| `dark.danger` | `#F27683` | danger | ~6.3:1 | integrity | not fluorescent | H ±5°, L ±5% |

`[OPEN]` Paper-like operational journal may retain a light page within dark shell.

## 4. Typography candidates

System-first stack until font deployment is separately decided:

```css
font-family: Inter, "Segoe UI", Roboto, Arial, sans-serif;
```

| Token | Candidate | Назначение | Acceptance | Диапазон |
|---|---:|---|---|---|
| `type.body` | 15px/1.45 | standard UI | readable, not marketing-spacious | 14–16px |
| `type.body.compact` | 14px/1.35 | dense table/journal metadata | usable in long shift | 13.5–15px |
| `type.caption` | 12px/1.35 | metadata | never sole carrier of critical info | 12–13px |
| `type.title.page` | 24px/1.2, 650 | page identity | no marketing-scale heading | 22–28px |
| `type.title.section` | 17px/1.3, 600 | section | hierarchy without cards | 16–19px |
| `type.title.row` | 15px/1.35, 600 | row subject | stronger than number | 14–16px |
| `type.mono` | 13px/1.4 | diagnostic IDs only | absent from normal mode | 12–14px |

Tabular numerals are candidate for timestamps, registration numbers and measurements.

## 5. Spacing candidates

Base rhythm candidate: `4px`.

| Token | Candidate | Назначение | Диапазон |
|---|---:|---|---|
| `space.1` | 4px | micro-gap | 3–5px |
| `space.2` | 8px | compact controls | 6–10px |
| `space.3` | 12px | field/group gap | 10–14px |
| `space.4` | 16px | standard section inner | 14–20px |
| `space.5` | 24px | section separation | 20–28px |
| `space.6` | 32px | major page separation | 28–40px |

## 6. Radius, border, shadow candidates

| Token | Candidate | Acceptance | Диапазон |
|---|---:|---|---|
| `radius.control` | 6px | serious, not archaic | 4–8px |
| `radius.surface` | 10px | no consumer bubble look | 8–12px |
| `radius.overlay` | 12px | clear elevation | 8–14px |
| `border.default` | 1px | not every block boxed | 1px |
| `shadow.overlay` | `0 12px 32px rgba(15,36,50,.16)` | visible, restrained | blur 24–40px, alpha .12–.22 |
| `shadow.surface` | none by default | hierarchy via layout | optional subtle |

## 7. Control geometry candidates

| Token | Candidate | Acceptance | Диапазон |
|---|---:|---|---|
| `control.height.compact` | 32px | journal/table toolbar | 30–36px |
| `control.height.default` | 40px | standard form/action | 38–44px |
| `control.height.touch` | 44px | mobile/critical | 44–48px |
| `icon.size` | 18px | clarity | 16–20px |
| `hit.target.minimum` | 36×36px | desktop icon controls | 34–40px |
| `hit.target.touch` | 44×44px | mobile | 44–48px |

## 8. Focus candidate

```css
outline: 2px solid var(--color-accent-cyan);
outline-offset: 2px;
```

Acceptance: visible on light/dark, not clipped by overflow, distinct from selection/error, supports forced-colors strategy. Допустимый диапазон 2–3px, offset 1–3px.

## 9. Layout candidates

| Archetype | Candidate width | Acceptance | Диапазон |
|---|---:|---|---|
| reading/detail | 1120px | readable hierarchy | 1040–1240px |
| form | 960px | fields not overly wide | 880–1080px |
| registry | 1600px | primary columns visible | 1440–1760px |
| workspace/journal | viewport minus gutters | stable geometry | gutter 16–32px |
| modal small | 480px | short decision only | 420–560px |
| drawer | 420px | context, not second app | 360–480px |

## 10. Breakpoint candidates

| Token | Candidate | Назначение | Диапазон |
|---|---:|---|---|
| `bp.mobile` | 640px | auxiliary mode | 600–720px |
| `bp.narrow` | 960px | stacked filters/detail | 900–1024px |
| `bp.desktop` | 1280px | full workstation | 1200–1366px |
| `bp.wide` | 1600px | expanded registry | 1440–1728px |

Breakpoints принимаются по content failure, а не по устройствам.

## 11. Z-layer candidates

```text
base content       0
sticky local      10
shell             20
dropdown/menu     40
popover           50
drawer            60
modal/backdrop    80
critical notice   90
```

Arbitrary `z-index: 9999` запрещается после введения canonical layer.

## 12. Motion candidates

| Token | Candidate | Acceptance | Диапазон |
|---|---:|---|---|
| `motion.fast` | 100ms | hover/focus feedback | 80–140ms |
| `motion.standard` | 160ms | menu/popover | 140–220ms |
| `motion.drawer` | 220ms | stable geometry | 180–280ms |
| easing | `cubic-bezier(.2,.8,.2,1)` | reduced-motion fallback | adjustable |

## 13. Token acceptance worksheet

```text
Token:
Reference screens:
Measured contrast:
Long-data result:
Light result:
Dark result:
Keyboard/focus result:
User decision:
Accepted value:
Allowed aliases:
Date/baseline:
```
