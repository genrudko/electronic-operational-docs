# NORMATIVE-EVIDENCE — module contract

## MODULE ID
`NORMATIVE-EVIDENCE` — Нормативные режимы и evidence-события.

## НАЗНАЧЕНИЕ
Legal-mode matrix, ПЭП и раздельные evidence events подписи, ознакомления, инструктажа, проверки знаний и подтверждения.

## КРИТИЧЕСКИЕ СЦЕНАРИИ
показать product target отдельно от proven mode · выполнить re-auth · зафиксировать event type и basis revision.

## PRIMARY FACTS / DERIVED VIEWS
Facts: normative revision/trace; evidence event; authentication event; legal mode decision. Views: legal matrix; evidence history; source traceability.

## РОЛИ И ПОЛНОМОЧИЯ
предметный модуль задаёт требуемое право · PERSONNEL-AUTHORITY подтверждает право.

## ДОКУМЕНТЫ И LEGAL MODE
ПЭП не универсально допустима; proven mode = VERIFY без official/local evidence.

## СВЯЗИ
потребляется всеми controlled actions · не заменяет предметный lifecycle.

## SOURCE IDS / BENCHMARK
`SRC-DEC-STAGE2`, `SRC-RESEARCH-SPECIALIZED`, `N-01`, `N-04`, `N-09`. Decisions: `D-02`, `D-14`.

## DEMO / POST-DEMO
`DEMO-BOUNDED`: separate event taxonomy; re-auth/integrity evidence; target/proven separation. Post-demo: qualified signature integration; automatic legal conclusion.

## CURRENT CODE STATUS / CAPABILITIES
`IMPLEMENTED-ACCEPTED`; release `ACCEPTED`. `CAP-NORMATIVE-LEGAL-MODES` (ACCEPTED/IMPLEMENTED-ACCEPTED; NORMATIVE-EVIDENCE-001; AC-NORMATIVE-LEGAL-MODES-001), `CAP-NORMATIVE-EVENTS` (ACCEPTED/IMPLEMENTED-ACCEPTED; NORMATIVE-EVIDENCE-001; AC-NORMATIVE-EVENTS-001), `CAP-NORMATIVE-PEP` (ACCEPTED/IMPLEMENTED-ACCEPTED; NORMATIVE-EVIDENCE-001; AC-NORMATIVE-PEP-001).

Accepted exact PR head: `24848d04984b61b0b183f3ed2b04117b3e05e5f9`. Merge commit: `6e5171776cd6bc02fcbc45eb9532a6a0e58e15f0`.

## DEPENDENCIES / UX CONTRACT
Dependencies: `PLATFORM`. Direction A; 1440×900, 1024×768, 390×844; loading/empty/error/readonly/long-data.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS
VERIFY: consolidated acts; local acts/retention; authority-at-action; УКЭП/УНЭП and external trust services. Forbidden: не приравнивать acknowledgement к инструктажу; не выводить legal mode из immutable model.
