# CHAT 0 — CURRENT HANDOFF

**Проект:** Электронная оперативная документация (ЭОД)  
**Репозиторий:** `genrudko/electronic-operational-docs`  
**Дата handoff:** 27.07.2026  
**Назначение:** продолжение основного интеграционного чата без потери решений, baseline и границ текущей работы.

---

## 1. Роль этого чата

Основной интеграционный чат остаётся местом для:

- архитектурных и процессных решений;
- проверки фактического состояния GitHub;
- baseline и accepted state;
- разрешения начала крупных work item;
- анализа межмодульных и инфраструктурных дефектов;
- окончательного решения о приёмке и merge.

Функциональная реализация выполняется в отдельных implementation chats.  
Один work item и один PR могут продолжаться в нескольких последовательных чатах.

```text
work item = одна ветка + один PR
implementation chat = расходуемая рабочая сессия
```

Завершение чата не означает завершение work item, Repair или пользовательской приёмки.

---

## 2. Непереговорные правила

- GitHub — единственный источник кода и канонической документации.
- VPS — единственный runtime/test-контур.
- Локальный репозиторий пользователя не используется как источник истины.
- Пользователь не редактирует код и не выполняет штатные VPS-команды для функциональных PR.
- Пользователь выполняет предметную, функциональную и визуальную приёмку.
- Preview не используется для разработки и не изменяется до отдельного принятия.
- Automatic merge запрещён.
- Merge выполняется только после отдельной явной команды пользователя.
- End-user UI — русский.
- Внутренние идентификаторы — профессиональный технический English.
- Реальные персональные данные, производственные оперативные данные, секреты и внутренние документы предприятия в Git не помещаются.
- Проект является независимым прототипом и не заявляется системой работодателя или готовым промышленным продуктом.

---

## 3. Фактический `main`

На момент handoff:

```text
main HEAD:
3f7efeb61f4d2f33bb247a6ee7ccca3d60275f5f
```

Последние прямые изменения в `main`:

### 3.1. Публичный README

```text
commit:
87a0cb0abdf27399b1d7db44b85deceb197025a6

message:
DOCS: update public repository notice and project overview
```

README переписан с учётом публичной видимости репозитория:

- public repository не объявляется open source;
- open-source лицензия отсутствует;
- Copyright © 2026 Геннадий Рудько;
- дополнительное использование материалов требует отдельного письменного разрешения;
- проект не является официальной системой предприятия;
- удалены demo-пароли и лишние runtime-реквизиты с главной страницы;
- промышленное, диспетчерское и safety-critical использование не допускается без отдельного официального проекта внедрения.

### 3.2. Telegram workflow notifications

```text
commit:
3f7efeb61f4d2f33bb247a6ee7ccca3d60275f5f

message:
NOTIFY-001: add centralized Telegram workflow notifications
```

Добавлен:

```text
.github/workflows/telegram-workflow-notifications.yml
```

Он слушает `workflow_run: completed` и отправляет Telegram-результат для:

- `AUTO-001A Foundation CI`;
- `AUTO-001B Controller CI`;
- `EOD Development Stack`;
- `EOD Documentation Contract`;
- `EOD Trusted Development Controller`.

`EOD CI` не включён, потому что уже имеет собственное Telegram-уведомление.

Security boundary:

- используются существующие `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`;
- checkout отсутствует;
- PR-код не исполняется;
- права только read;
- controller, SSH, deployment и rollback не изменены.

---

## 4. Правило прямых микро-изменений

Принято ускорение процесса:

```text
небольшие изменения без влияния на продукт/runtime
→ допускаются напрямую в main
```

Типичные примеры:

- README;
- опечатки и ссылки;
- небольшая синхронизация документации;
- безопасные публичные предупреждения;
- узкие изменения без миграций, бизнес-логики и runtime-риска.

Код продукта, модели, миграции, предметная логика, security boundary, controller, deployment и существенные workflows по умолчанию требуют отдельной ветки и PR.

Исключение для узкого изменения workflow возможно только после явного решения пользователя и при доказанно малом риске, как было сделано для централизованного Telegram notifier.

---

## 5. Принятые baseline

### PLAN-001

Финальный accepted PLAN-001 exact head:

```text
62fd62332c63c73acc4c0a66307538cbe20ea2f1
```

Финальный ZIP SHA-256:

```text
8453841a6d6e377cdc4f56a2b98eeff29e2baf25129a4fbf74825bad301f53fc
```

PLAN-001 merged в `main` коммитом:

```text
b75db8bc073e4b02a3254512e9b99d00f3e6e0e2
```

Accepted application baseline, используемый в проектной документации:

```text
937d2cd2b187c17fac3088ccfc52079fc4608306
```

---

## 6. Текущий work item: DEFECT-001

```text
title:
DEFECT-001: Source-bound equipment defect journal

Draft PR:
#16

branch:
feature/defect-001-equipment-defect-journal

state:
OPEN / DRAFT / NOT MERGED

current PR head at handoff:
eb61ae2f262b1c723cbd56c87552a1e58f30413e
```

Текущий head:

```text
DEFECT-001 Repair 3: update Russian UI presentation contract
```

Последнее проверенное изменение заменяет остаток англоязычного пользовательского текста `authenticated user` на русское представление и добавляет отрицательную regression-проверку.

### Текущие exact-head workflows для `eb61ae2f...`

```text
AUTO-001A Foundation CI:      SUCCESS
AUTO-001B Controller CI:      SUCCESS
EOD Development Stack:       SUCCESS
EOD Documentation Contract:  SUCCESS
EOD CI:                       SUCCESS
```

### Текущий acceptance state

```text
implementation: CONTINUES
current repair: REPAIR 3
user acceptance: NOT COMPLETE
current repair acceptance: NOT CONFIRMED
merge authorization: ABSENT
merge: NOT PERFORMED
preview: MUST REMAIN UNTOUCHED
```

Нельзя считать, что `eb61ae2f...` уже развёрнут в development, пока это не подтверждено trusted deployment evidence.  
Нельзя считать Repair 3 принятым до явной пользовательской проверки.

### История важного Repair №2

Repair №2 исправил общий allocator регистрационных номеров:

```text
organization + registration_number = UNIQUE
```

Алгоритм:

1. lock организации через `select_for_update()`;
2. lock sequence типа документа и года;
3. следующий candidate;
4. построение итогового номера;
5. проверка занятости среди всех документов организации;
6. пропуск коллизий;
7. сохранение фактически выданного значения в `last_value`.

DB constraint не ослаблялся.  
Seed-only workaround не применялся.

Exact head Repair №2:

```text
d31d19fdf17058116ce5a91b5317f2f5268fa799
```

Пять exact-head workflow для него были green. После него work item продолжился пользовательской приёмкой и следующими Repairs.

---

## 7. Continuity DEFECT-001

Первый implementation chat DEFECT-001 закончился посреди пользовательской приёмки и до принятия Repair.

Пользователь решил continuity так:

```text
экспорт закончившегося чата в PDF
→ новый implementation chat
→ восстановление обсуждения из PDF
→ обязательная сверка с GitHub
→ продолжение того же PR #16
```

Новый чат не должен:

- создавать новую ветку;
- создавать новый PR;
- считать предыдущий Repair принятым;
- начинать DEFECT-001 заново;
- выполнять merge;
- изменять preview.

PDF служит историей решений и замечаний.  
GitHub служит источником фактического кода, SHA и CI-состояния.

На будущее предпочтительная связка:

```text
полный PDF чата → история и нюансы
короткий handoff → текущее состояние и следующий шаг
GitHub → фактический код и evidence
```

---

## 8. UX/UI decision

DEFECT-001 сейчас использует legacy-интерфейс приложения. Утверждённый UX/UI-план к нему ещё не применён.

Во время текущей приёмки пользователь проверяет:

- предметную корректность;
- жизненный цикл;
- работоспособность действий;
- смысл и состав полей;
- локальные UX-дефекты, мешающие работе;
- обрезания, наложения, недоступные действия;
- непонятный порядок операций;
- ошибки русскоязычного пользовательского контракта.

Не требуется блокировать текущий Repair из-за:

- фирменных цветов;
- логотипа;
- окончательной типографики;
- скруглений, теней и декоративных деталей;
- полной переработки глобальной навигации;
- полного соответствия будущей дизайн-системе.

Принятое направление:

```text
DEFECT-001
→ предметная и функциональная приёмка
→ merge только после отдельного решения
→ отдельный UX/UI design-system этап
→ следующие журналы строятся на общих компонентах
→ финальная брендовая полировка перед демонстрацией
```

В финальном DEFECT-001 отчёте должно быть явно указано:

```text
Предметная и функциональная приёмка выполнена.

Текущий визуальный стиль является legacy-интерфейсом
и не считается принятым целевым UX/UI.

Переход на утверждённую дизайн-систему выполняется
отдельным этапом.
```

---

## 9. Development access

Development доступен только через SSH tunnel:

```text
remote:
127.0.0.1:8766

local browser:
http://127.0.0.1:8766
```

На рабочем ноутбуке создан отдельный отзываемый SSH-ключ, не основной домашний ключ.

Рекомендуемое имя локального ключа:

```text
%USERPROFILE%\.ssh\eod_work_laptop_ed25519
```

Приватный ключ не передаётся в чат и не коммитится.

PowerShell tunnel:

```powershell
ssh -N -T `
  -o ExitOnForwardFailure=yes `
  -o ServerAliveInterval=30 `
  -o ServerAliveCountMax=3 `
  -L 8766:127.0.0.1:8766 `
  -i "$env:USERPROFILE\.ssh\eod_work_laptop_ed25519" `
  eodadmin@5.181.177.72
```

Туннель уже проверен пользователем и работает.

---

## 10. Trusted deployment rules

Штатный deployment:

```text
trusted PR label
→ пять green exact-head workflows
→ trusted request validation from main
→ restricted SSH controller
→ exact PR SHA
→ isolated PostgreSQL checks
→ backup
→ migrations
→ presentation data
→ health
→ confirm или automatic rollback
```

Пользователь не выполняет ручные VPS-команды.

При failed deployment анализируются:

- первая первичная ошибка;
- failing command;
- состояние development;
- rollback;
- `transaction`;
- `pending_run_id`;
- preview untouched.

Метка deployment должна создавать новое `labeled` event. После failed run старую метку снимают и добавляют обратно ровно один раз, но только после готового green exact head.

---

## 11. Отдельные follow-up work items

Не смешивать с текущим DEFECT-001 Repair без необходимости.

### DATA-DEPLOY-001

Убрать риск безусловного presentation seed из `post_migrate`:

```text
migrate
→ explicit presentation seed
→ explicit seed result
→ runtime smoke
```

### CI-OPT-001

Сократить product delivery time без ослабления доказательного final gate:

- быстрые focused checks на промежуточных commit;
- regression + focused module для narrow repair;
- один полный PostgreSQL suite на final exact head;
- короткий runtime smoke при deployment;
- path gates;
- optional nightly full suite.

### UX/UI design-system stage

После функционального принятия DEFECT-001 закрепить:

- общий application shell;
- навигацию;
- таблицы и фильтры;
- карточки;
- формы;
- hierarchy действий;
- статусы;
- уведомления;
- типографику;
- spacing/density;
- CSS tokens.

---

## 12. Предметные инварианты

- Оперативный журнал остаётся специализированным модулем.
- Остальные рабочие журналы используют общее structured-document core и source-bound формы.
- Оператор не конструирует произвольные формы журналов.
- ЩПТ и ШОТ относятся к одной technical equipment family; различие сохраняется как исходное обозначение или вариант исполнения.
- Paper, hybrid и electronic modes не объявляются юридически эквивалентными без нормативного основания.
- УКЭП/УНЭП не заявляются там, где этого не подтверждает реализация и нормативная модель.
- Наличие модели, route, template или test не означает готовность vertical slice.
- Один журнал доводится до automated и user acceptance, затем начинается следующий.

---

## 13. Позиционирование проекта

Проект:

- личная независимая инициатива;
- не поручен работодателем;
- не использует производственные серверы и реальные оперативные данные;
- не является официальной системой предприятия;
- не предназначен для промышленной эксплуатации на текущем этапе.

Официальный pilot возможен только после отдельного решения о:

- правах на код;
- нормативном соответствии;
- информационной безопасности;
- персональных и производственных данных;
- инфраструктуре;
- сопровождении;
- backup/retention;
- эксплуатационной ответственности.

---

## 14. Первый шаг нового интеграционного чата

Использовать следующий starter:

```text
Восстанови контекст основного интеграционного чата строго по приложенному
CHAT_0_CURRENT_HANDOFF.

Сначала через GitHub проверь фактическое состояние:

1. текущий main HEAD;
2. открытые PR;
3. текущий head Draft PR #16;
4. последние commits DEFECT-001;
5. exact-head workflows;
6. trusted deployment evidence, если оно уже появилось.

Не считай SHA, deployment, Repair или пользовательскую приёмку актуальными
только потому, что они указаны в handoff. GitHub и runtime evidence имеют
приоритет.

Текущий DEFECT-001 остаётся в существующей ветке и PR #16.
Пользовательская приёмка не завершена.
Merge не разрешён.
Preview изменять запрещено.

Первый ответ:

FACT
ACTIVE WORK ITEMS
ACCEPTANCE STATE
OPEN DECISIONS
NEXT ACTION
```

---

## 15. Критический текущий вывод

```text
main:
3f7efeb61f4d2f33bb247a6ee7ccca3d60275f5f

active product PR:
#16 / OPEN / DRAFT / NOT MERGED

DEFECT-001 current head:
eb61ae2f262b1c723cbd56c87552a1e58f30413e

five exact-head workflows:
SUCCESS

user acceptance:
NOT COMPLETE

merge authorization:
ABSENT
```

Перед любым новым действием эти факты необходимо повторно проверить через GitHub.
