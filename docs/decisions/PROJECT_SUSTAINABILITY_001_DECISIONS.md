# PROJECT-SUSTAINABILITY-001 — решения и предложения

**Дата:** 05.08.2026
**Work item:** `PROJECT-SUSTAINABILITY-001`
**Issue / PR:** `#48 / #49`
**Статус документа:** `DECISION RECORD CANDIDATE / USER ACCEPTANCE REQUIRED`

## 1. Правило чтения

- **[DECISION]** — ранее принятое решение владельца продукта или решение, уже закреплённое canonical documentation.
- **[PROPOSAL]** — вывод аудита, который становится обязательным только после пользовательской приёмки PR #49.
- **[FACT]** — проверенное состояние кода, конфигурации, GitHub или документации.
- **[GAP]** — доказанное отсутствие/расхождение.
- **[VERIFY]** — отдельная проверка обязательна; молчаливое предположение запрещено.
- **[WISHLIST]** — не влияет на ближайшие gates.

## 2. Сохраняемые архитектурные решения

### PSD-001 — modular Django monolith

- **[DECISION]** ЭОД остаётся modular Django monolith.
- **[DECISION]** Микросервисы запрещено вводить без отдельного доказательства, что требование невозможно безопасно закрыть внутри модульного монолита.
- **[FACT]** Текущий code layout уже разделён на 11 собственных Django apps и имеет общие core/domain primitives.
- **[PROPOSAL]** Индустриализация должна усиливать границы apps и control plane, а не менять deployable architecture.

### PSD-002 — один продукт, разные наборы модулей

- **[DECISION]** Все журналы и функциональные контуры поставляются как модули одного продукта, а не как отдельные версии/форки.
- **[DECISION]** Поэтапная активация выполняется по organization, energy site и/или workplace.
- **[DECISION]** Отключение модуля не удаляет исторические сведения.
- **[PROPOSAL]** Все Django apps остаются installed статически; доступность capability регулируется module registry/control plane, а не динамическим изменением `INSTALLED_APPS`.

### PSD-003 — lifecycle модулей

- **[PROPOSAL]** Единый lifecycle: `AVAILABLE`, `CONFIGURED`, `ACTIVE`, `READ_ONLY`, `RETIRED`.
- **[PROPOSAL]** `ACTIVE` разрешает новые действия; `READ_ONLY` и `RETIRED` запрещают новые предметные факты, но сохраняют history/read access по полномочиям.
- **[PROPOSAL]** Scope precedence и правила конфликтов должны быть приняты в `MODULE-ACTIVATION-CONTRACT-001` до создания models/migrations.

### PSD-004 — migrations и inactive modules

- **[PROPOSAL]** Миграции применяются ко всему единому продукту независимо от activation state.
- **[PROPOSAL]** Inactive modules обязаны безопасно migrate, сохранять data и re-activate после upgrade.
- **[PROPOSAL]** Отдельная версия приложения на каждый набор модулей запрещается.

## 3. UX-решения

### PSD-005 — единая UX-платформа

- **[DECISION]** Direction A остаётся общесистемным visual/interaction language.
- **[DECISION]** Shared components, design tokens and page templates обязательны; новая visual system для отдельного журнала запрещена.
- **[FACT]** DEFECT и OPJ уже являются принятыми reference implementations разных page profiles.
- **[PROPOSAL]** Четыре стандартных профиля: `REGISTRY_PAGE`, `STANDARD_JOURNAL`, `SPECIALIST_WORKSPACE`, `PROCESS_TIMELINE`.

### PSD-006 — миграция без big-bang rewrite

- **[DECISION]** Legacy/Direction A migration выполняется постепенно.
- **[PROPOSAL]** Единица миграции — реальный route/user scenario с inventory template/static assets, browser evidence и доказанным удалением obsolete layer.
- **[PROPOSAL]** Нельзя закрывать visual debt новым override layer без owner, срока удаления и regression test.

### PSD-007 — browser and visual evidence

- **[PROPOSAL]** Critical routes получают blocking browser gates для Edge-compatible Chromium и Chrome, themes, accepted viewports, keyboard and print.
- **[PROPOSAL]** Screenshot baseline используется как controlled evidence, но не заменяет behavioral assertions.

## 4. Данные и зарегистрированные факты

### PSD-008 — неизменяемость

- **[DECISION]** Зарегистрированные факты не переписываются и не удаляются; исправление/отмена создают новый связанный факт.
- **[FACT]** Application layer уже реализует protected managers, `PROTECT`, snapshots, checksums and audit events.
- **[PROPOSAL]** Для пилота добавить least-privilege DB role, controlled maintenance and periodic integrity reports; blockchain/WORM не вводить без отдельного требования.

### PSD-009 — backup не равен recovery

- **[PROPOSAL]** Наличие dump не считается достаточным; valid recovery point существует только после успешного restore verification.
- **[PROPOSAL]** RPO, RTO, retention, off-host copy, encryption and restore schedule должны быть приняты до pilot.
- **[PROPOSAL]** Restore certificate является обязательным release/pilot evidence.

### PSD-010 — migration compatibility

- **[PROPOSAL]** Clean-database CI сохраняется, но дополняется upgrade tests representative accepted databases.
- **[PROPOSAL]** Destructive schema changes используют expand/migrate/contract and explicit rollback decision.

### PSD-011 — export and portability

- **[PROPOSAL]** До pilot определить schema-versioned export package, включающий records, snapshots, signatures/confirmations, authority snapshots, audit, source IDs and attachments.
- **[PROPOSAL]** Export считается готовым только после round-trip verification.

## 5. Deployment и эксплуатация

### PSD-012 — Preview не является production profile

- **[FACT]** Текущие deployment modes: `development`, `ci`, `preview`.
- **[DECISION]** Preview остаётся acceptance/demo contour и не переименовывается в production.
- **[PROPOSAL]** Создать отдельный fail-closed pilot/production mode и deployment contract.

### PSD-013 — первый pilot single-node

- **[PROPOSAL]** Для первого пилота целевой topology — сопровождаемый single-node deployment с PostgreSQL, reverse proxy/TLS, off-host backup and observability.
- **[PROPOSAL]** HA, replication, Kubernetes and microservices не являются prerequisite первого пилота.

### PSD-014 — immutable release

- **[PROPOSAL]** Accepted release определяется commit SHA + image digest + locked dependency manifest + DB compatibility + evidence bundle.
- **[PROPOSAL]** Пересборка диапазонов dependencies во время rollback запрещается как основной recovery method.

### PSD-015 — observability and incident response

- **[PROPOSAL]** Structured logs, request correlation, readiness/liveness, metrics, alerts and backup freshness входят в pilot prerequisite.
- **[PROPOSAL]** Incident runbook дополняется severity, roles, escalation, notification and postmortem SLA.

## 6. Security

### PSD-016 — secret hygiene

- **[FACT]** CI evidence раскрывает постоянные demo credentials.
- **[PROPOSAL]** Credentials должны быть удалены из output/history where practical, rotated and replaced generated/ephemeral or masked mechanism.
- **[PROPOSAL]** Secret scan становится required check.

### PSD-017 — production security profile

- **[PROPOSAL]** Pilot/production mode обязан fail closed при DEBUG, default secret/password, missing TLS/proxy/cookie controls, SQLite or unsafe host configuration.
- **[PROPOSAL]** `manage.py check --deploy` и external TLS/session smoke входят в release gate.

### PSD-018 — identity assurance

- **[DECISION]** Предметные authority и snapshot at action time сохраняются.
- **[PROPOSAL]** До pilot определить privileged assurance: re-auth, MFA target, rate limiting, lockout, periodic access review and break-glass.
- **[VERIFY]** Конкретный MFA mechanism выбирается отдельным work item с учётом эксплуатационной среды.

### PSD-019 — uploads

- **[PROPOSAL]** Все uploads/imports подчиняются centralized policy: size, MIME, extension, naming, quarantine/AV, isolated storage, authorization and retention.
- **[VERIFY]** Полный attack-surface inventory обязателен до выбора реализации.

## 7. Source governance

### PSD-020 — GitHub и Drive

- **[DECISION]** GitHub — единственный canonical source кода, contracts, decisions and metadata.
- **[DECISION]** Google Drive — library of originals/materials, но не владелец продуктовых решений.
- **[PROPOSAL]** Drive item связывается stable source ID, locator, owner, version, checksum, freshness and publication status.

### PSD-021 — module source requirements

- **[PROPOSAL]** Каждый module/capability имеет machine-readable список mandatory source IDs and local instructions.
- **[PROPOSAL]** Missing/stale mandatory source блокирует начало work item.
- **[PROPOSAL]** Normative evidence, enterprise practice, competitor evidence and user decision хранятся раздельно.

## 8. Sequencing decisions

### PSD-022 — два gate вместо бесконечной паузы

- **[PROPOSAL]** `SAFE-CONTINUATION` закрывает минимальные prerequisites до массовой предметной разработки.
- **[PROPOSAL]** `PILOT-READY` закрывает полный operational/security/support baseline до реального пилота.
- **[PROPOSAL]** Это предотвращает две крайности: unsafe feature rush и многомесячный big-bang platform rewrite.

### PSD-023 — предметная очередь

- **[DECISION]** `SHIFT-HANDOVER-001` не начинается внутри `PROJECT-SUSTAINABILITY-001`.
- **[PROPOSAL]** После принятия программы сначала закрываются Phase 0 and SAFE-CONTINUATION work items; затем владелец отдельным решением разрешает продолжение предметной очереди.
- **[PROPOSAL]** Новый module после SAFE-CONTINUATION обязан использовать activation contract, source requirements and UX page profile.

### PSD-024 — reference modules

- **[DECISION]** DEFECT и OPJ являются первыми эталонными types/modules.
- **[PROPOSAL]** Они используются для extraction shared contracts; их переписывание с нуля запрещается.

## 9. Future modules

### PSD-025 — NOTES

- **[DECISION]** Личные и общие заметки входят в target architecture как optional module.
- **[PROPOSAL]** Earliest dependencies: module registry, data governance and page-template library.
- **[PROPOSAL]** Note не является зарегистрированным operational fact; conversion to document/record требует явного action and audit.

### PSD-026 — MAIL-INTEGRATION

- **[WISHLIST]** Local Exchange integration остаётся последней очередью.
- **[DECISION]** Не входит в SAFE-CONTINUATION, PILOT-READY и первый pilot.
- **[PROPOSAL]** Начинается только при наличии подтверждённого enterprise integration contract and security approval.

## 10. Pilot acceptance

### PSD-027 — pilot declaration

- **[PROPOSAL]** Green CI, working Preview или successful demo не равны pilot readiness.
- **[PROPOSAL]** `PILOT-READINESS-001` должен независимо проверить module control, identity/security, data/recovery, operations, UX/browser, performance and support handover.
- **[DECISION]** Финальное разрешение pilot даёт владелец продукта отдельным явным решением; limitations публикуются без приукрашивания.

## 11. Решения, требующие явной приёмки владельца

При принятии PR #49 владелец подтверждает либо корректирует:

1. **[PROPOSAL]** two-gate model `SAFE-CONTINUATION / PILOT-READY`;
2. **[PROPOSAL]** Phase 0–7 sequence и risk priorities;
3. **[PROPOSAL]** static installed apps + scoped control plane вместо dynamic app loading;
4. **[PROPOSAL]** single-node first pilot target;
5. **[PROPOSAL]** mandatory restore certificate and immutable release manifest;
6. **[PROPOSAL]** mandatory security/observability/browser/support gates;
7. **[PROPOSAL]** resumption rule for `SHIFT-HANDOVER-001` after SAFE-CONTINUATION decision.

До такой приёмки все перечисленные пункты остаются proposal, а PR #49 — Draft / NOT MERGED.
