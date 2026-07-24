# ЭОД — процесс принятия и выпуска

## 1. Уровни

- `working branch` — незавершённое или ещё не принятое изменение;
- `ready for review` — automated and VPS gates completed;
- `accepted` — пользователь подтвердил результат и разрешил merge;
- `merged` — change включён в `main`;
- `baseline` — merged `main` дополнительно синхронизирован с preview и прошёл post-merge gate;
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
9. зафиксировать новый baseline.

## 6. Tags

Tag создаётся после post-merge success для значимых рубежей:

```text
eod-baseline-<milestone>
eod-demo-<version>
```

Tag не создаётся на непринятой branch.

## 7. Release notes

Для milestone указываются:

- baseline SHA/tag;
- user-visible changes;
- domain decisions;
- migrations/data impact;
- verified scenarios;
- known limitations;
- rollback/recovery information;
- next planned gate.

## 8. Accepted with follow-up

Неблокирующие замечания:

- добавляются в `OPEN_ITEMS.md`;
- получают отдельный work item;
- не описываются как уже исправленные;
- не меняют accepted scope задним числом.

## 9. Rollback

Post-merge rollback является отдельным управляемым действием. Предпочтение:

- revert commit для code history;
- restore verified backup для данных;
- проверка совместимости schema/data;
- новая запись в decision/acceptance/baseline history.

Нельзя переписывать `main`, чтобы скрыть неудачный release.

## 10. Internal prototype release

Дополнительно нужны:

- полный regression checklist;
- presentation reset;
- 6–8 сквозных scenarios;
- known limitations;
- user guide for demo route;
- clean restoration test;
- explicit statement that release is a non-production prototype.