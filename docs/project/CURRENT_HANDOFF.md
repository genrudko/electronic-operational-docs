# ЭОД — текущий handoff

**Обновлено:** 25.07.2026

**Accepted application baseline:** `main / 937d2cd2b187c17fac3088ccfc52079fc4608306`

**Current main history HEAD:** `937d2cd2b187c17fac3088ccfc52079fc4608306`

**Current work:** `DOCS-005 — AUTO-000 baseline finalization`, Draft PR #10

**Next implementation work:** `AUTO-001 — GitHub/VPS Development Orchestrator MVP`

**Parallel open Draft:** `PLAN-001 — PR #7`

## Проект

Независимый демонстрационный прототип электронной оперативной документации для энергетики. Пользователь — начальник смены ВЭС, владелец продукта и предметный эксперт; программирование, commits, PR и техническая диагностика выполняются ассистентом.

Производственные серверы, фактические оперативные записи, реальные персональные данные и секреты предприятия не используются и не коммитятся.

## Обязательная рабочая модель

Основной цикл GitHub-first/VPS-first:

1. ассистент создаёт complete change в отдельной GitHub branch;
2. GitHub Actions выполняет gates;
3. `/srv/eod/development` получает exact branch/SHA;
4. выполняются development refresh/rebuild, checks, full tests и status;
5. пользователь проверяет UI, данные и предметную логику через SSH tunnel;
6. repair commits создаются в той же branch/PR;
7. merge выполняется только по явной команде пользователя;
8. `/srv/eod/repository` синхронизируется с новым `main` и проходит post-merge gate;
9. canonical docs актуализируются в том же PR или обязательном metadata follow-up.

Пользователь не должен вручную редактировать код, собирать файлы, применять patch scripts или выполнять Git write operations.

До принятия AUTO-001 остаётся ручной VPS execution/log-transfer этап. Для долгих операций на VPS установлен `tmux`; обрыв мобильного SSH-клиента не должен останавливать процесс.

## Контуры VPS

### Preview

```text
checkout: /srv/eod/repository
branch: main only
compose project: eod-preview
database: eod_preview
application: 127.0.0.1:8765
secrets: /srv/eod/secrets/preview.env
```

### Development

```text
checkout: /srv/eod/development
branch: active non-main branch only
compose project: eod-development
database: eod_development
application: 127.0.0.1:8766
secrets: /srv/eod/secrets/development.env
```

PostgreSQL host ports отсутствуют. Контуры изолированы. VPS deploy key read-only. Development checkout не переводится на `main` после merge.

## Что принято последним

### QUALITY-001

- PR #8 принят и squash-merged;
- exact accepted PR head: `4bf055d681ef35a881c8bf5dc28e8945c1948e0d`;
- main merge commit: `4237aadc2cfdee518567024c2b45b653f49c16e7`;
- EOD CI, EOD Development Stack и EOD Documentation Contract успешны;
- development database identity: `eod_development`;
- development worktree clean;
- full PostgreSQL suite: `497/497 OK`.

Штатная команда полного suite:

```text
python manage.py test apps --verbosity 2
```

### AUTO-000

- PR #9 принят пользователем и squash-merged;
- exact accepted PR head: `3a4b4770e1fce41405813efa1e931288bf1a26b8`;
- main merge commit: `937d2cd2b187c17fac3088ccfc52079fc4608306`;
- change type: documentation-only operating-system milestone;
- runtime/workflows/VPS/secrets не менялись;
- automatic merge запрещён;
- AUTO-001 implementation отсутствует.

AUTO-000 зафиксировал:

- automation master plan;
- AUTO-001 functional contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- exact-SHA, preview isolation и fail-closed requirements.

## Post-merge preview evidence

На current `main / 937d2cd2…` подтверждено:

- preview checkout `main`, exact SHA, clean;
- app image rebuilt from current checkout;
- app container recreated и healthy;
- DB container не пересоздавался и healthy;
- health endpoint OK;
- main page HTTP 200 на `127.0.0.1:8765`;
- database identity `eod_preview`;
- `migrate --check` passed;
- `makemigrations --check --dry-run` — no changes detected;
- host/container `src` match после исключения generated `electronic_operational_docs.egg-info/*`;
- final marker `FINAL PREVIEW GATE PASSED`.

Accepted application baseline повышен до `937d2cd2b187c17fac3088ccfc52079fc4608306`.

## Текущая metadata-работа

### DOCS-005 — PR #10

```text
branch: docs/005-auto000-baseline-finalization
change type: documentation-only metadata follow-up
runtime impact: none
status: Draft
```

Цель:

- записать accepted baseline `937d2cd…`;
- закрыть AUTO-000 как accepted/merged/post-merge verified;
- обновить state, handoff, baseline/acceptance history, roadmap, open items и release notes;
- подготовить новый постоянный Chat 0.

Собственный merge commit DOCS-005 не создаёт новый application baseline.

## Следующий implementation work item

### AUTO-001 — GitHub/VPS Development Orchestrator MVP

AUTO-001 выполняется в отдельном implementation-чате и отдельной branch/PR после завершения DOCS-005 и создания нового Чата 0.

Первый этап AUTO-001:

1. проверить фактический `main`, exact SHA, open PR и branches;
2. прочитать `AGENTS.md`, `docs/INDEX.md`, current state/handoff и весь `docs/automation/`;
3. изучить actual workflows, compose, development scripts и runbooks;
4. проверить network route GitHub-hosted runner → VPS;
5. сформировать gap analysis;
6. не писать workflow/gateway до завершения gap analysis.

Целевой маршрут:

```text
trusted PR trigger
→ green required checks for current head
→ restricted VPS gateway
→ exact-SHA development deployment
→ explicit refresh/rebuild
→ check
→ full test apps
→ status
→ preview isolation proof
→ sanitised GitHub evidence
```

Запрещено:

- automatic merge;
- arbitrary root shell;
- ordinary self-hosted runner with sudo/Docker socket;
- workflow execution from untrusted PR code with secrets;
- preview write;
- Git commits from VPS;
- Base64 payload, temporary part-files и self-applying Actions workflows;
- autonomous code repair.

Exit gate:

- два последовательных successful deployments;
- один intentional failure case;
- exact-SHA and superseded proof;
- preview isolation;
- no manual VPS commands in normal cycle;
- explicit user acceptance.

После AUTO-001 продуктовая работа возвращается к PLAN-001. AUTO-002+ не блокируют продукт.

## PLAN-001 — доказательная ревизия плана и реализации

PR #7 остаётся Draft на branch `plan/001-evidence-audit`, current head `41c3229a1b0cbfad3d21e87e6c2b767445df4a23`.

Он был начат от более старого main и перед продолжением должен быть доказательно синхронизирован с accepted main после AUTO-001 без потери уже подготовленного instrumentation.

Нужно сопоставить:

```text
requirement
→ models/migrations
→ services/constraints
→ UI routes
→ tests/gates
→ presentation data
→ acceptance evidence
→ remaining deficit
```

Выходы:

- master plan v3.0;
- подтверждённый ближайший журнальный vertical slice;
- минимальный smoke/integration suite поверх полного `497/497` baseline;
- реалистичная продуктовая последовательность.

Рабочее правило: журналы доводятся по одному — минимальный общий контракт → один журнал полностью → минимальные реальные связи → automated and user acceptance → следующий журнал.

## UX-001

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Следующий visual gate:

```text
два компактных visual directions
для application shell + одного structured-journal screen
→ решение пользователя
→ ограниченный runtime prototype
→ visual correction and acceptance
→ accepted tokens
```

Concrete palette, typography, density, radii, shadows, shell composition и внешний вид reference screens пока не приняты.

## Принятые продуктовые решения

### Последовательная журнальная разработка

```text
минимальный общий контракт
→ один журнал полностью
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Связи не откладываются до завершения всего пакета, но universal timeline не проектируется заранее без подтверждённых кейсов.

### Журнал ключей

- paper-first;
- бумажный журнал остаётся рабочим оригиналом;
- полный электронный lifecycle выдачи/возврата не входит в обязательный внутренний прототип;
- электронный справочный/control contour требует отдельной оценки.

### UI/UX

- visual goal: современная операционная платформа, не administrative console;
- UI конечного пользователя только русский;
- internals — professional technical English;
- candidate tokens не становятся стандартом без runtime и user visual acceptance;
- оперативный журнал остаётся specialized document-first environment.

## Предметные правила, которые нельзя потерять

- оперативный журнал остаётся специализированным;
- structured working forms только source-bound;
- управление и ведение раздельны;
- информационное ведение — характеристика ведения;
- ЩПТ и ШОТ — одна technical equipment family с сохранением исходного обозначения;
- electronic work permit model не объявляется юридически допустимой без актуального нормативного исследования;
- реальные данные и secrets не коммитятся;
- automatic merge выполняется никогда без явной команды пользователя;
- применимые canonical docs обновляются после каждого принятого изменения.

## Новый Chat 0

После принятия и merge DOCS-005 пользователь создаёт новый постоянный интеграционный чат. Он:

- восстанавливает состояние строго по GitHub и этому handoff;
- фиксирует accepted main/baseline;
- координирует work-item chats;
- выбирает следующий этап;
- не реализует AUTO-001 внутри интеграционного чата;
- подготавливает starter для отдельного AUTO-001 implementation chat.
