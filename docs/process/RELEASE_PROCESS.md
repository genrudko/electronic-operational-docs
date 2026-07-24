# ЭОД — процесс принятия и выпуска

## 1. Уровни

- `working branch` — незавершённое или ещё не принятое изменение;
- `ready for review` — automated and VPS gates completed;
- `accepted` — пользователь подтвердил результат и разрешил merge;
- `merged` — change включён в `main`;
- `application baseline` — merged `main` дополнительно синхронизирован с preview и прошёл post-merge gate;
- `metadata follow-up` — documentation-only фиксация уже принятого baseline;
- `milestone release` — устойчивый демонстрационный рубеж с release notes/tag.

## 2. Подготовка к приёмке

AI фиксирует:

- exact PR head;
- CI runs;
- migrations/data changes;
- development branch/database identity;
- health and HTTP results;
- acceptance route;
- known limitations.

## 3. Пользовательское решение

Допустимые результаты:

- принять и разрешить merge;
- принять с follow-up;
- отправить на repair;
- отклонить и изменить направление.

## 4. Merge

Merge выполняется только после явного разрешения и с expected head SHA. Если head изменился, acceptance считается относящейся к старому SHA и требуется повторная проверка применимых частей.

## 5. Post-merge preview

Порядок:

1. определить merge commit;
2. backup preview database, если change затрагивает schema/data;
3. `git pull --ff-only origin main` в `/srv/eod/repository`;
4. rebuild/recreate app при необходимости;
5. migrate с контролируемым environment;
6. проверить containers, database identity, health and HTTP;
7. проверить demo authentication или профильный smoke;
8. при failure выполнить rollback/restore;
9. зафиксировать новый application baseline.

## 6. Metadata-only follow-up

Merge commit невозможно записать внутрь документации до его появления. Поэтому после успешного post-merge gate допускается короткий documentation-only PR, который фиксирует уже принятый application baseline в:

- `CURRENT_STATE.md`;
- `CURRENT_HANDOFF.md`;
- `BASELINE_HISTORY.md`;
- `ACCEPTANCE_HISTORY.md`;
- release notes;
- связанных roadmap/open-items/module-map документах.

Такой follow-up:

- не меняет application behavior, schema, migrations or runtime data;
- не создаёт новый application baseline только из-за собственного documentation commit;
- не требует бесконечной цепочки follow-up для записи собственного SHA;
- проходит documentation CI и documentation-only preview health gate;
- остаётся видимым в обычной `main` history.

Следующий application baseline появляется после нового принятого изменения, затрагивающего application/runtime или отдельный значимый operating-system milestone, для которого принято явное baseline decision.

## 7. Tags

Tag создаётся после post-merge success для значимых рубежей:

```text
eod-baseline-<milestone>
eod-demo-<version>
```

Tag не создаётся на непринятой branch.

## 8. Release notes

Для milestone указываются:

- baseline SHA/tag;
- user-visible changes;
- domain decisions;
- migrations/data impact;
- verified scenarios;
- known limitations;
- rollback/recovery information;
- next planned gate.

## 9. Accepted with follow-up

Неблокирующие замечания:

- добавляются в `OPEN_ITEMS.md`;
- получают отдельный work item;
- не описываются как уже исправленные;
- не меняют accepted scope задним числом.

## 10. Rollback

Post-merge rollback является отдельным управляемым действием. Предпочтение:

- revert commit для code history;
- restore verified backup для данных;
- проверка совместимости schema/data;
- новая запись в decision/acceptance/baseline history.

Нельзя переписывать `main`, чтобы скрыть неудачный release.

## 11. Internal prototype release

Дополнительно нужны:

- полный regression checklist;
- presentation reset;
- 6–8 сквозных scenarios;
- known limitations;
- user guide for demo route;
- clean restoration test;
- explicit statement that release is a non-production prototype.