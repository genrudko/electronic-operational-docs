# Direction A component catalog

| Component | Shared contract | Допустимая специализация |
|---|---|---|
| shell/sidebar/topbar | tokens, navigation, density, responsive behaviour | состав доступных разделов по правам |
| buttons/fields/tables/status | states, focus, validation, selection, disabled/readonly | предметные labels и columns |
| modal/drawer | overlay, focus trap, close behaviour, mobile geometry | предметная форма и confirmation text |
| hierarchy selector | search, tree, keyboard, selected context | equipment/person/document tree |
| workspace canvas | canvas/surface, density, scroll and responsive boundary | OPJ spread, switching steps, source-bound form |
| notifications | severity, lifetime, accessibility | предметное сообщение без ложного success |
| print | theme-independent, source traceability | утверждённая source-bound layout |

Новый компонент не создаётся, если задача решается существующим shared primitive без потери предметного смысла.
