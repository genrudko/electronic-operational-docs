# ЭОД — сквозные демонстрационные сценарии

Сценарии определяют целевой внутренний показ. Их текущая фактическая готовность проверяется в PLAN-001; документ не утверждает, что каждый маршрут уже реализован полностью.

## Общие preconditions

- presentation database reset выполнен;
- exact branch/head зафиксирован;
- `operator.demo` and `supervisor.demo` доступны;
- health and HTTP gates success;
- пользователь работает через обычный browser;
- исходное состояние сценария известно.

## Сценарий 1 — начало смены

### Цель

Оперативный работник входит в систему и видит текущее состояние документации и незавершённых вопросов.

### Маршрут

1. войти как `operator.demo`;
2. открыть рабочее место/главную страницу;
3. увидеть текущую смену, последние оперативные записи, незавершённые дела и связанные документы;
4. перейти к документации рабочего места;
5. открыть актуальную позицию/редакцию;
6. вернуться без потери контекста.

### Проверяется

- organization/workplace isolation;
- понятная сводка;
- русская terminology;
- отсутствие technical noise;
- связи с документацией.

## Сценарий 2 — оперативная запись с помощью

### Цель

Создать запись оперативного журнала с шаблоном, сокращением и equipment reference.

### Маршрут

1. открыть создание записи;
2. выбрать template;
3. заполнить параметры;
4. использовать abbreviation expansion;
5. выбрать equipment через searchable picker;
6. проверить editable semantic link;
7. сохранить запись;
8. найти её в chronology and search.

### Проверяется

- editor stability;
- keyboard navigation;
- caret/focus/scroll;
- no duplicated link icon;
- time of event vs registration;
- equipment snapshot.

## Сценарий 3 — дефект оборудования

### Цель

Зарегистрировать дефект из оперативного события и сохранить взаимные связи.

### Маршрут

1. открыть существующую оперативную запись;
2. создать/связать defect record;
3. выбрать equipment;
4. заполнить source-bound defect fields;
5. сохранить и открыть карточку дефекта;
6. перейти обратно к оперативной записи;
7. проверить history and status.

### Проверяется

- source-bound form;
- cross-document link;
- specialized validation;
- immutable history;
- search/filter by equipment/status.

## Сценарий 4 — заявка и распоряжение

### Цель

Создать заявку, затем связанное распоряжение и проследить цепочку.

### Маршрут

1. создать application;
2. указать объект, оборудование, сроки и основание;
3. выполнить допустимый status transition;
4. создать disposition из заявки;
5. указать issuer/recipient/content;
6. связать документы с оперативной записью;
7. открыть timeline.

### Проверяется

- numbering;
- roles and transitions;
- source fields;
- application → disposition relation;
- audit and snapshots.

## Сценарий 5 — работа по наряду или распоряжению

### Цель

Показать базовую регистрацию работы без заявления о полном юридически значимом paperless lifecycle.

### Маршрут

1. выбрать режим оригинала: paper/hybrid/electronic demo;
2. создать permit/disposition work record;
3. указать работу, место, equipment and participants;
4. зафиксировать допустимые demo events: admission/suspension/resumption/completion;
5. связать с журналом работ и оперативной записью;
6. открыть историю событий.

### Проверяется

- honest legal mode label;
- separate events;
- participant roles;
- no retroactive overwrite;
- source and normative limitations visible.

## Сценарий 6 — выдача и возврат ключа

### Цель

Провести полный короткий lifecycle ключа.

### Маршрут

1. выбрать ключ/место хранения;
2. указать получателя, основание и время выдачи;
3. сохранить issuance;
4. найти outstanding key;
5. зарегистрировать возврат;
6. проверить issuer/receiver/returner and timestamps;
7. убедиться, что ключ больше не числится выданным.

### Проверяется

- uniqueness/current state;
- role and participant selection;
- audit;
- clear outstanding filter;
- prevention of invalid duplicate issuance.

## Сценарий 7 — документ переключений

### Цель

Зарегистрировать switching document без автоматической генерации операций.

### Маршрут

1. создать карточку БП/ТБП/программы;
2. указать type, number, status, equipment, application basis and disposition;
3. назначить executor and controller;
4. приложить безопасный demo file или ввести manual operation sequence;
5. связать с оперативной записью;
6. отметить выполнение/остановку/продолжение в допустимом demo объёме.

### Проверяется

- граница registry vs generator;
- relations;
- participants;
- event history;
- отсутствие ложного safety validation claim.

## Сценарий 8 — сдача смены

### Цель

Завершить сквозной день и передать незавершённые вопросы следующей смене.

### Маршрут

1. открыть shift summary;
2. увидеть новые записи, active defects, applications, dispositions, works and issued keys;
3. отметить или сформировать unfinished matters;
4. подготовить report;
5. выполнить handover/acceptance as demo users;
6. войти принимающей ролью и проверить доступность переданной информации.

### Проверяется

- cross-module aggregation;
- no lost unresolved item;
- role separation;
- timestamps and audit;
- usable demonstration finale.

## Итоговая оценка

Для каждого сценария фиксируются:

```text
status: not implemented / partial / passes / accepted
exact head:
data reset:
account:
blocking defects:
non-blocking limitations:
evidence:
```

Release-A требует прохождения обязательного ядра без blocking defects.