# AUTO-000 — scope and review contract

## Статус

```text
work item: AUTO-000
change type: documentation-only
runtime impact: none
status: accepted and merged
accepted PR head: 3a4b4770e1fce41405813efa1e931288bf1a26b8
main merge commit: 937d2cd2b187c17fac3088ccfc52079fc4608306
implementation authorization for AUTO-001: granted by AUTO-000 acceptance
AUTO-001 implementation: absent until separate work item
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

AUTO-000 принят пользователем, squash-merged PR #9 и post-merge verified. Это означает принятие архитектурного контракта и разрешение подготовить отдельный implementation PR AUTO-001.

Acceptance AUTO-000 не означает, что automation уже работает. AUTO-001 требует отдельного implementation chat, branch, Draft PR, gap analysis, exact-head CI, VPS acceptance и явного пользовательского merge decision.
