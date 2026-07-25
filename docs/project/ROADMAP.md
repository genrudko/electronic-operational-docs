# ЭОД — roadmap

## Принцип

Roadmap управляется доказательствами. Каждый этап начинается после проверки current baseline и заканчивается технической и пользовательской приёмкой.

## Последнее принятое изменение

### QUALITY-001 — PostgreSQL test execution repair

**Статус:** принят, squash-merged PR #8.

```text
main history HEAD: 4237aadc2cfdee518567024c2b45b653f49c16e7
full PostgreSQL suite: 497/497 OK
test command: python manage.py test apps --verbosity 2
```

Закрыт долг нулевого test discovery.

## Текущий короткий инфраструктурный спринт

### AUTO-000 — Development automation contract

**Тип:** documentation-only.

Результат:

- automation master plan;
- GitHub/VPS orchestrator contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- актуальные state/handoff после QUALITY-001.

AUTO-000 не меняет runtime и не включает workflow/VPS code.

### AUTO-001 — Development orchestrator MVP

Начинается после принятия AUTO-000.

Минимальный vertical infrastructure slice:

```text
trusted PR trigger
→ green current-head CI
→ exact-SHA development deployment
→ explicit refresh/rebuild
→ check
→ test apps
→ status
→ evidence in GitHub
```

Gate завершения:

- два успешных deployment;
- один failure case;
- exact-SHA proof;
- preview isolation;
- штатный цикл без ручных VPS-команд пользователя.

## Возврат к продуктовой фазе

После AUTO-001 MVP продолжается PLAN-001. AUTO-002 и последующие улучшения автоматизации не блокируют продукт.

### PLAN-001 — ревизия фактической реализации

Цель:

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

Выход:

- master plan v3.0;
- подтверждённый ближайший journal vertical slice;
- реалистичная последовательность;
- актуальные acceptance criteria.

## Параллельная UX-фаза

UX-001 v0.3 остаётся provisional. Следующий gate:

```text
2 compact visual directions
→ user choice
→ limited runtime prototype
→ visual correction
→ accepted tokens
```

UX не блокирует PLAN-001 и не разрешает массовый редизайн.

## Предварительная продуктовая очередь после PLAN-001

1. Один подтверждённый structured-journal vertical slice, вероятный кандидат — defect journal.
2. Минимальные реальные связи с operational journal, equipment, participants and basis.
3. Automated and user acceptance.
4. Следующий journal slice.
5. Work permit and switching minimum.
6. Operational journal assistance/stabilization.
7. Internal prototype release.
8. Cross-document lifecycle.
9. Electronic work-permit lifecycle только после нормативного исследования.
10. Full demonstration release.

Keys journal остаётся paper-first до отдельного решения.

## Automation после MVP

Только по реальной необходимости:

- AUTO-002 change classification;
- AUTO-003 structured evidence;
- AUTO-004 Playwright acceptance;
- visual regression после принятия tokens;
- automatic development DB reset;
- trusted preview deployment.

## Дальняя очередь

Только после решения предприятия:

- AD/LDAP;
- HR/СЭД;
- legally significant electronic signature;
- SCADA/CIM;
- mobile offline;
- high availability;
- industrial commissioning;
- отмена бумажного дублирования.
