# PROJECT-SUSTAINABILITY-001 — доказательный baseline сопровождаемости ЭОД

**Дата аудита:** 05.08.2026  
**Репозиторий:** `genrudko/electronic-operational-docs`  
**Issue:** `#48`  
**Draft PR:** `#49`  
**Ветка:** `audit/project-sustainability-001`  
**Initial exact head аудита:** `8ddae63ad3c6bf3f2a3f55a0c385f3f10283aebf`  
**Текущий main на factual preflight:** `8bd895f5b0f18df0eb4a9adc60c6c6d1f8a29db9`  
**Accepted application baseline, зафиксированный в `CURRENT_STATE.md`:** `c4e344342b647ce59a390a04329d2cadb1f34d7c`  
**Тип работы:** `DOCUMENTATION / ARCHITECTURE / AUDIT`  
**Runtime/Preview impact:** `NONE / UNTOUCHED`

## 1. Итоговый вердикт

- **[FACT]** ЭОД уже не является пустым прототипом: это работоспособный modular Django monolith с PostgreSQL-контуром CI, контролируемыми миграциями, 11 собственными Django apps, общим shell, принятыми DEFECT и OPJ UX-направлениями, персональными учётными записями, предметными полномочиями, журналированием и защищёнными зарегистрированными фактами.
- **[FACT]** На initial exact head PR #49 все пять обязательных workflows завершились успешно; основной PostgreSQL job обнаружил и успешно выполнил 716 тестов. Проверены Ruff, `compileall`, `manage.py check`, отсутствие незаявленных миграций, применение миграций на PostgreSQL 18, gate `011.7`, `collectstatic`, полный test suite и container preview smoke.
- **[GAP]** Успешный CI доказывает корректность текущего репозиторного состояния, но не доказывает промышленную эксплуатационную готовность: отсутствуют подтверждённые production profile, регулярный контрольный restore, RPO/RTO, наблюдаемость, security baseline, supply-chain controls, универсальная активация модулей и пилотный operational acceptance.
- **[GAP]** Canonical planning views фактически расходятся с принятым кодом и историей: `DEMO_RELEASE_PLAN.yaml`, `MODULE_MAP.md` и `IMPLEMENTATION_SEQUENCE.md` сохраняют устаревшие статусы отдельных модулей и очередь `SHIFT-HANDOVER-001`, хотя `PERSONNEL-AUTHORITY-001` и `OPJ-LIFECYCLE-001` уже приняты. Это создаёт риск запуска неверного work item даже при формально правильном процессе.
- **[DECISION]** Сохраняется modular Django monolith. Микросервисы не являются направлением программы и могут рассматриваться только при доказанном эксплуатационном требовании, которое невозможно закрыть модульным монолитом.
- **[DECISION]** Массовая реализация предметных модулей не должна продолжаться поверх текущих платформенных gaps. Одновременно промышленная подготовка не должна превращаться в big-bang rewrite: вводится двухступенчатая модель — минимальный gate безопасного продолжения разработки и более строгий gate пилотной эксплуатации.
- **[PROPOSAL]** До возобновления очереди предметных модулей выполнить обязательный пакет `SAFE-CONTINUATION`: reconciliation canonical state, security/secret hygiene, контрольный backup/restore, production configuration contract, module activation contract и воспроизводимую фиксацию зависимостей.
- **[PROPOSAL]** До первого пилота дополнительно закрыть наблюдаемость, incident response, upgrade/rollback rehearsal, security hardening, эксплуатационный handover, browser/visual gates, data portability и pilot acceptance.

## 2. Метод и границы доказательств

### 2.1. Проверенные источники

- **[FACT]** GitHub state: issue #48, Draft PR #49, branch/ref/head, PR diff, сравнение branch/main и workflow runs.
- **[FACT]** Canonical/project docs: `AGENTS.md`, `README.md`, `docs/INDEX.md`, `CURRENT_STATE.md`, `DEMO_RELEASE_PLAN.yaml`, `CURRENT_HANDOFF.md`, work-item contract, architecture, domain invariants, UX contract/catalog/matrix, process and runbooks, module map and implementation sequence.
- **[FACT]** Application/config evidence: `manage.py`, `pyproject.toml`, `src/eod_config/settings.py`, `src/eod_config/urls.py`, `src/eod_config/health.py`, `Dockerfile`, `compose.preview.yaml`, representative organization/document/operational-document models, migrations and test evidence from CI logs.
- **[FACT]** Workflow evidence at `8ddae63...`: EOD Documentation Contract `30989719023`, EOD CI `30989719027`, AUTO-001A `30989719006`, AUTO-001B `30989719051`, EOD Development Stack `30989719293` — all `SUCCESS`.

### 2.2. Ограничения аудита

- **[FACT]** Этот work item не меняет и не инспектирует runtime/VPS непосредственно; Preview остаётся untouched.
- **[VERIFY]** Фактические сроки хранения backup, последняя дата успешного restore и наличие внешнего мониторинга нельзя подтвердить только репозиторием. Для них требуется отдельный evidence collection на разрешённом runtime-контуре.
- **[VERIFY]** Наличие корпоративного reverse proxy, TLS termination, внешнего резервного копирования, host hardening и журналов ОС не подтверждено repository evidence.
- **[VERIFY]** Полнота upload attack surface требует отдельного inventory всех `FileField`, import endpoints и пользовательских вложений; текущий аудит подтверждает контролируемые imports, но не объявляет весь контур файлов безопасным.

## 3. Фактический inventory репозитория

### 3.1. Технологический baseline

- **[FACT]** Python `>=3.13,<3.14`; Django `>=5.2,<5.3`; gunicorn `>=26,<27`; PostgreSQL driver `psycopg[binary]`; WhiteNoise; openpyxl. Browser profile использует Playwright как optional dependency.
- **[FACT]** Пакет имеет версию `0.1.0`; зависимости заданы диапазонами в `pyproject.toml`, lock-файл в проверенном evidence не обнаружен.
- **[FACT]** Контейнер строится из `python:3.13-slim-bookworm`, устанавливает пакет через `pip install .`, работает от системного пользователя `eod`, запускает gunicorn с 2 workers × 4 threads.
- **[FACT]** Preview Compose использует `postgres:18.4-bookworm`, private backend network, `no-new-privileges`, tmpfs `/tmp`, loopback-only app port и health checks.
- **[GAP]** Базовые образы не закреплены digest; Python dependencies не зафиксированы exact lock/constraints. Повторная сборка того же commit не гарантирует побитово эквивалентный набор зависимостей.

### 3.2. Фактический code layout

Проверенный `INSTALLED_APPS`:

1. `apps.system`;
2. `apps.organizations`;
3. `apps.documents`;
4. `apps.normatives`;
5. `apps.equipment`;
6. `apps.dispatching`;
7. `apps.imports`;
8. `apps.workplace_docs`;
9. `apps.operational_documents`;
10. `apps.equipment_defects`;
11. `apps.operational_log`.

- **[FACT]** Все перечисленные apps подключены статически при старте Django; все URL-конфигурации включены глобально в `eod_config.urls`.
- **[FACT]** В middleware присутствует специализированный `EquipmentDefectRouteGuardMiddleware`, но универсальный cross-module route/service/task guard в проверенном коде не обнаружен.
- **[GAP]** Фактическая архитектура модульна по Django apps, но «app установлен» сейчас фактически равно «код модуля присутствует в процессе». Это не равно требуемой управляемой активации по организации/энергообъекту/рабочему месту.
- **[PROPOSAL]** Сохранить статическую установку Django apps и реализовать module control plane поверх неё: manifest, dependency graph, scoped activation, capability checks и read-only/retired lifecycle. Динамическое изменение `INSTALLED_APPS` не требуется и повышало бы риск миграций.

### 3.3. Сопровождаемость и coupling

- **[FACT]** `organizations` уже содержит широкий набор организационных, кадровых, квалификационных и operational-authority сущностей; `operational_documents` напрямую зависит от `documents`, `equipment` и `organizations`.
- **[FACT]** `operational_documents` использует JSON-конфигурацию схем, статусов, переходов и participant roles, что позволяет избегать копирования общего ядра для каждого структурированного журнала.
- **[GAP]** Направления зависимостей описаны архитектурно, но не закреплены автоматическим import/dependency gate. Наращивание модулей может постепенно превратить `organizations` и `system` в неформальные «god modules».
- **[GAP]** Ruff содержит точечные per-file ignores для нескольких крупных personnel-management файлов. Это не дефект само по себе, но является measurable hotspot, который должен войти в maintainability inventory, а не бесконечно расширяться.
- **[PROPOSAL]** Ввести machine-readable module manifest и автоматический dependency rule: core не импортирует feature modules; feature-to-feature dependency допускается только через объявленный contract/service.

## 4. Архитектура подключаемых модулей

### 4.1. Что уже есть

- **[FACT]** Organization, Division, Workplace, OperationalArea, EnergySite relationships и предметные права уже дают основу scoped access.
- **[FACT]** Domain invariants требуют сохранения исторических данных при отключении модуля.
- **[FACT]** Приложение имеет реальный tenant-like organization scope и тесты cross-organization isolation.

### 4.2. Чего нет

- **[GAP]** Нет единого реестра module/capability definitions и версий manifest.
- **[GAP]** Нет единой модели lifecycle `AVAILABLE → CONFIGURED → ACTIVE → READ_ONLY → RETIRED`.
- **[GAP]** Нет общего механизма активации на уровнях organization / energy site / workplace и разрешения конфликтов наследования.
- **[GAP]** Нет доказанного общего guard для routes, commands, services, background tasks, exports и APIs.
- **[GAP]** Нет acceptance matrix для комбинаций активных/неактивных модулей при migrate/upgrade/rollback.

### 4.3. Target contract

- **[DECISION]** Один deployable product, одна версия приложения и единый набор миграций.
- **[DECISION]** Деактивация запрещает новые предметные действия, но не удаляет данные и не скрывает исторические сведения для уполномоченного просмотра.
- **[PROPOSAL]** Scope resolution: наиболее конкретная настройка `workplace` перекрывает `energy_site`, затем `organization`, затем product default; запрещающие состояния `READ_ONLY/RETIRED` не могут быть неявно отменены дочерним scope без административного решения.
- **[PROPOSAL]** Миграции применяются для всех installed apps независимо от activation; inactive data сохраняется и проходит integrity tests.
- **[PROPOSAL]** Feature modules получают manifest: code, owner app, capabilities, dependencies, incompatible capabilities, activation scopes, route namespaces, permission predicates, data-retention rule, UX profile, health checks and migration compatibility.

## 5. UX-платформа и постепенная миграция

### 5.1. Сильные стороны

- **[FACT]** Direction A, shared shell, design tokens и component catalog уже закреплены канонически.
- **[FACT]** DEFECT и OPJ являются реальными reference implementations двух разных профилей: registry/process module и specialist journal workspace.
- **[FACT]** Route reference matrix классифицирует существующие маршруты и viewport/state expectations.

### 5.2. Gaps

- **[GAP]** Coexistence legacy/partial/Direction A допускается контрактом, но нет автоматического source-of-truth inventory, показывающего, какой template/static layer реально обслуживает каждый route.
- **[GAP]** История OPJ repairs подтверждает риск overlay accumulation и stale assets. Проблема решалась узкими CSS/JS repairs, но отсутствует общий gate против повторного подключения obsolete layers.
- **[GAP]** Playwright объявлен optional dependency, однако на проверенном exact-head workflow отсутствует blocking cross-browser visual/behavior suite.
- **[GAP]** Component catalog является документацией, а не версионируемым executable catalog с examples/states/tests.
- **[PROPOSAL]** Не переписывать legacy целиком. Ввести route-by-route strangler migration: inventory → target profile → shared primitive adoption → browser evidence → удаление только доказанно неиспользуемого слоя.
- **[PROPOSAL]** Создать четыре типовых профиля: `REGISTRY_PAGE`, `STANDARD_JOURNAL`, `SPECIALIST_WORKSPACE`, `PROCESS_TIMELINE`; новые модули обязаны выбрать профиль, а не создавать новую visual system.

## 6. Данные, неизменяемость и аудит

### 6.1. Реализованные гарантии

- **[FACT]** Документы, версии, snapshots, signatures, links и audit events используют `PROTECT`, защищённые managers/querysets, запрет physical delete и запрет update для immutable records.
- **[FACT]** Registered documents и published schemas блокируют последующее изменение через model API.
- **[FACT]** Присутствуют server-side numbering, unique/check constraints, SHA-256 canonical snapshots, signature snapshots и authority snapshots.
- **[FACT]** CI включает concurrency tests и доменные tests неизменяемости/изоляции.

### 6.2. Ограничения

- **[GAP]** Основная неизменяемость обеспечивается application/model layer и обычными DB constraints. Привилегированный SQL-доступ или ошибочный maintenance script способен обойти Python guards.
- **[GAP]** Нет подтверждённого периодического integrity scan, который пересчитывает digest, проверяет audit chains и выдаёт signed evidence.
- **[GAP]** Не определены retention/archive policies для операционных фактов, audit events, imports и будущих attachments.
- **[GAP]** Нет подтверждённого полного export/portability package, позволяющего передать данные, snapshots, audit и attachments другому специалисту/инсталляции.
- **[PROPOSAL]** Для первого пилота не вводить сложный blockchain/WORM. Достаточно: least-privilege DB role, запрет прямых write-доступов, регулярный integrity report, immutable backup evidence и отдельный break-glass process.

## 7. Миграции, backup, restore и rollback

- **[FACT]** CI применяет все миграции на чистом PostgreSQL 18 и проверяет отсутствие незаявленных миграций.
- **[FACT]** Репозиторий содержит подробные runbooks backup/restore, incident/rollback и post-merge deployment; destructive operations требуют backup.
- **[GAP]** Runbook прямо признаёт отсутствие утверждённой retention policy.
- **[GAP]** В repository evidence нет scheduled restore drill, последнего restore certificate, RPO/RTO, backup encryption/replication policy или автоматической проверки срока годности backup.
- **[GAP]** CI не доказывает upgrade с representative accepted database snapshot через несколько релизов и не покрывает module-set combinations.
- **[GAP]** Rollback строится вокруг пересборки/перезапуска и ручного выбора совместимого backup; immutable release image, schema compatibility matrix и rehearsed one-command rollback отсутствуют.
- **[PROPOSAL]** Перед продолжением массовых modules провести реальный non-production restore drill и зафиксировать checksum, elapsed time, object counts, integrity report и recovery decision.

## 8. Установка, deployment и operations

- **[FACT]** Preview и development разделены checkout, Compose project, env, port и database; PostgreSQL не публикуется наружу; app слушает loopback VPS port.
- **[FACT]** Контейнер работает non-root, с `no-new-privileges`; backend network internal.
- **[FACT]** Health endpoint проверяет HTTP app и `SELECT 1` в database.
- **[GAP]** `EOD_DEPLOYMENT_MODE` допускает только `development`, `ci`, `preview`; production/pilot profile отсутствует по определению.
- **[GAP]** Health endpoint не различает liveness/readiness, не проверяет migrations, storage capacity, background processing, critical configuration или module health.
- **[GAP]** Нет репозиторного evidence structured JSON logging, correlation/request IDs, metrics, alert rules, dashboards, SLO/SLI и log retention.
- **[GAP]** Incident runbook технически полезен, но не содержит severity matrix, notification chain, incident commander, SLA и postmortem deadline.
- **[PROPOSAL]** Первый operational target — single-node pilot, не HA: reproducible install, immutable image, managed secrets, DB backup off-host, reverse proxy/TLS, structured logs, metrics, alerting и rehearsed recovery.

## 9. Authentication, RBAC и security hardening

### 9.1. Реализовано

- **[FACT]** Используются персональные Django accounts, Employee profile, domain roles/authorities и action-time evaluation/snapshot.
- **[FACT]** Включены CSRF middleware, HTTP-only cookies, content-type nosniff и `X_FRAME_OPTIONS=DENY`.
- **[FACT]** Preview запрещает default secret, DEBUG, SQLite и default PostgreSQL password.

### 9.2. Gaps

- **[GAP]** В development/ci defaults остаются known fallback `SECRET_KEY` и PostgreSQL password; безопасно только при строгой изоляции, которую необходимо автоматически проверять.
- **[GAP]** В CI log evidence опубликованы демонстрационные логины/пароли. Даже если они предназначены только для demo, public reusable credentials формируют плохой operational pattern и риск повторного использования.
- **[GAP]** В settings не закреплены production cookie/TLS controls (`SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, HSTS, proxy SSL header) и нет production mode, который fail-closed проверяет их.
- **[GAP]** Password re-auth является существующим confirmation method, но MFA, privileged-session policy, account lockout/rate limiting и break-glass governance не подтверждены.
- **[GAP]** В проверенных workflows отсутствуют dependency vulnerability scan, secret scan, SAST, container scan, SBOM и signed image provenance.
- **[VERIFY]** Upload/import hardening по MIME, extension, size, antivirus, quarantine, storage isolation и access-controlled download требует отдельного inventory.

## 10. Source governance и Google Drive

- **[FACT]** GitHub закреплён единственным canonical owner; Drive допустим как библиотека исходных материалов.
- **[FACT]** `SOURCE_REGISTRY.csv` уже существует и различает source/evidence/decision.
- **[GAP]** Нет единой machine-readable матрицы `module/capability → mandatory source IDs → required local instructions → freshness owner → availability status`.
- **[GAP]** Нет автоматического gate, который не позволяет стартовать module work item при отсутствии обязательного source package.
- **[PROPOSAL]** Drive хранит оригиналы и крупные/ограниченные материалы; GitHub хранит только stable source ID, metadata, checksum, version, owner, legal/publication status и canonical decision derived from source.
- **[PROPOSAL]** Для каждого module contract добавить `required_source_ids`, `required_local_instructions`, `freshness_policy`, `drive_locator`, `github_decision_refs`.

## 11. Готовность к сопровождению другим специалистом

- **[FACT]** Репозиторий имеет сильнее среднего для демонстрационного проекта набор docs, runbooks, invariants, acceptance history и CI.
- **[GAP]** Независимая установка с нуля другим специалистом не подтверждена release evidence.
- **[GAP]** Нет единого service catalog: компоненты, owners, ports, dependencies, secrets classes, backup assets, dashboards, alerts, recurring maintenance.
- **[GAP]** Нет support matrix и процедуры передачи: L1/L2/L3, типовые incidents, escalation, access provisioning, rotation/revocation, maintenance calendar.
- **[PROPOSAL]** Exit gate `SUPPORT-HANDOVER-001`: независимый специалист разворачивает clean pilot environment только по repository docs, восстанавливает backup, выполняет upgrade/rollback и диагностирует scripted incident без устных подсказок автора.

## 12. Критерии готовности к пилотной эксплуатации

Пилот может быть объявлен готовым только при одновременном выполнении:

1. **[PROPOSAL] Configuration:** отдельный `pilot/production` fail-closed profile; no default secrets; TLS/cookie/proxy controls verified.
2. **[PROPOSAL] Identity:** персональные accounts, lifecycle joiner/mover/leaver, privileged roles, access review and break-glass procedure.
3. **[PROPOSAL] Module control:** scoped activation and deactivation tested for at least two organizations/sites/workplaces; history remains readable.
4. **[PROPOSAL] Data:** representative upgrade test, migration rollback decision, integrity scan and export package.
5. **[PROPOSAL] Recovery:** successful restore drill from off-host backup; RPO/RTO accepted; rollback rehearsal recorded.
6. **[PROPOSAL] Operations:** logs, metrics, alerts, dashboards, retention, severity/escalation and on-call ownership.
7. **[PROPOSAL] Security:** threat model, dependency/secret/container scans, upload controls, patch policy and remediation SLA.
8. **[PROPOSAL] UX:** supported-browser matrix, desktop/mobile/theme gates, no false actions, critical scenarios visually accepted.
9. **[PROPOSAL] Support:** clean install/handover by another specialist and complete runbook set.
10. **[DECISION] Product truth:** known limitations documented; no claim of legal/industrial readiness beyond accepted evidence.

## 13. Рекомендуемая граница продолжения разработки

- **[DECISION]** Не выполнять big-bang industrialization и не перестраивать продукт в микросервисы.
- **[PROPOSAL]** Gate `SAFE-CONTINUATION` должен быть закрыт до массового продолжения modules: state reconciliation, module activation contract, security baseline, dependency lock/provenance, restore drill и production configuration design.
- **[PROPOSAL]** После `SAFE-CONTINUATION` предметная разработка может возобновиться ограниченно, но первый pilot запрещён до полного `PILOT-READY` gate.
- **[PROPOSAL]** DEFECT и OPJ использовать как reference modules для platform contracts; не переписывать их заново.
- **[DECISION]** NOTES остаётся будущим подключаемым модулем после стабилизации control plane и UX profiles.
- **[WISHLIST]** Local Exchange integration остаётся последней очередью и не влияет на первый pilot.

## 14. Основные evidence references

| Evidence | Что подтверждает |
|---|---|
| `docs/project/CURRENT_STATE.md` | accepted baseline, active work item, OPJ/personnel acceptance |
| `docs/project/DEMO_RELEASE_PLAN.yaml` | canonical release planning owner и выявленный status drift |
| `docs/project/SYSTEM_ARCHITECTURE.md` | modular monolith и target module activation principles |
| `docs/project/DOMAIN_INVARIANTS.md` | tenant, authority, immutable facts, module history invariants |
| `docs/ux/UX_UI_CONTRACT_V1.md` | Direction A и gradual migration |
| `src/eod_config/settings.py` | apps, deployment modes, database/security defaults |
| `src/eod_config/urls.py` | global static URL inclusion |
| `src/eod_config/health.py` | DB-aware shallow health |
| `src/apps/documents/models.py` | immutable document/version/signature/audit patterns |
| `src/apps/operational_documents/models.py` | structured journal kernel, schemas, snapshots and protected records |
| `src/apps/organizations/models.py` | organization/workplace/authority foundation |
| `Dockerfile`, `compose.preview.yaml` | container and preview topology |
| workflow runs `30989719006/23/27/51/293` | exact-head CI evidence and 716 tests |
| `docs/runbooks/DATABASE_BACKUP_AND_RESTORE.md` | backup/restore process and missing retention decision |
| `docs/runbooks/INCIDENT_AND_ROLLBACK.md` | manual incident/rollback contract |

## 15. Заключение

- **[FACT]** Текущий ЭОД имеет достаточную предметную и инженерную основу, чтобы его рационально индустриализировать; переписывание с нуля не обосновано.
- **[GAP]** Платформа пока не обладает доказанным operational envelope для пилота и не поддерживает требуемую универсальную module activation model.
- **[PROPOSAL]** Следующая работа должна быть не очередным предметным модулем и не абстрактным «рефакторингом всего», а последовательностью ограниченных risk-ranked work items из `INDUSTRIALIZATION_PROGRAM`.
