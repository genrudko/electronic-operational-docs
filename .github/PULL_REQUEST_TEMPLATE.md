## Цель

<!-- Какую пользовательскую, предметную, инфраструктурную или документационную задачу решает PR? -->

## Контекст и основание

<!-- Связанные решения, источники, ADR, дефекты, результаты исследования. -->

## Scope

### Входит

-

### Не входит

-

## Точный baseline

```text
base branch: main
base SHA:
head branch:
head SHA:
```

## Изменения

-

## Предметные инварианты

- [ ] `docs/project/DOMAIN_INVARIANTS.md` проверен.
- [ ] Изменение не нарушает существующие инварианты.
- [ ] Новый/изменённый инвариант зафиксирован в `DECISION_LOG.md`.
- [ ] Нормативные assumptions отделены от доказанных требований.

## Данные и migrations

```text
migrations: none / list
data transformation: none / description
preview impact: none / description
backup required: yes / no
rollback/restore plan:
```

- [ ] Реальные персональные и оперативные данные отсутствуют.
- [ ] Secrets, `.env`, databases, dumps, backups and sensitive logs отсутствуют.

## Автоматические gates

| Gate | Run/job/result |
|---|---|
| EOD CI | |
| Development stack | |
| Documentation contract | |
| Profile tests/gates | |

- [ ] Exact current head прошёл обязательный CI.
- [ ] Ноль обнаруженных tests не принят как success.
- [ ] Skipped tests перечислены и оценены.

## VPS development

```text
checkout: /srv/eod/development
branch:
HEAD:
database: eod_development / eod_development
refresh or rebuild:
health:
HTTP:
preview isolation:
```

- [ ] Development не находится на `main`.
- [ ] Worktree clean.
- [ ] App and db healthy.
- [ ] Preview не изменён.

## Приёмочный маршрут

1.
2.
3.

### Ожидаемый результат

-

### Результат пользователя

```text
not checked / accepted / accepted with follow-up / repair required / rejected
```

## Known limitations and follow-up

-

## Документация

- [ ] `CURRENT_STATE.md` обновлён, если изменилось фактическое состояние.
- [ ] `CURRENT_HANDOFF.md` обновлён.
- [ ] `MODULE_MAP.md` обновлён, если изменился статус модуля.
- [ ] `OPEN_ITEMS.md` обновлён.
- [ ] Decision/baseline/acceptance/release notes обновлены, если применимо.
- [ ] Runbook/ADR обновлены.

## Merge gate

```text
accepted exact head SHA:
explicit user merge permission: not received / received
planned merge method:
```

- [ ] PR не draft.
- [ ] Blocking review threads resolved.
- [ ] Пользователь явно разрешил merge.
- [ ] Merge будет выполнен с expected head SHA.

## Post-merge

Заполняется после merge:

```text
merge commit:
preview checkout HEAD:
backup/migrations/deployment:
preview health:
preview HTTP:
database identity:
new accepted baseline:
```