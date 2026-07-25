# ЭОД — программа автоматизации разработки

## 1. Цель

Автоматизировать механическую часть существующего GitHub-first/VPS-first цикла без перехода в Codex и без передачи ИИ неконтролируемого доступа к VPS.

Целевой пользовательский цикл:

```text
поставить задачу
→ получить готовый development и evidence
→ проверить продукт
→ принять, отправить на repair или изменить направление
→ явно разрешить merge
```

## 2. Текущий ручной разрыв

Сейчас после зелёного CI необходимо вручную:

```text
обновить /srv/eod/development
→ переключить branch
→ выполнить refresh/rebuild
→ выполнить check/test/status
→ передать лог в чат
```

AUTO-001 устраняет именно этот разрыв. Полная автоматизация всех дальнейших операций не является предварительным условием продолжения продуктовой разработки.

## 3. Принципы

### P-01 — GitHub source of truth

Исходники, история, branches, commits, PR и merge существуют только в GitHub.

### P-02 — Exact SHA

Deployment, проверки и evidence относятся к одному точному commit SHA:

```text
PR head SHA
= requested SHA
= VPS checkout HEAD
= tested SHA
= reported SHA
```

### P-03 — Разделение контуров

| Контур | Checkout | Branch | Compose | Database | Port |
|---|---|---|---|---|---:|
| preview | `/srv/eod/repository` | `main` only | `eod-preview` | `eod_preview` | `127.0.0.1:8765` |
| development | `/srv/eod/development` | non-main | `eod-development` | `eod_development` | `127.0.0.1:8766` |

### P-04 — Минимальные полномочия

GitHub Actions не получает:

- интерактивный root shell;
- общий Docker socket;
- preview credentials;
- права записи в repository contents;
- право merge.

### P-05 — Fail closed

Automation останавливается при:

- несовпадении SHA;
- dirty development worktree;
- попытке запуска `main` в development;
- неизвестном repository/PR/profile;
- нездоровой development database;
- нарушении preview isolation;
- невозможности однозначно определить результат.

### P-06 — Человек остаётся контрольным воротом

Техническая готовность не равна предметной или визуальной приёмке. Merge возможен только после явной команды пользователя.

## 4. Последовательность этапов

### AUTO-000 — Documentation contract

- master plan;
- functional contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- синхронизация canonical state после QUALITY-001.

### AUTO-001 — Minimal development orchestrator

Минимум:

```text
trusted PR trigger
→ green required checks
→ exact-SHA deployment
→ explicit refresh/rebuild profile
→ check
→ test apps
→ status
→ structured result in GitHub
```

AUTO-001 считается достаточным для возврата к PLAN-001 после двух успешных и одного отрицательного acceptance case.

### AUTO-002 — Change classifier

Автоматический выбор `refresh`/`rebuild`, migrations и test profile после накопления реальных случаев.

### AUTO-003 — Unified evidence

JUnit/JSON, группировка ошибок и единый PR report.

### AUTO-004 — Browser acceptance

Playwright smoke, screenshots, video и trace перед первым крупным UI vertical slice.

### AUTO-005+ — По фактической необходимости

- visual regression после принятия design tokens;
- автоматизированный development DB reset;
- trusted preview deployment после стабилизации development orchestrator;
- расширенная PR state machine.

## 5. Что остаётся ручным

- первая установка restricted VPS gateway;
- создание/ротация deploy credential;
- предметная и визуальная приёмка;
- решение при неоднозначной миграции или восстановлении;
- merge authorization;
- действия при security incident.

## 6. Метрики

- ручные VPS-команды пользователя на PR;
- ручные копирования логов;
- время от green CI до VPS evidence;
- случаи SHA mismatch;
- случаи нарушения preview isolation;
- доля PR, готовых к пользовательской проверке без технического участия пользователя.

## 7. Ограничение спринта

Основная продуктовая разработка приостанавливается только до принятого AUTO-001 MVP. AUTO-002 и последующие этапы не блокируют PLAN-001 и продуктовые vertical slices.
