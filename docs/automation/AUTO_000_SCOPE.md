# AUTO-000 — scope and review contract

## Статус

```text
work item: AUTO-000
change type: documentation-only
runtime impact: none
implementation authorization for AUTO-001: pending AUTO-000 acceptance
```

## Цель

Зафиксировать безопасный и ограниченный контракт AUTO-001 до появления workflow, VPS gateway, deploy credential или иной исполняемой автоматизации.

## Входит

- automation master plan;
- AUTO-001 functional contract;
- security model;
- acceptance contract;
- implementation roadmap;
- decision register;
- синхронизация canonical state после QUALITY-001.

## Не входит

- application code;
- models or migrations;
- GitHub Actions workflow;
- VPS scripts/system changes;
- SSH keys or secrets;
- database changes;
- automatic merge;
- automatic preview deployment.

## Review questions

1. Достаточен ли AUTO-001 MVP для устранения ручного PR→VPS разрыва?
2. Не расширены ли полномочия GitHub Actions/VPS gateway сверх необходимого?
3. Подтверждён ли запрет automatic merge?
4. Достаточны ли exact-SHA and preview-isolation criteria?
5. Можно ли после AUTO-001 MVP немедленно вернуться к PLAN-001?

## Acceptance

Merge AUTO-000 означает принятие архитектурного контракта и разрешение подготовить отдельный implementation PR AUTO-001. Он не означает, что automation уже работает.
