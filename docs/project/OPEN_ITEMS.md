# ЭОД — открытые вопросы и отложенные задачи

## 1. Текущий обязательный инфраструктурный этап

### AUTO-000

- принять automation architecture;
- принять security boundaries;
- принять exact-SHA contract;
- принять acceptance and rollback;
- зафиксировать scope AUTO-001 MVP;
- не менять runtime, workflows, VPS или secrets.

### AUTO-001

- проверить сетевой маршрут GitHub-hosted runner → VPS;
- выбрать restricted transport;
- реализовать exact-SHA orchestrator;
- реализовать GitHub and VPS concurrency locks;
- реализовать sanitised evidence;
- выполнить два success и один failure acceptance case;
- подтвердить preview isolation;
- исключить automatic merge.

После принятия AUTO-001 MVP продолжается PLAN-001. AUTO-002+ не являются предварительным блокером продукта.

## 2. PLAN-001 — доказательная ревизия

PR #7 остаётся Draft.

Нужно установить по каждому модулю:

- что фактически реализовано;
- что реализовано частично;
- что сделано иначе, чем планировалось;
- какие tests/gates реально актуальны;
- какие presentation scenarios работают;
- какие этапы утратили актуальность;
- какое направление и vertical slice выбрать следующим.

Результат должен включать конкретный первый журнальный vertical slice, master plan v3.0 и минимальный automated smoke/integration suite поверх действующего полного PostgreSQL test baseline.

## 3. Структурированные журналы

Требуют проверки и/или завершения:

- журнал заявок;
- журнал распоряжений;
- журнал дефектов оборудования;
- журнал ввода оборудования в работу;
- журнал РЗА и телемеханики;
- журнал учёта работ по нарядам;
- журнал учёта работ по распоряжениям.

Для каждой формы нужны source traceability, точные графы, специализированные rules, UI, минимальные реальные связи, presentation data, automated gates и acceptance scenario.

Рабочая стратегия:

```text
один журнал целиком
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Предварительный первый кандидат — журнал дефектов, но PLAN-001 должен подтвердить или опровергнуть эту гипотезу.

## 4. Журнал выдачи и возврата ключей

Текущая продуктовая позиция — paper-first:

- бумажный журнал остаётся основным рабочим оригиналом;
- полный электронный lifecycle выдачи/возврата не входит в обязательный внутренний прототип;
- возможный электронный справочник, outstanding-control или зеркальная регистрация требуют отдельного предметного и UX-решения;
- демонстрационный сценарий не должен изображать бумажный процесс полностью электронным без реальной необходимости.

## 5. Наряды и распоряжения

Открытые предметные вопросы:

- электронный оригинал наряда;
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

Минимальный реестр требует реализации или доказательной ревизии. Автоматическая генерация БП/ТБП/ТПП и safety engine остаются отдельной дальней очередью.

## 8. Оперативный журнал

Нужна отдельная ревизия редактора и assistance:

- insertion caret в конец записи;
- Ctrl+Left/Right/Home/End внутри текущей записи;
- PgUp/PgDown без прокрутки всей страницы;
- редактирование автоматически вставленной semantic link;
- отсутствие дублирования link icon при copy/paste;
- отсутствие скачка страницы при клике вне листа;
- шаблоны, сокращения и автодополнение.

Runtime-видео подтверждает конечное состояние с повторяющимися semantic markers, но не доказывает точную последовательность воспроизведения. Marker serialization/copy-paste остаётся блокирующим repair candidate.

## 9. UX-001

UX-001 v0.3 подготовлен и сохраняется в репозитории как provisional project contract.

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Структурно подготовлены:

- evidence-based audit;
- runtime video audit;
- самостоятельное visual direction;
- UI principles;
- candidate design tokens;
- component contract;
- interaction/keyboard/focus/overlay contract;
- page archetypes;
- three textual reference-screen contracts;
- staged implementation roadmap.

Открытые visual gates:

1. подготовить два компактных визуальных направления на application shell и одном показательном structured-journal screen;
2. получить выбор/корректировку пользователя;
3. реализовать ограниченный runtime prototype на development contour;
4. проверить target desktop, long Russian data, density, states, focus and overlays;
5. зафиксировать accepted tokens только после визуальной приёмки.

Не приняты:

- concrete palette;
- typography scale;
- density;
- radii and shadows;
- shell composition;
- окончательный внешний вид reference screens;
- dark-theme release scope;
- target desktop viewport;
- названия top-level product areas.

Риски:

- превратить provisional contract в неизменяемый стандарт без визуальной проверки;
- развернуть дизайн на все экраны до проверки одного real vertical slice;
- потерять рабочую информационную плотность ради «воздуха»;
- смешать visual recommendations с domain lifecycle;
- создать сходство с identifiable third-party branding;
- отложить blocking operational-journal repairs до полного редизайна.

## 10. Импорт и данные

- шесть неоднозначных строк документации рабочего места остаются в staging;
- проверить полноту и терминологию импорта оборудования;
- поддерживать общий equipment family для ЩПТ/ШОТ;
- закрепить управляемый RU→EN domain lexicon;
- не импортировать реальные чувствительные данные в presentation profile.

## 11. Тесты и quality gates

QUALITY-001 закрыт:

```text
test discovery: fixed
full suite: 497/497 OK
command: python manage.py test apps --verbosity 2
```

Открыто:

- определить минимальный обязательный smoke/integration subset для быстрых product gates;
- сохранять полный `test apps` как основной regression baseline;
- добавлять профильные tests/gates вместе с каждым журналом;
- добавить automated regression для semantic marker copy/paste/save/reload;
- добавить AUTO-001 negative/security tests;
- позднее добавить structured machine-readable test evidence.

## 12. Инфраструктура

- AUTO-001 restricted gateway;
- сетевой маршрут GitHub-hosted runner → VPS;
- deploy credential rotation/revoke;
- stale-lock recovery;
- artifact retention;
- backup policy перед future automatic migrations;
- определить retention backups;
- reverse proxy/HTTPS/domain не являются текущим блокером;
- production hardening относится к отдельному официальному этапу;
- не расширять инфраструктурный scope сверх AUTO-001 MVP без подтверждённой необходимости.

## 13. Документационная непрерывность

- применимые canonical docs обновляются в том же PR, что и изменение;
- после принятого feature/repair обязательны актуальные `CURRENT_STATE.md` и `CURRENT_HANDOFF.md`;
- новый application baseline фиксируется после post-merge verification;
- metadata-only follow-up не создаёт новый baseline только из-за собственного SHA;
- UX package сохраняется без подмены provisional status визуальной приёмкой;
- automation docs не изображают AUTO-001 реализованным до фактической acceptance;
- внезапное завершение чата не должно требовать восстановления состояния по памяти.
