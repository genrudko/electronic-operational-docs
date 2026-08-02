# SHIFT — module contract

## MODULE ID
`SHIFT` — Начало и передача смены.

## НАЗНАЧЕНИЕ
Workflow открытия, сдачи и приёмки смены с report, active states and two-side evidence.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
open shift · build handover report · confirm handover by two persons · store authority evidence.

## PRIMARY FACTS / DERIVED VIEWS
Facts: shift/membership; handover report; two-side evidence; active-state snapshot. Views: shift workspace; handover report; unfinished/active list.

## РОЛИ И ПОЛНОМОЧИЯ
обе стороны проверяются независимо · одно лицо не подменяет обе стороны без exception.

## ДОКУМЕНТЫ И LEGAL MODE
Handover confirmation is a separate evidence event, not universal signature.

## СВЯЗИ
snapshot OPJ/defects/groundings/works · не меняет source facts.

## SOURCE IDS / BENCHMARK
`SRC-DEC-STAGE2`, `SRC-RESEARCH-SPECIALIZED`. Decisions: `D-07`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: shift start; report; active states; two-side confirmation. Post-demo: HR roster integration; offline handover.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-PARTIAL`; release `IN_PROGRESS`. `CAP-SHIFT-START` (IN_PROGRESS/IMPLEMENTED-PARTIAL; SHIFT-HANDOVER-001; AC-SHIFT-START-001), `CAP-SHIFT-HANDOVER` (NOT_STARTED/ABSENT; SHIFT-HANDOVER-001; AC-SHIFT-HANDOVER-001)

## DEPENDENCIES / UX CONTRACT
Dependencies: `OPJ`, `PERSONNEL-AUTHORITY`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: local handover regulation; substitution rules. Forbidden: не считать последнюю запись ОЖ handover; не auto-close active facts.

## ГРАНИЦА С `OPJ-LIFECYCLE-001`

- `SHIFT-HANDOVER-001` не создаёт базовый механизм перевода строки ОЖ из черновика в зарегистрированный чистовик. Этот механизм принадлежит `OPJ-LIFECYCLE-001`.
- Передача смены использует уже зарегистрированные записи ОЖ и отдельно формирует handover report, active-state snapshot и подтверждения сдающей и принимающей сторон.
- Наличие незарегистрированных черновых строк должно быть явно показано при подготовке к сдаче смены и может блокировать её завершение по отдельному правилу, но не превращает handover в массовую скрытую регистрацию.
- Регистрация отдельной записи, закрытие смены и двустороннее подтверждение передачи являются разными предметными действиями с самостоятельными полномочиями и evidence-событиями.
- Последняя зарегистрированная запись ОЖ, автоматическое закрытие смены и подтверждение только одним лицом не заменяют workflow передачи смены.
