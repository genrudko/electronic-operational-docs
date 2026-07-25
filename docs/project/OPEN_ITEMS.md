# ЭОД — открытые вопросы и отложенные задачи

## 1. Текущий обязательный инфраструктурный этап

### AUTO-000 — закрыт

Принят пользователем, merged PR #9 и post-merge verified на `main / 937d2cd2b187c17fac3088ccfc52079fc4608306`.

Зафиксированы:

- automation architecture;
- security boundaries;
- exact-SHA contract;
- acceptance and rollback;
- scope AUTO-001 MVP;
- запрет automatic merge;
- отсутствие runtime/workflow/VPS changes внутри AUTO-000.

### DOCS-005 — текущий metadata follow-up

- записать accepted baseline `937d2cd…`;
- обновить state/handoff/history/roadmap/release notes;
- подготовить новый Chat 0;
- не менять application runtime, workflows, VPS, schema, data или secrets;
- не считать собственный будущий merge SHA новым application baseline.

### AUTO-001 — следующий implementation work item

До написания executable automation:

- проверить фактический main/exact SHA/open PR/branches;
- прочитать actual workflows, compose, scripts, runbooks и весь `docs/automation/`;
- проверить route GitHub-hosted runner → VPS;
- выбрать restricted transport;
- выполнить documented gap analysis.

Реализация должна:

- принимать только trusted trigger;
- проверять green required checks для current PR head;
- выполнять exact-SHA deployment в `/srv/eod/development`;
- поддерживать явно выбранный `refresh` или `rebuild`;
- выполнять `check`, full `test apps`, `status`;
- проверять preview isolation;
- использовать GitHub and VPS concurrency locks;
- публиковать sanitised evidence;
- fail closed при SHA mismatch, dirty worktree, unknown profile или ambiguous result;
- исключать automatic merge, preview write и arbitrary shell.

Acceptance:

- два последовательных successful deployments;
- один intentional failure case;
- exact-SHA and superseded proof;
- preview isolation proof;
- отсутствие ручных VPS-команд пользователя в normal run;
- explicit user acceptance.

После AUTO-001 MVP продолжается PLAN-001. AUTO-002+ не являются предварительным блокером продукта.

## 2. PLAN-001 — доказательная ревизия

PR #7 остаётся Draft и был создан от более старого main. После AUTO-001 требуется безопасно синхронизировать branch с accepted main без потери instrumentation.

Нужно установить по каждому модулю:

- что фактически реализовано;
- что реализовано частично;
- что сделано иначе, чем планировалось;
- какие tests/gates актуальны;
- какие presentation scenarios работают;
- какие этапы утратили актуальность;
- какой vertical slice выбрать следующим.

Результат:

- master plan v3.0;
- concrete first journal vertical slice;
- минимальный automated smoke/integration suite поверх полного `497/497` baseline;
- реалистичная последовательность product work.

## 3. Структурированные журналы

Требуют проверки и/или завершения:

- журнал заявок;
- журнал распоряжений;
- журнал дефектов оборудования;
- журнал ввода оборудования в работу;
- журнал РЗА и телемеханики;
- журнал учёта работ по нарядам;
- журнал учёта работ по распоряжениям.

Для каждой формы нужны source traceability, точные графы, specialized rules, UI, минимальные реальные связи, presentation data, automated gates и acceptance scenario.

```text
один журнал целиком
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Предварительный кандидат — журнал дефектов, но окончательное решение принимает PLAN-001.

## 4. Журнал выдачи и возврата ключей

Текущая позиция — paper-first:

- бумажный журнал остаётся рабочим оригиналом;
- полный электронный lifecycle выдачи/возврата не входит в обязательный внутренний прототип;
- electronic reference/outstanding-control/mirror registration требует отдельного предметного и UX-решения;
- demonstration scenario не должен изображать paper process полностью электронным без основания.

## 5. Наряды и распоряжения

Открытые предметные вопросы:

- electronic original work permit;
- раздельные журналы работ по нарядам и распоряжениям;
- целевые инструктажи;
- первичный и ежедневный допуск;
- изменения состава бригады;
- переводы;
- приостановка и возобновление;
- окончание, закрытие и хранение;
- доказательства действий и требования к подписям;
- paper/hybrid/electronic modes.

Решение принимается после актуального нормативного исследования.

## 6. Эксплуатационные работы

Добавить отдельную модель и/или справочники для работ в порядке текущей эксплуатации:

- перечень для оперативного персонала;
- перечень для ремонтного персонала;
- связь с рабочим местом, оборудованием и инструкцией;
- период действия и редакция.

## 7. Переключения

Минимальный реестр требует реализации или доказательной ревизии. Automatic generation БП/ТБП/ТПП и safety engine остаются отдельной дальней очередью.

## 8. Оперативный журнал

Нужна отдельная ревизия editor and assistance:

- insertion caret в конец записи;
- Ctrl+Left/Right/Home/End внутри текущей записи;
- PgUp/PgDown без прокрутки всей страницы;
- редактирование автоматически вставленной semantic link;
- отсутствие дублирования link icon при copy/paste;
- отсутствие скачка страницы при клике вне листа;
- шаблоны, сокращения и автодополнение.

Marker serialization/copy-paste/save/reload остаётся blocking repair candidate и требует automated regression.

## 9. UX-001

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Открытые visual gates:

1. два compact visual directions для application shell и одного structured-journal screen;
2. выбор/корректировка пользователя;
3. limited runtime prototype на development;
4. проверка target desktop, long Russian data, density, states, focus and overlays;
5. accepted tokens только после visual acceptance.

Не приняты:

- concrete palette;
- typography scale;
- density;
- radii and shadows;
- shell composition;
- final reference screen appearance;
- dark-theme release scope;
- target desktop viewport;
- names of top-level product areas.

## 10. Импорт и данные

- шесть неоднозначных строк документации рабочего места остаются в staging;
- проверить полноту и терминологию equipment import;
- сохранять common equipment family для ЩПТ/ШОТ;
- закрепить managed RU→EN domain lexicon;
- не импортировать реальные чувствительные данные в presentation profile.

## 11. Тесты и quality gates

Закрыто QUALITY-001:

```text
test discovery: fixed
full suite: 497/497 OK
command: python manage.py test apps --verbosity 2
```

Открыто:

- определить минимальный smoke/integration subset для быстрых product gates;
- сохранять full `test apps` как regression baseline;
- добавлять профильные tests/gates вместе с каждым журналом;
- automated regression для semantic marker copy/paste/save/reload;
- AUTO-001 negative/security tests;
- позднее structured machine-readable test evidence.

## 12. Инфраструктура

- AUTO-001 restricted gateway;
- network route GitHub-hosted runner → VPS;
- deploy credential creation/rotation/revoke;
- stale-lock recovery;
- artifact retention;
- backup policy перед future automatic migrations;
- reverse proxy/HTTPS/domain не текущий blocker;
- production hardening — отдельный официальный этап;
- не расширять AUTO-001 MVP без подтверждённой необходимости.

На VPS установлен `tmux` для устойчивости длинных ручных операций до AUTO-001.

## 13. Документационная непрерывность

- canonical docs обновляются в том же PR, что и изменение, либо обязательном metadata follow-up;
- accepted application baseline фиксируется после post-merge verification;
- metadata-only follow-up не создаёт новый baseline только из-за собственного SHA;
- UX package сохраняет provisional status до visual acceptance;
- automation docs не изображают AUTO-001 реализованным до acceptance;
- новый Chat 0 восстанавливает контекст строго по GitHub, `CURRENT_STATE.md` и `CURRENT_HANDOFF.md`;
- один work-item/PR ведётся в одном отдельном чате, включая repairs.
