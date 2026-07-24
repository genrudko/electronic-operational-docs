# ЭОД — политика веток и pull request

## 1. Назначение

Branch/PR является изолированной единицей проектирования, реализации, проверки и приёмки одного work item.

## 2. Создание ветки

Ветка создаётся от current accepted `main`, а не от локальной памяти или старой feature branch.

```text
feature/<number>-<name>
fix/<number>-<name>
infra/<number>-<name>
docs/<number>-<name>
research/<number>-<name>
```

## 3. Scope

PR должен иметь одну понятную цель. Допустимы связанные code, migrations, tests, fixtures, docs and runbooks, необходимые для полного vertical slice.

Не допускается незаметно добавлять новый продуктовый scope в repair.

## 4. Draft

Draft PR используется, когда:

- implementation ещё не завершена;
- CI expected to fail while foundation is being built;
- требуется ранняя фиксация архитектуры или evidence.

Ready for review — только после завершения применимых automated gates and VPS checks.

## 5. Обязательная структура PR

- цель;
- контекст и основание;
- scope/in-scope/out-of-scope;
- architecture/data/migration impact;
- changed files/areas;
- tests and CI evidence;
- VPS deployment evidence;
- acceptance route;
- user result;
- known limitations;
- rollback/data restore note;
- exact head SHA;
- explicit merge permission.

## 6. Evidence

Утверждения формулируются точно:

- `CI run X succeeded` — только при фактическом conclusion success;
- `preview unaffected` — только после simultaneous health/isolation gate;
- `accepted` — только после пользовательского решения;
- `post-merge verified` — только после фактического preview check.

## 7. Review threads

Blocking thread должен быть:

- исправлен и resolved;
- либо явно признан non-blocking и перенесён в `OPEN_ITEMS.md`.

Игнорирование thread без решения запрещено.

## 8. Repair commits

Repair остаётся в исходном PR, если исправляет acceptance criteria того же work item. Изменение product direction требует нового решения и, при необходимости, новой branch.

## 9. Merge permission

AI не интерпретирует молчание или отсутствие замечаний как разрешение. Нужна однозначная команда пользователя.

## 10. Merge protection

При merge передаётся expected head SHA. Если head изменился после приёмки, merge прекращается до повторной проверки.

## 11. После merge

PR дополняется или связанная документация фиксирует:

- merge commit;
- post-merge main/preview status;
- новый baseline;
- follow-up items.

## 12. Закрытие без merge

PR закрывается без merge, если:

- направление отвергнуто;
- решение заменено другим;
- branch скомпрометирована данными/историей;
- work item потерял актуальность.

Причина закрытия фиксируется явно.