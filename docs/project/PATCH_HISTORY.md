# ЭОД — история технических этапов

Этот документ хранит значимые этапы и итог неуспешных repair-циклов. Полные старые журналы отдельных попыток доступны в Git history удаляемого каталога `docs/project_state/` и в локальных patch logs вне репозитория.

## Foundation

| Этап | Результат |
|---|---|
| Patch 001 | Django bootstrap |
| Patch 001.5 | локальный Git и private GitHub |
| Patch 002 | организация, персонал и аутентификация |
| Patch 003 | документарное ядро |
| Patch 003.1 | UTF-8 и постоянный локальный порт |
| Patch 004 | re-auth, canonical snapshot, integrity confirmation |
| Patch 005 | нормативный реестр и организационные редакции |
| Patch 006 | оборудование, aliases, dispatch names and snapshots |
| Patch 006.1 | масштабируемый equipment selector |
| Patch 006.2 | защита private repository и очищенная история |
| Patch 007 | управление и ведение |
| Patch 007.2–007.4 | presentation UI, темы, terminology, organization profile |

## Import and operational foundation

| Этап | Результат |
|---|---|
| Patch 008 | foundation импортов и publication flow |
| Patch 009 | workplace documentation registry |
| Patch 010 | operational log and shift foundation |
| Patch 011 | operational communication foundation/related work |
| Patch 011.5 | equipment and dispatching object importer |
| Patch 011.6 | personnel, rights and workplace documentation importers |
| Patch 011.7 | operational documentation core |

## Patch 011.7 repair cycle

Первая реализация общего ядра прошла серию контролируемых отказов и rollback. Выявлялись и устранялись:

- Ruff violations;
- payload newline contract;
- logging after preflight;
- неправильное использование отсутствующего `Workplace.public_id`;
- ложная изменённость пустых formset rows;
- некорректный synthetic search expectation;
- Unicode casefold issue в SQLite;
- cache-busting revision mismatch;
- устаревший homepage smoke contract;
- недостаточная диагностика parallel test runner.

Каждая неуспешная попытка завершалась без commit и с восстановлением runtime databases/worktree.

### Patch 011.7 Repair 1 Revision 10

- technical success;
- commit `fec8bd675f9565b0c4e398124cd22f8fabec02b4`;
- test discovery 495, один skipped;
- general core accepted technically.

### Patch 011.7 Repair 2

Визуальная проверка выявила неверную product boundary: пользовательский конструктор форм создавал несоответствующую предметную модель.

Repair 2:

- отключил ручное создание произвольных форм;
- ввёл source-bound catalog;
- заблокировал рабочие действия для technical schemas;
- упростил пользовательский UI;
- привязал каталог к `И-00-007-ОР-2025 версия 2`, разделам 7–11 и приложениям 4–8;
- был технически и визуально принят.

Принятый commit до инфраструктурной серии: `bf986433ea33bf932f98925e7daf61b0199e23d0`; tag `eod-baseline-011.7-repair2`.

## INFRA-001 — CI baseline

- branch `infra/001-ci-baseline`;
- GitHub Actions on Ubuntu 24.04, Python 3.13, PostgreSQL 18.4;
- lint, compile, checks, migration verification, migrations, current gate, collectstatic and full tests;
- VPS не используется как self-hosted runner.

## INFRA-002 — container preview

- safe preview Compose;
- application only on `127.0.0.1:8765`;
- PostgreSQL host port unpublished;
- presentation profile migrated to `eod_preview`;
- demo authentication verified;
- merge commit `ded4571dcacd973184d3121b19c8db8c70e7b08a`;
- tag `eod-baseline-infra-002`.

## INFRA-003 — isolated VPS development

- branch `infra/003-isolated-vps-development`;
- isolated checkout, Compose project, database/user, volume, networks and secrets;
- application on `127.0.0.1:8766`;
- safe reset from preview dump into development only;
- CI, VPS isolation, demo authentication and browser tunnel accepted;
- merge commit `abd6066885b060e3e3d2c39098fcaf640bb70416`.

## DOCS-001 — project operating system

Цель текущей ветки:

- заменить patch-centric документацию;
- сделать GitHub главным источником истины;
- создать canonical documentation tree;
- закрепить AI-driven development с пользовательской приёмкой;
- добавить documentation CI contract;
- подготовить PLAN-001.

## Правило истории

- успешный merge фиксируется в `BASELINE_HISTORY.md`;
- предметная/визуальная приёмка — в `ACCEPTANCE_HISTORY.md`;
- архитектурное решение — в `DECISION_LOG.md`;
- подробные неуспешные логи не копируются в Markdown целиком, но их итог и rollback фиксируются здесь.