# AUTO-000 — review checklist

## Документационный scope

- [ ] AUTO-000 остаётся documentation-only.
- [ ] AUTO-001 не изображён реализованным.
- [ ] Current manual workflow сохранён до implementation acceptance.
- [ ] QUALITY-001 reflected as 497/497 test baseline.
- [ ] Accepted application baseline не повышен без post-merge preview evidence.

## Архитектура

- [ ] GitHub остаётся source of truth.
- [ ] Exact-SHA invariant обязателен.
- [ ] Preview and development isolation сохранены.
- [ ] Один development deployment одновременно.
- [ ] AUTO-001 MVP имеет ограниченный scope.

## Безопасность

- [ ] Нет self-hosted PR runner с Docker socket и sudo.
- [ ] Нет interactive root SSH.
- [ ] Нет repository write/merge permissions у automation.
- [ ] Secrets и credentials отсутствуют в diff.
- [ ] Open security decisions не решены молча.

## Приёмка

- [ ] Два success и один failure case обязательны.
- [ ] Проверяется superseded SHA.
- [ ] Проверяется no-shell behavior.
- [ ] Проверяется preview isolation.
- [ ] После AUTO-001 MVP PLAN-001 возобновляется.
