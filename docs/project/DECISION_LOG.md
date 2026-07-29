# ЭОД — журнал решений

Записи добавляются хронологически. Изменение решения оформляется новой записью; историческая запись не удаляется.

## 2026-07-22 — единое ядро структурированных журналов

Оперативный журнал остаётся специализированным модулем. Остальные журналы используют общее ядро: публикуемая схема, запись, поля, статусы, участники, оборудование, документы, связи, редакции, аудит, поиск и фильтры.

## 2026-07-23 — Patch 011.6 принят

Приняты импорт оборудования, персонала, оперативных прав и документации рабочего места. Импорт документации явно привязывается к активному рабочему месту; исходная неоднозначность не исправляется молча.

## 2026-07-23 — двухфазная непрерывность контекста

Чат не является единственным носителем состояния. В старом локальном workflow перед patch создавался pre-patch snapshot, а после визуального принятия — context package. Эта практика остаётся исторически значимой, но после DOCS-001 главным онлайн-источником истины становится репозиторий и его каноническая документация.

## 2026-07-23 — Patch 011.7 не зашивает конкретные журналы

Patch 011.7 реализует механизмы общего ядра. Конкретные журналы и специализированные правила относятся к следующим vertical slices.

## 2026-07-23 — snapshots проверяются по содержанию

ZIP snapshot не идентифицируется заранее зашитым SHA одной сборки. Проверяются самосогласованные manifest, sidecar checksum, branch, HEAD, clean worktree и назначение.

## 2026-07-23 — patch logging начинается до preflight

Контролируемый отказ обязан оставлять диагностический лог. Logger подключается до дорогих или блокирующих проверок.

## 2026-07-23 — payload проверяется целиком

Встроенные текстовые файлы автономного patch должны были использовать LF, один завершающий перевод строки и проходить полный decode/hash contract. После перехода к GitHub-first это правило сохраняется как требование качества committed text files, а не как обязательный формат доставки.

## 2026-07-24 — рабочие формы только из утверждённых источников

Общее ядро не является пользовательским конструктором. Состав граф, порядок, роли и действия устанавливаются по утверждённым инструкциям и приложениям. Технические схемы не допускают рабочих записей.

## 2026-07-24 — постоянный CI на Linux/PostgreSQL

GitHub Actions использует Ubuntu 24.04, Python 3.13 и PostgreSQL 18.4. Постоянный pipeline выполняет lint, compile, Django checks, migration checks, migrations, актуальный профильный gate, collectstatic и test command.

Исторические `gate_patch_*.py` не запускаются все подряд: они являются контрактами своего baseline, а не автоматически кумулятивным набором.

## 2026-07-24 — безопасный preview на VPS

Accepted preview отделён от локальной разработки:

- checkout `/srv/eod/repository`;
- только `main`;
- Compose project `eod-preview`;
- PostgreSQL `eod_preview`;
- loopback port `8765`;
- PostgreSQL host port отсутствует.

## 2026-07-24 — presentation data перенесены в PostgreSQL

Accepted presentation profile импортирован в preview PostgreSQL с проверкой fixture object count, database identity, health endpoint и demo authentication.

## 2026-07-24 — изолированный VPS development

Development получил отдельные checkout, branch, Compose project, database/user, volume, networks, secrets и loopback port `8766`. Reset development data читает preview dump, но восстанавливает только `eod_development`.

## 2026-07-24 — GitHub-first/VPS-first вместо patch-download

Нормальный цикл больше не требует скачивать и запускать автономные Python patch-файлы. Ассистент коммитит изменение в GitHub, VPS получает его через `git pull --ff-only`, затем выполняются checks/tests и визуальная приёмка.

Patch-файл остаётся только аварийным fallback.

## 2026-07-24 — человек исключён из механической цепочки программирования

Пользователь не редактирует код, не собирает файлы и не устраняет синтаксические ошибки. Он сохраняет роли владельца продукта, предметного эксперта и приёмщика.

Merge в `main` остаётся обязательным человеческим контрольным воротом и выполняется только по явному разрешению пользователя.

## 2026-07-24 — репозиторий становится главным онлайн-источником истины

DOCS-001 вводит канонический индекс, current state, handoff, plans, runbooks, acceptance records и CI-контракт. Чат и локальные context packages становятся вспомогательными, а не первичными источниками.

## 2026-07-24 — план подлежит ревизии после DOCS-001

Исторический master plan сохраняется, но очередность не применяется автоматически. Следующий этап — доказательная сверка требований с code, migrations, UI, tests, presentation data and acceptance, после чего утверждается master plan v3.0.

## 2026-07-24 — ЩПТ и ШОТ являются общей технической группой

ЩПТ и ШОТ не моделируются как разные технические виды только из-за обозначения. Они относятся к оборудованию системы оперативного постоянного тока; различие сохраняется как исходное обозначение, место установки или конструктивный вариант.

## 2026-07-24 — журнальный контур развивается последовательными vertical slices

После PLAN-001 конкретные журналы доводятся по одному. Рабочий цикл:

```text
минимальный общий контракт
→ один журнал целиком
→ минимальные реальные связи
→ automated and user acceptance
→ следующий журнал
```

Связи с оперативным журналом, оборудованием, участниками и документом-основанием не откладываются до завершения всего пакета, но полноценная универсальная timeline не проектируется заранее без реальных кейсов.

## 2026-07-24 — журнал ключей рассматривается как paper-first

Полный электронный lifecycle выдачи и возврата ключей исключён из обязательного объёма внутреннего прототипа. Бумажный журнал остаётся основным рабочим оригиналом. Электронное отражение, справочник или контрольный реестр допускаются только как необязательный вспомогательный контур после отдельной предметной и UX-оценки.

## 2026-07-24 — UX-001 создаёт единый дизайн-контракт

Параллельный UI/UX-чат формирует design principles, tokens, components, page archetypes and interaction contract. Решения проверяются на реальных экранах, длинных русских данных и сменных сценариях. UI-чат не становится вторым интеграционным центром и не меняет domain model самостоятельно.

## 2026-07-24 — документация обновляется вместе с каждым принятым изменением

Принятый patch, feature slice, repair или infrastructure change не считается полностью завершённым без актуализации применимых canonical docs в том же PR или в обязательном post-merge documentation follow-up. `CURRENT_STATE.md` и `CURRENT_HANDOFF.md` должны позволять продолжить работу даже при внезапном завершении чата.

## 2026-07-25 — DOCS-001 принят как project operating system

Пользователь принял DOCS-001 и явно разрешил squash merge PR #4. Merge commit `e18872face7f27f489056b72fed31e5586121b0c` прошёл post-merge preview verification: main/HEAD, clean worktree, documentation contract, healthy containers, HTTP 200, database identity `eod_preview` and no pending migrations.

Этот commit становится accepted application baseline. Следующий обязательный этап — PLAN-001.

## 2026-07-25 — metadata-only follow-up не создаёт рекурсивный baseline

Merge commit невозможно записать внутрь документации до его появления. Поэтому после post-merge gate создаётся короткий documentation-only PR, фиксирующий уже принятый SHA.

Такой follow-up:

- не меняет application/runtime/schema/data;
- не становится новым application baseline только из-за собственного documentation commit;
- не запускает бесконечную цепочку follow-up;
- проходит documentation CI and documentation-only preview health gate.

## 2026-07-25 — UX-001 v0.3 принимается только как provisional design contract

Пользователь ещё не видел новое визуальное направление на реальных макетах или runtime-прототипе. Поэтому UX-001 v0.3 сохраняется в репозитории как обратимая проектная основа, а не как визуально принятый стандарт.

```text
status: provisional
visual acceptance: pending
implementation authorization: not granted
```

Приняты структурные границы: самостоятельная visual identity, evidence model, component/interaction contracts, page archetypes и reference-screen requirements. Не приняты concrete palette, typography, density, radii, shadows, shell composition и внешний вид reference screens.

Следующий gate — сравнить два компактных визуальных направления на shell и одном показательном structured-journal screen, получить решение пользователя, затем проверить выбранный вариант ограниченным runtime-прототипом. Массовое внедрение до этого не разрешено.

## 2026-07-25 — QUALITY-001 восстанавливает реальное выполнение тестов

PR #8 принят и squash-merged в `4237aadc2cfdee518567024c2b45b653f49c16e7`. Полный PostgreSQL suite выполняется командой `python manage.py test apps --verbosity 2`; на exact accepted PR head подтверждено `497/497 OK`. Нулевое test discovery больше не считается текущим долгом.

## 2026-07-25 — короткий AUTO-спринт перед продолжением PLAN-001

Перед продолжением основной продуктовой разработки выполняются:

```text
AUTO-000 documentation contract
→ AUTO-001 development orchestrator MVP
→ return to PLAN-001
```

AUTO-001 устраняет ручной мост между green PR и VPS development. Полный набор AUTO-002+ не является блокером продуктовой работы.

## 2026-07-25 — ограничения AUTO-001 MVP

AUTO-001 обязан использовать exact PR head SHA, один development deployment одновременно, минимальные права и доказанную preview isolation. Обычный self-hosted runner с `sudo` и Docker socket запрещён. Automation не получает права automatic merge; пользователь остаётся единственным merge gate.

## 2026-07-25 — AUTO-000 принят и разрешает отдельную реализацию AUTO-001

Пользователь принял AUTO-000 и явно разрешил squash merge PR #9. Exact accepted head `3a4b4770e1fce41405813efa1e931288bf1a26b8`; merge commit `937d2cd2b187c17fac3088ccfc52079fc4608306` прошёл post-merge preview verification после rebuild текущего source image.

Принятие AUTO-000 означает:

- architecture/security/acceptance contract утверждены;
- отдельный AUTO-001 implementation work item разрешён;
- AUTO-001 ещё не реализован;
- automatic merge и preview write остаются запрещены;
- перед executable implementation обязателен actual infrastructure gap analysis;
- после AUTO-001 MVP работа возвращается к PLAN-001.

Accepted application baseline повышен до `main / 937d2cd2b187c17fac3088ccfc52079fc4608306`.

## 2026-07-25 — постоянный Chat 0 и отдельные work-item chats

Для предотвращения смешения интеграционных решений и implementation detail принят следующий communication workflow:

- один постоянный Chat 0 хранит baseline, priorities, architecture, acceptance and next-work decisions;
- каждый отдельный work item/PR реализуется в отдельном implementation chat;
- repairs, CI failures and acceptance fixes остаются в том же work-item chat;
- research chats отделяются от implementation chats;
- после каждого accepted merge работа возвращается в Chat 0;
- Chat 0 не реализует каждый PR внутри себя, а готовит starter/handoff следующего отдельного чата;
- GitHub и canonical docs остаются source of truth, чат — координационный слой.

Первым применением модели после DOCS-005 является отдельный AUTO-001 implementation chat. PLAN-001 продолжается после принятия AUTO-001 MVP.

## 2026-07-29 — исследование вертикальных продуктов принято как decision input

Комплект `eod_vertical_products_research_20260729_v1` принят как доказательная база: 16 продуктов и модулей, 27 источников, 18 UX-паттернов и 16 предварительных решений.

Внешний факт, наблюдение на экране, аналитический вывод и предлагаемое решение ЭОД различаются. Используется классификация `ADOPT / ADAPT / REJECT / DEFER / VERIFY`. Исследовательская находка не становится requirement автоматически.

Canonical traceability хранится в `docs/research/`. Сторонние screenshots, PDF и видео не включаются в публичный репозиторий без подтверждённого права публикации.

## 2026-07-29 — принят best-of-breed critical path

Перед реализацией основного модуля определяется главный ежедневный пользовательский сценарий. Он сравнивается с фактической бумагой, Excel/Word и релевантным узким продуктом по времени, количеству действий, повторному вводу, ручному тексту, вероятности ошибки, печатному результату и восстановлению после прерывания.

Принцип требует конкурентоспособности критического маршрута, но не копирования полного функционала специализированного продукта.

## 2026-07-29 — первичный объект и производные представления разделены

Один первичный документ или факт может формировать реестр, журнал учёта, рапорт и отчёт. Производные представления не становятся второй независимой базой и не требуют повторного ручного ввода.

Для сложных документов отдельно проектируются authoring/печать и domain/legal lifecycle. В частности, быстрое оформление наряда не смешивается с полным электронным lifecycle допуска и подписей.

## 2026-07-29 — Direction A становится общесистемным UX/UI contract

Одинаковые по назначению элементы во всех журналах должны выглядеть и работать одинаково. Общими являются shell, navigation, visual tokens, page headers, buttons, fields, tabs, cards, statuses, tables, selectors, pickers, overlays и responsive behavior.

Специализированными остаются оперативный editor, ribbon, лист/разворот, утверждённые формы, наряд, переключения, defect lifecycle, маршрут обхода и другие domain workspaces.

Копирование feature-local visual classes под новым префиксом и их независимое развитие запрещено. OPJ-UX-001 является вторым реальным потребителем shared Direction A layer.

## 2026-07-29 — принят risk-tiered development loop

Рабочий цикл разделён на:

```text
factual preflight
→ focused repair loop
→ candidate profile
→ one final exact-head gate
```

Micro-repair получает пропорциональные проверки и trusted hot refresh. Полный PostgreSQL suite и все required workflows не запускаются после каждой косметической правки. Один полный final gate выполняется на окончательном accepted head.

Цель ручных технических команд пользователя — ноль. Exact-SHA validation, rollback, preview isolation, security boundaries и пользовательский merge gate не ослабляются.

## 2026-07-29 — CI-OPT-001 следует после OPJ-UX-001

После завершения пользовательской приёмки OPJ-UX-001 выполняется короткий factual/implementation slice `CI-OPT-001`.

Его цель — убрать доказанное дублирование полного PostgreSQL suite между GitHub и VPS при неизменном exact SHA, сохранив required checks, migration/data checks, runtime smoke, environment trust, rollback и evidence.

`DEV-EVIDENCE-001`, `UI-CONTRACT-001` и `WORKITEM-BOOTSTRAP-001` выполняются только при измеримой выгоде и не должны превращаться в параллельный большой инфраструктурный спринт.
