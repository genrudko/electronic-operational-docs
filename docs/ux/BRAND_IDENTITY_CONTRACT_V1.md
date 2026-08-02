# EOD brand identity V1

**Status:** `CANONICAL / DIRECTION A`

**Accepted basis:** Onest Variable + EOD Outline 24 + deterministic SVG brand assets.

This contract records the accepted refinement of the project identity. It supplements
`ICONOGRAPHY_TYPOGRAPHY_CONTRACT_V1.md` and supersedes its earlier exceptions for the
operational-journal typeface.

## 1. Main project logo

The EOD logo is not a generated illustration. It is a deterministic SVG construction.

The full brand mark combines:

- a document contour;
- a folded document corner;
- a vertical sequence of registered operational events;
- aligned record lines.

The mark deliberately avoids lightning bolts, globes, random network orbits and decorative
industrial clichés. The full mark and the favicon are separate size-specific SVG assets rather
than one overloaded drawing forced into every context.

Canonical assets:

```text
src/static/system/brand-mark.svg   # sidebar and other 32 px+ lockups
src/static/system/favicon.svg      # simplified 16–32 px browser icon
```

The favicon preserves the document and registered-record meaning but removes the vertical
event axis and point markers that merged together at 16–24 px. It uses two clear record lines
and heavier integer-aligned geometry. The full mark remains the canonical sidebar sign.

The application lockup is assembled from the full SVG mark and live Onest text:

```text
ЭОД
Электронная оперативная документация
```

The text is not converted to an AI-generated raster image. This preserves exact Cyrillic,
theme adaptation and accessibility.

### 1.1. Colour use

Light theme:

```text
mark background:  #1267A5
mark linework:    #FFFFFF
wordmark:         #182338
descriptor:       #68788E
```

Dark theme:

```text
mark background:  #1267A5
mark linework:    #FFFFFF
wordmark:         #EDF3F9
descriptor:       #A9B8C8
```

Blue is an accent and mark colour. Long text and the wordmark are not rendered blue on a
white surface.

## 2. Typography

Onest Variable is used across the entire user-facing product:

- shared shell and navigation;
- registries, tables and cards;
- forms and dialogs;
- organization and personnel;
- operational rights;
- operational journal, including its document surface;
- future modules and reports.

The controlled weight vocabulary is:

```text
400 regular
500 medium
600 semibold
700 bold
800 brand / exceptional emphasis
```

The font is variable, therefore optical weight can be tuned through the approved scale
without introducing unrelated families.

Onest upstream provides the accepted upright variable family. Where semantic emphasis
requires italic text, EOD uses a controlled 10-degree CSS oblique of Onest rather than
switching to another family.

Technical monospaced text uses:

```text
Consolas
Cascadia Mono
Cascadia Code
Liberation Mono
monospace
```

Consolas is the canonical first choice; the remaining entries are platform fallbacks.

## 3. Icon alignment

Every icon-and-text composition must use a real alignment container. Icons are not positioned
with arbitrary negative margins or route-specific pixel offsets.

Required behaviour:

- SVG uses a `24 × 24` viewBox;
- normal stroke is `2 px`;
- `stroke-linecap` and `stroke-linejoin` are round;
- icon box uses an integer size: `16 / 18 / 20 / 24 / 32`;
- the SVG is vertically centred through flex/grid alignment;
- icon-only controls use an explicit centred `36 × 36` minimum target;
- tree glyphs use a fixed 22 px alignment slot;
- baseline and optical centring are checked at each supported size;
- the same object/action keeps the same icon everywhere.

`vertical-align: middle` is a fallback for inline contexts, not the primary layout mechanism.

## 4. Personnel tree levels

The organization/personnel hierarchy has a stable icon vocabulary:

| Level | Symbol |
|---|---|
| Organization | `icon-organization` |
| Operating/maintenance centre | `icon-org-center` |
| Generic division | `icon-org-division` |
| Operational service | `icon-org-operations` |
| Maintenance service | `icon-org-maintenance` |
| RZA/telemechanics service | `icon-org-rza` |
| Technical service | `icon-org-technical` |
| Position | `icon-position` |
| Employee | `icon-user` |

An operational service and an external dispatch centre are different entities and must never
share the same glyph:

```text
internal operational service: icon-org-operations
ODU / RDU / CUS / commercial or local DC: icon-dispatch-center
```

## 5. Domain catalogue coverage

The canonical sprite includes the following project-specific groups.

### Processes and modules

```text
icon-shift-handover
icon-grounding
icon-operational-order
icon-current-works
icon-inspection
icon-commissioning
icon-breaker-interruptions
icon-battery-inspection
icon-emergency-readiness
icon-cross-document
icon-reporting
```

### Equipment types

```text
icon-equipment-line
icon-equipment-cable
icon-equipment-transformer
icon-equipment-busbar
icon-equipment-breaker
icon-equipment-disconnector
icon-equipment-ground-switch
icon-equipment-portable-ground
icon-equipment-rza
icon-equipment-telemechanics
icon-equipment-dc-supply
icon-equipment-battery
```

Exact object names, voltage classes, operational states, personnel categories and qualification
groups remain text. A type icon does not replace domain wording.

## 6. Acceptance checks

A brand/identity change is accepted only after checking:

- simplified favicon at 16, 20, 24 and 32 px;
- full brand mark at 32, 44 and 64 px;
- sidebar lockup in light and dark themes;
- exact Cyrillic wordmark and descriptor;
- Onest in the operational journal;
- Consolas boundary for technical values;
- icon/text alignment in navigation, buttons, tables and personnel trees;
- operational-service and dispatch-centre distinction;
- all SVGs free from raster content and generated text.
