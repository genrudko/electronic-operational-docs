# ЭОД — текущий handoff

**Обновлено:** 24.07.2026  
**Accepted baseline:** `main / abd6066885b060e3e3d2c39098fcaf640bb70416`  
**Active branch:** `docs/001-project-operating-system`

## Проект

Независимый демонстрационный прототип электронной оперативной документации для энергетики. Пользователь — начальник смены ВЭС, владелец продукта и предметный эксперт; программирование, commits, PR и техническая диагностика выполняются ассистентом.

## Рабочая модель

Основной цикл GitHub-first/VPS-first:

1. ассистент создаёт complete change в active GitHub branch;
2. GitHub Actions выполняет gates;
3. `/srv/eod/development` получает branch через `git pull --ff-only`;
4. выполняются development refresh/check/test/status;
5. пользователь проверяет UI, данные и предметную логику через SSH tunnel;
6. repair commits создаёт ассистент;
7. merge выполняется только по явной команде пользователя;
8. `/srv/eod/repository` синхронизируется с новым `main` и проходит health check.

Пользователь не должен вручную редактировать код, собирать файлы, применять patch scripts или выполнять Git write operations.

## Контуры VPS

### Preview

```text
/srv/eod/repository
main only
eod-preview
eod_preview
127.0.0.1:8765
/srv/eod/secrets/preview.env
```

### Development

```text
/srv/eod/development
active non-main branch
eod-development
eod_development
127.0.0.1:8766
/srv/eod/secrets/development.env
```

Оба контура подтверждены simultaneously healthy. PostgreSQL host ports отсутствуют.

## Что принято последним

INFRA-003:

- isolated VPS development;
- separate checkout/Compose/database/user/volume/networks/secrets;
- safe preview-to-development data reset;
- current PR head CI green;
- browser access through SSH tunnel accepted;
- PR #3 merged;
- merge commit `abd6066885b060e3e3d2c39098fcaf640bb70416`.

## Текущая работа

DOCS-001 создаёт новый documentation operating system:

- README and AGENTS;
- canonical index;
- current state, master plan, roadmap, domain invariants;
- architecture/module map/data policy;
- decisions/open items/history/baselines/acceptance;
- development process and release rules;
- preview/development/database/tunnel/rollback runbooks;
- acceptance documents;
- PR template and documentation CI gate;
- migration of `docs/project_state/`.

На ветке уже создаются документы напрямую через GitHub. Development checkout должен получить изменения обычным `git pull --ff-only` перед проверкой.

## Следующая обязательная работа после DOCS-001

PLAN-001 — доказательная ревизия плана и реализации.

Нужно сопоставить:

```text
требование
→ models/migrations
→ services/constraints
→ UI routes
→ tests/gates
→ presentation data
→ acceptance evidence
→ remaining deficit
```

Результат — master plan v3.0 и возможная корректировка направления разработки.

## Предметные правила, которые нельзя потерять

- оперативный журнал остаётся специализированным;
- рабочие structured forms только source-bound;
- UI только русский, internals — professional technical English;
- управление и ведение раздельны;
- информационное ведение — характеристика ведения;
- ЩПТ и ШОТ — одна техническая equipment family с сохранением исходного обозначения;
- electronic work permit model не объявляется юридически допустимой без актуального исследования;
- реальные данные и secrets не коммитятся.

## Быстрая проверка ветки на VPS

```bash
cd /srv/eod/development
git status --short --branch
git fetch --prune origin
git pull --ff-only
sudo bash scripts/development_stack.sh check
sudo bash scripts/development_stack.sh test
sudo bash scripts/development_stack.sh status
```

## Источники истины

1. accepted `main` Git history and exact SHA;
2. `docs/project/CURRENT_STATE.md`;
3. migrations, tests, CI and VPS diagnostics;
4. `docs/project/CURRENT_HANDOFF.md`;
5. decision/baseline/acceptance histories;
6. current chat;
7. historical local plans and context archives.

При расхождении факт проверяется, а документы исправляются в той же рабочей ветке.