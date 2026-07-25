# ЭОД — текущий handoff

**Обновлено:** 25.07.2026

```text
accepted application baseline:
main / e18872face7f27f489056b72fed31e5586121b0c

current main history HEAD:
4237aadc2cfdee518567024c2b45b653f49c16e7

current work:
AUTO-000 documentation contract

parallel open draft:
PLAN-001 / PR #7
```

## 1. Что принято последним

QUALITY-001 принят и squash-merged как PR #8.

Exact PR-head evidence:

- GitHub CI gates green;
- development database identity correct;
- worktree clean;
- PostgreSQL suite `497/497 OK`.

Штатный test command:

```text
python manage.py test apps --verbosity 2
```

Устаревшее утверждение `0 test(s)` больше не является текущим техническим долгом.

Accepted application baseline не повышается автоматически только из-за merge history; новый baseline фиксируется после документированного post-merge preview gate.

## 2. Текущий work item

`AUTO-000 — Development Automation Contract`

Цель:

- зафиксировать минимальную автоматизацию GitHub → development VPS;
- определить trust boundaries и минимальные полномочия;
- определить exact-SHA contract;
- определить acceptance и rollback;
- не менять runtime, workflows, VPS или secrets.

Branch:

```text
docs/004-auto-000-development-automation-contract
```

После принятия AUTO-000 отдельный implementation chat создаёт AUTO-001.

## 3. Следующий implementation work item

`AUTO-001 — GitHub/VPS Development Orchestrator MVP`

Минимальный результат:

```text
trusted PR trigger
→ green current-head checks
→ restricted VPS gateway
→ exact-SHA development deployment
→ explicit refresh/rebuild
→ check
→ test apps
→ status
→ structured evidence in GitHub
```

AUTO-001 не включает automatic merge, browser automation, visual regression, automatic DB reset или preview deployment.

## 4. Gate возврата к продукту

До продолжения PLAN-001 нужны:

1. два успешных AUTO-001 deployment;
2. один отрицательный acceptance case;
3. exact-SHA proof;
4. preview isolation proof;
5. отсутствие ручных VPS-команд пользователя в штатном цикле.

После этого PLAN-001 и продуктовые vertical slices продолжаются. AUTO-002+ не являются блокерами.

## 5. Контуры VPS

### Preview

```text
/srv/eod/repository
main only
eod-preview
eod_preview
127.0.0.1:8765
```

### Development

```text
/srv/eod/development
non-main only
eod-development
eod_development
127.0.0.1:8766
```

VPS deploy key read-only. Preview и development secrets не смешиваются.

## 6. PLAN-001

PR #7 остаётся Draft. Он меняет только audit instrumentation и не является конкурирующим automation implementation.

После AUTO-001:

- обновить branch от принятого main;
- выполнить evidence audit;
- сформировать master plan v3.0;
- выбрать первый journal vertical slice.

## 7. Обязательные источники нового чата AUTO-001

1. `AGENTS.md`;
2. `docs/INDEX.md`;
3. current state/handoff;
4. `docs/automation/`;
5. development workflow and runbooks;
6. INFRA-003 ADR;
7. actual workflows;
8. `compose.development.yaml`;
9. `scripts/development_stack.sh`;
10. backup/restore contract.

## 8. Запреты

- не писать secrets в Git;
- не использовать root-capable self-hosted PR runner;
- не давать Docker socket недоверенному runner;
- не исполнять изменённый PR workflow с secrets;
- не менять preview;
- не выполнять merge без явной команды пользователя;
- не использовать Base64/self-applying bootstrap.
