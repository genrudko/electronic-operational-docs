# AUTO-000 — review checklist

**Проверено:** 25.07.2026

**Охват:** все 17 изменённых файлов PR #9

**Тип проверки:** содержательный self-review поверх автоматических GitHub gates

## Документационный scope

- [x] AUTO-000 остаётся documentation-only.
- [x] AUTO-001 нигде не изображён реализованным.
- [x] Current manual workflow сохранён до implementation acceptance.
- [x] QUALITY-001 отражён как подтверждённый baseline `497/497`.
- [x] Accepted application baseline не повышен без post-merge preview evidence.
- [x] Исторические release notes и DOCS evidence не переписаны задним числом.
- [x] `docs/INDEX.md` сохраняет исходные назначения документов и полный набор разделов.
- [x] `CURRENT_HANDOFF.md` сохраняет подробные UX, product and domain contracts.

## Архитектура

- [x] GitHub остаётся source of truth.
- [x] Exact-SHA invariant обязателен.
- [x] Preview and development isolation сохранены.
- [x] Одновременно разрешён один development deployment.
- [x] AUTO-001 MVP ограничен устранением ручного PR→VPS разрыва.
- [x] AUTO-002+ не являются предварительным блокером PLAN-001.

## Безопасность

- [x] Нет self-hosted PR runner с Docker socket и sudo.
- [x] Нет interactive root SSH.
- [x] Automation credential должен технически исключать repository write and merge.
- [x] `pull-requests: write` не назначается по умолчанию только ради comment/labels.
- [x] Secrets и credentials отсутствуют в diff.
- [x] PR-код считается недоверенным относительно VPS host and accepted preview.
- [x] Development runtime не получает Docker socket, privileged mode, host keys или preview credentials.
- [x] Open security decisions не решены молча и перечислены в decision register.

## Приёмка AUTO-001

- [x] Два success и один failure case обязательны.
- [x] Проверяется superseded SHA.
- [x] Проверяется no-shell behavior.
- [x] Проверяется preview isolation.
- [x] Проверяется отсутствие host/preview capabilities у PR runtime.
- [x] После принятого AUTO-001 MVP PLAN-001 возобновляется.

## Намеренно открыто до implementation audit

- trusted GitHub event;
- restricted transport;
- network route GitHub-hosted runner → VPS;
- exact GitHub reporting permissions;
- detached HEAD or temporary local branch;
- outbound network policy for development containers;
- artifact retention;
- stale-lock recovery;
- фактическое поведение refresh/rebuild/migrations;
- bootstrap and rollback details.

Эти вопросы должны быть закрыты evidence-based решением в AUTO-001 implementation PR. Они не разрешают расширять полномочия молча.
