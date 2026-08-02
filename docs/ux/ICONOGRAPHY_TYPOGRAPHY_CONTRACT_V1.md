# EOD visual identity V1 — typography and iconography

**Status:** `CANONICAL / DIRECTION A`

**Scope:** every user-facing EOD route, shared shell and future module.

This contract complements [`UX_UI_CONTRACT_V1.md`](UX_UI_CONTRACT_V1.md). It does not create a second visual system.

## 1. Decisions

### 1.1. Corporate interface typeface

The primary EOD interface family is **Onest Variable**.

```text
UI / navigation / forms / registers / cards / dialogs: Onest
Technical identifiers / hashes / code / immutable audit payloads: Cascadia Mono
Operational-journal document and approved print forms: source-bound document typography
```

Reasons for the decision:

- one variable file covers the required weight range;
- Cyrillic and Latin have one visual character rather than looking like two joined fonts;
- compact lowercase forms remain readable in dense tables, navigation and long Russian labels;
- headings have enough identity without becoming decorative;
- the family is distributed under SIL Open Font License 1.1.

`Inter` is not an EOD corporate font. It may remain only as a deep fallback if neither Onest nor a platform UI family is available.

### 1.2. Icon foundation

The EOD icon language is **EOD Outline 24**, a curated local SVG sprite based on the Lucide geometry:

```text
canvas: 24 × 24
stroke: 2 px
linecap: round
linejoin: round
fill: none
optical safe area: approximately 2 px
color: currentColor
```

The application does not load an icon webfont and does not depend on runtime JavaScript for icons. Only approved symbols are copied into the local `src/static/system/icons.svg` sprite.

## 2. Core principle: icon, text, color and status are different channels

An icon identifies a stable object class or a conventional action. It is not decoration and does not replace a required label.

A color identifies a limited semantic family or state. It must not become a unique color code for every department or organization.

A text marker preserves exact domain meaning. Abbreviations such as `АТП`, `ОП`, `ОРП`, `РП`, `АТП/ОП`, voltage class, electrical-safety group and authority qualifier remain text.

A status is always readable without color:

```text
marker + text + optional icon
```

Forbidden:

- an icon as the only explanation of an operationally meaningful state;
- a unique pictogram for each named organization when organizations share one type;
- emoji, Unicode dingbats or platform-dependent glyphs in product UI;
- mixing filled, duotone, hand-drawn and outline families;
- icon tiles in dense trees and tables merely to make the screen more colorful;
- different icons for the same object or action in different journals.

## 3. Icon taxonomy

### 3.1. Module/navigation icons

Used once per top-level navigation destination and in module launchers.

| EOD destination | Canonical symbol | Meaning |
|---|---|---|
| Рабочий стол | `icon-home` | user workspace, not a generic web home page |
| Оперативный журнал | `icon-journal` | sequential operational record |
| Журналы | `icon-directory` | family of structured registers |
| Журнал дефектов | `icon-module-defects` | equipment deviation requiring attention |
| Заявки | `icon-request` | request/coordination record |
| Наряды и распоряжения | `icon-module-work-permits` | organized work and permit contour |
| Документы переключений | `icon-module-switching` | controlled operation sequence |
| Схемы | `icon-module-schemes` | related engineering objects and documents |
| Документы | `icon-document` | document registry |
| Оборудование | `icon-equipment` | technical asset/catalogue |
| Управление и ведение | `icon-management` | dispatch/control relation |
| Организация и персонал | `icon-organization` | organizational hierarchy |
| Оперативные права | `icon-role` | verified domain authority |
| Импорт | `icon-import` | controlled source ingestion |
| Нормативные документы | `icon-normative` | approved normative source |

Top-level entries receive an icon. Child entries in a dense sidebar are text-first unless ambiguity is proven; repeating icons on every line creates noise rather than hierarchy.

### 3.2. Entity/type icons

Entity icons identify a type, never a status or a particular company name.

| Entity type | Canonical symbol |
|---|---|
| Organization / hierarchy root | `icon-organization` |
| Generic division | `icon-org-division` |
| Leadership | `icon-org-leadership` |
| Operational/dispatch division | `icon-org-operations` |
| Maintenance / repair | `icon-org-maintenance` |
| RZA / telemechanics | `icon-org-rza` |
| Engineering / technical division | `icon-org-technical` |
| Wind-farm contour | `icon-org-wind` |
| Substation / grid facility | `icon-org-substation` |
| ODU / RDU / CUS / commercial DC | `icon-dispatch-center` plus exact text label |
| Person | `icon-user` |
| Group of persons / holders | `icon-subjects` |

`ОДУ`, `РДУ`, `ЦУС`, commercial dispatch center and a local control center do not receive unrelated logos. They share the dispatch-center type icon and are distinguished by their exact name, relation kind and scope.

### 3.3. Action icons

Conventional actions use one stable symbol throughout EOD:

```text
add       icon-add
edit      icon-edit
search    icon-search
filter    icon-filter
history   icon-history
print     icon-print
import    icon-import
delete    icon-delete
open      icon-chevron-right
```

Default action presentation is `icon + verb`. Icon-only buttons are permitted only for universally familiar compact controls and must have `aria-label`, tooltip and at least a 36 × 36 px target.

### 3.4. States and categories

The following remain chips/markers, not entity icons:

- personnel categories `АТП / ОП / ОРП / РП / АТП/ОП`;
- electrical-safety and RZA groups;
- lifecycle status;
- `ALLOW / DENY / VERIFY`;
- matrix markers `+ / +1 / +2 / … / —`;
- voltage class and operational scope.

Category color is allowed as a secondary cue, but the abbreviation and expanded wording remain visible in cards and registers.

## 4. Size and placement

```text
16 px — inline metadata and compact table actions
18 px — dense navigation and tree rows
20 px — standard buttons, fields and page actions
24 px — module cards and empty states
32 px — rare explanatory illustration in a large empty state
```

Do not scale a 24 px symbol to arbitrary fractional sizes. Icons align optically to text, not mechanically to the outer box.

Dense tree rows use a bare monoline icon without a colored square. A soft icon container is reserved for module launchers, onboarding/empty states and other spacious compositions.

## 5. Typography scale

The interface uses a controlled weight set:

```text
400 regular     body copy, table values
500 medium      secondary controls, compact navigation
600 semibold    labels, buttons, active navigation, table headers
700 bold        page and section headings
800 extra-bold  brand mark and exceptional numeric emphasis only
```

Weights such as `650`, `750`, `760`, `850`, `900` must not be introduced ad hoc. Variable-font interpolation is a tool for optical tuning, not a replacement for a defined hierarchy.

Recommended shared scale at the default 14 px UI base:

| Role | Size / line-height | Weight |
|---|---|---|
| Page title | `28–34 / 1.12` | 700 |
| Compact page title | `22–27 / 1.16` | 700 |
| Section title | `16–19 / 1.25` | 650–700 |
| Panel title | `14–16 / 1.3` | 600–650 |
| Body / table value | `13–14 / 1.4–1.5` | 400–500 |
| Label / navigation | `12–13 / 1.3` | 550–600 |
| Metadata | `11–12 / 1.35` | 400–500 |

Dates, times, registration numbers, counters and matrix values use tabular lining numerals. Technical payloads remain monospace.

Uppercase with wide tracking is restricted to short technical eyebrows. Long Russian headings, buttons and table headers are not transformed to uppercase.

## 6. Theme and accessibility

The same glyph is used in light and dark themes. Theme changes color tokens, not icon artwork.

Every meaningful symbol must satisfy:

- sufficient contrast in normal, hover, focus, disabled and selected states;
- no meaning conveyed by color alone;
- visible keyboard focus for icon-only controls;
- text alternative when the SVG is not decorative;
- `aria-hidden="true"` for a glyph that duplicates adjacent text.

## 7. Extension protocol

A new icon is allowed only when an existing canonical symbol would create a false domain statement.

Before adding it:

1. name the stable domain object/action;
2. prove that the existing catalogue is semantically wrong, not merely unfamiliar;
3. draw on the EOD Outline 24 grid and stroke contract;
4. add the symbol to the local sprite;
5. add the mapping to this document;
6. verify light/dark and 16/18/20/24 px rendering;
7. verify that Russian and English labels remain understandable without the glyph.

A module must not introduce its own icon package, icon font or duplicate SVG set.

## 8. Delivery boundary

The current candidate loads Onest from an immutable upstream revision through a pinned CDN URL so the visual choice can be accepted on the development contour. Before offline or production packaging the exact licensed WOFF2 asset and OFL notice must be stored locally; an unpinned remote font is forbidden.

Acceptance requires real-route evidence for at least:

- shared sidebar and topbar;
- operational journal registry/workspace;
- defect journal registry/detail;
- organization/personnel workspace;
- authority matrix and employee card;
- light and dark themes at `1440×900`, `1024×768` and `390×844`.
