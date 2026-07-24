# ЭОД — системная архитектура

## 1. Архитектурный стиль

Приложение развивается как модульный Django monolith:

- единый deployment unit;
- разделение по предметным приложениям и services;
- PostgreSQL как основная серверная СУБД;
- общие механизмы истории, аудита, доступа и связей;
- предметные правила остаются внутри профильных модулей.

Микросервисное разделение не является текущей целью и не должно вводиться без доказанной необходимости.

## 2. Основные слои

```text
Browser UI
    ↓
Django views/forms/templates
    ↓
Application services and transitions
    ↓
Domain models, constraints and snapshots
    ↓
PostgreSQL
```

Поперечные механизмы:

- authentication and authorization;
- versioned configuration;
- audit events;
- immutable snapshots;
- source traceability;
- search and filtering;
- imports and publication;
- tests and gates.

## 3. Предметные модули

Точный статус приведён в `MODULE_MAP.md`. Крупные области:

- organizations and personnel;
- documents;
- normatives;
- equipment;
- dispatching;
- imports;
- workplace documentation;
- operational log;
- operational documentation core;
- будущие work permits, switching documents and cross-document timeline.

## 4. Оперативный журнал

Оперативный журнал сохраняет отдельную модель и UI, потому что его основной объект — последовательная текстовая запись с временем события, временем регистрации, semantic references и сменным контекстом.

Он интегрируется с общим ядром через ссылки и события, но не превращается в динамическую табличную форму.

## 5. Общее ядро структурированных журналов

Ядро предоставляет механизмы:

- published document type/schema;
- source binding;
- record and field values;
- participants;
- equipment references;
- document relations;
- states and transitions;
- revisions and audit;
- search index and filtering.

Профильный журнал добавляет:

- утверждённый набор граф;
- обязательность;
- специализированные validation rules;
- допустимые роли и переходы;
- представление списка и карточки;
- traceability tests.

## 6. История и snapshot

Историческая устойчивость обеспечивается не только foreign keys. При регистрации или публикации сохраняются канонические snapshots значимых данных:

- наименование организации;
- Ф.И.О., должность и подразделение;
- оборудование и диспетчерское наименование;
- содержимое документа;
- версия формы или источника;
- полномочия и подтверждение действия.

## 7. Импорт

Импорт проходит стадии:

```text
source file → raw staging → normalization → conflicts → review → publication
```

Исходное значение не теряется. Повторный импорт должен быть идемпотентным или явно показывать конфликт.

## 8. Runtime-контуры

### Preview

- accepted `main`;
- `/srv/eod/repository`;
- `eod-preview`;
- `eod_preview`;
- `127.0.0.1:8765`;
- стабильные presentation data.

### Development

- активная feature branch, никогда `main`;
- `/srv/eod/development`;
- `eod-development`;
- `eod_development`;
- `127.0.0.1:8766`;
- отдельные volume, secrets и networks.

## 9. CI

GitHub Actions является обязательным независимым gate. Основной pipeline проверяет Linux/Python/PostgreSQL, а отдельный development smoke подтверждает container configuration и isolation.

VPS не используется как self-hosted runner и сохраняет read-only deploy key.

## 10. Доступ

Приложения слушают только loopback. Пользователь подключается через SSH local port forwarding. Публичный reverse proxy, HTTPS и domain не являются текущим условием разработки.

## 11. Конфигурация

Локальные особенности не зашиваются в код:

- организационная структура;
- типы и формы документов;
- roles and permissions;
- numbering;
- equipment and aliases;
- dispatching relations;
- normative editions.

Они хранятся как управляемые и, где требуется, публикуемые редакции.

## 12. Будущие границы

Отдельными компонентами могут стать только после доказанной необходимости:

- генератор и safety engine переключений;
- signature/cryptography service;
- integration adapters;
- document rendering service;
- offline/mobile synchronization.

До этого они проектируются как явные границы внутри монолита.