# ЭОД — текущее состояние

**Дата factual check:** 01.08.2026

**Единственный владелец:** accepted main SHA, active work item/issue/PR/branch и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb
active work item: NORMATIVE-EVIDENCE-001
active issue: #40
active PR: #41 / OPEN / DRAFT / NOT MERGED
active branch: feature/normative-evidence-001
runtime impact: NONE
preview: UNTOUCHED
```

`MASTER-DATA-ALIGNMENT-001` принят пользователем и merged обычным merge commit `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb` из exact PR head `e507b63ab35a4767c25364d729accb9a741af874`. Issue #34 закрыт. Принятый diff добавляет staged target `ORGANIZATION_STRUCTURE`, dependency-aware publication `Division → Workplace → EnergySite`, детерминированные проверки конфликтов и полный transactional rollback; legacy `ORGANIZATION` сохранён.

`NORMATIVE-EVIDENCE-001` стартовал после factual preflight текущего GitHub. Issue #40 и Draft PR #41 открыты; ветка создана от process/documentation tip `c05ace785f054233aa878ddead491def47525140`. Первый implementation slice фиксирует pure domain contract legal modes/evidence events и focused tests без schema migration, runtime delivery или preview write.

Ни один non-`VERIFY` legal mode не считается доказанным только из-за immutable model, SHA-256 или password re-authentication. Применимость официальной консолидированной нормы и локального акта остаётся отдельным evidence gate.

С 01.08.2026 действует единый пользовательский контур: один активный чат ведёт work item от factual preflight до post-merge coordination. При технической смене чата новый исполнитель самостоятельно восстанавливает состояние из GitHub; пользователь не переносит между чатами handoff, SHA, CI-отчёты или команды.

Release/module/capability/work-item planning state остаётся в [`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
