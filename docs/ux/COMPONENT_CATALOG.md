# Direction A component catalog

| Component | Shared contract | Допустимая специализация |
|---|---|---|
| shell/sidebar/topbar | tokens, navigation, density, responsive behaviour | состав доступных разделов по правам |
| typography | Onest UI family, scale, weights, tabular numerals, monospace boundary | source-bound registered document/print typography |
| iconography | local EOD Outline 24 sprite, symbol mapping, sizes, accessibility | new domain glyph only through icon extension protocol |
| buttons/fields/tables/status | states, focus, validation, selection, disabled/readonly | предметные labels и columns |
| icon button | 36 px minimum target, tooltip, aria-label, standard action symbol | compact conventional action only |
| module icon container | 24 px glyph, soft semantic surface, spacious composition | module-specific semantic tone |
| dense tree icon | bare 18 px outline glyph, no decorative colored tile | stable entity-type mapping |
| status/category chip | marker + explicit text, theme-safe contrast | domain status/category vocabulary |
| modal/drawer | overlay, focus trap, close behaviour, mobile geometry | предметная форма и confirmation text |
| hierarchy selector | search, tree, keyboard, selected context | equipment/person/document tree |
| workspace canvas | canvas/surface, density, scroll and responsive boundary | OPJ spread, switching steps, source-bound form |
| notifications | severity, lifetime, accessibility | предметное сообщение без ложного success |
| print | theme-independent, source traceability | утверждённая source-bound layout |

Новый компонент не создаётся, если задача решается существующим shared primitive без потери предметного смысла.

Feature CSS не может подключать собственный font stack, icon font, внешний icon package или дублирующий SVG sprite. Mapping и правила расширения зафиксированы в [`ICONOGRAPHY_TYPOGRAPHY_CONTRACT_V1.md`](ICONOGRAPHY_TYPOGRAPHY_CONTRACT_V1.md).
