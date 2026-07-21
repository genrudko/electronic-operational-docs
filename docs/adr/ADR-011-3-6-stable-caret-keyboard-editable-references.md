# ADR-011.3.6 — Stable caret, keyboard navigation and editable semantic references

## Status

Accepted for the independent demonstration prototype.

## Context

The journal editor rendered semantic references as atomic `contenteditable=false`
tokens containing both the document label and a visible arrow glyph. This mixed
editable document text with UI decoration. Automatic re-linking rebuilt DOM
nodes and could restore a collapsed selection only before or after a token.
Browser-default `Home`, `End`, `PageUp` and `PageDown` behavior was also not
constrained to the active record editor.

## Decision

1. The reference label remains ordinary editable text. Only a separate empty
   action span is non-editable; its arrow is rendered by CSS and is not part of
   `textContent` or clipboard text.
2. A text mutation inside a reference detaches the stale semantic binding before
   the browser applies the edit. The automatic resolver may then bind the new
   designation again.
3. Caret bookmarks are stored as block index plus logical text offset and can be
   restored inside reference labels after automatic DOM replacement.
4. Plain-text paste is sanitized from the legacy copied arrow artifact. Copy
   explicitly writes clean `text/plain`.
5. Windows-style navigation is handled inside the active editor: word movement
   for Ctrl+Left/Right, visual-line boundaries for Home/End, editor boundaries
   for Ctrl+Home/End and line-page movement for PageUp/PageDown.
6. The server-side editor schema remains `operational-draft-editor.v4`; no model
   or migration change is introduced.

## Consequences

Semantic identity is no longer allowed to survive a changed visible label. The
link preview opens from the dedicated arrow action or Ctrl+Click, while a normal
click and double-click on the label retain native caret and word-selection
behavior.

## Repair 3 — logical clipboard serialization and viewport-safe Page navigation

Ручная проверка выявила два остаточных дефекта: CSS-зависимый `innerText` мог
добавлять перенос между подписью ссылки и следующим знаком препинания, а
многократный `Selection.modify(..., "line")` прокручивал весь журнал.

Repair 3 закрепляет следующие решения:

- plain-text clipboard строится собственным обходом клонированного `Range`;
- подпись semantic reference сериализуется как обычный текст, action-иконка
  пропускается, а переносы создаются только реальными блоками и `<br>`;
- `PageUp`/`PageDown` находят первую или последнюю визуальную строку через
  геометрию текстовых диапазонов и caret-from-point API;
- исходный viewport восстанавливается синхронно и в двух следующих кадрах;
- для однострочной записи `PageUp` и `PageDown` переходят соответственно к
  началу и концу записи; `Shift` продолжает выделение.
