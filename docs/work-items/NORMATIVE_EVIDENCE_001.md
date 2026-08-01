# NORMATIVE-EVIDENCE-001 — execution package

**Issue:** #40  
**Branch:** `feature/normative-evidence-001`  
**Starting main tip:** `c05ace785f054233aa878ddead491def47525140`  
**Accepted application baseline:** `b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb`

## WORK ITEM ID

`NORMATIVE-EVIDENCE-001`

## PARENT RELEASE

`DEMO-RELEASE BASELINE V1.0`

## PARENT MODULE

`NORMATIVE-EVIDENCE` — нормативные режимы и evidence-события.

## CAPABILITY IDS

- `CAP-NORMATIVE-LEGAL-MODES`;
- `CAP-NORMATIVE-EVENTS`;
- `CAP-NORMATIVE-PEP`.

## EXACT BASELINE SHA

```text
current main tip: c05ace785f054233aa878ddead491def47525140
accepted application baseline: b644048f1ec17e19e03c2e4fb538fc0cfc1f5feb
```

Ветка создана непосредственно от current main tip. Поздние documentation-only commits не объявляются новым accepted application baseline.

## GOAL

Создать единый bounded-контур, который:

1. раздельно хранит product target и доказанный legal mode;
2. различает подпись, ознакомление, инструктаж, проверку знаний и подтверждение действия;
3. связывает evidence event с конкретным subject, actor, серверным временем, способом подтверждения, digest и нормативным основанием;
4. переиспользует существующие immutable snapshot/signature/re-auth/integrity primitives;
5. не выдаёт техническую неизменяемость или повторную аутентификацию за автоматически доказанную юридическую значимость.

## USER SCENARIO

Пользователь выполняет контролируемое действие в предметном модуле. Система показывает, какое именно подтверждение создаётся, при необходимости требует повторно подтвердить текущую учётную запись, фиксирует отдельное append-only evidence event и позволяет позднее доказуемо увидеть:

- кто совершил действие;
- что именно подтверждено;
- когда это произошло;
- каким способом подтверждена учётная запись;
- какой immutable payload зафиксирован;
- на какую нормативную редакцию/source trace опиралось решение;
- является режим лишь product target либо имеет доказанный статус.

## BUSINESS RESULT

Последующие `PERSONNEL-AUTHORITY`, OPJ, SHIFT, WORK-PERMIT и иные controlled workflows получают один общий evidence contract вместо несовместимых локальных флагов и текстовых отметок.

## FACTUAL START

- `apps.normatives` содержит `NormativeDocument`, immutable published `NormativeRevision`, `NormativeRequirement` и `RequirementTrace`.
- `apps.documents` содержит immutable `SignedSnapshot`, `DocumentSignature`, canonical JSON, SHA-256, password re-authentication и integrity verification.
- `apps.organizations` содержит identity, login/logout `AuthenticationEvent`, роли и частичные operational-right foundations.
- Единой persisted taxonomy evidence events нет.
- Legal-mode matrix уже различает product target и proven mode; доказанные режимы сохраняют `VERIFY`, пока нормативное и локальное основание не подтверждено.

## IN SCOPE

1. Machine-readable legal-mode contract:
   - product target;
   - normative evidence status;
   - local-act status;
   - proven legal mode;
   - basis revision/source IDs;
   - запрет недоказанного повышения `VERIFY`.
2. Evidence-event taxonomy:
   - `SIGNATURE`;
   - `ACKNOWLEDGEMENT`;
   - `INSTRUCTION`;
   - `KNOWLEDGE_CHECK`;
   - `ACTION_CONFIRMATION`.
3. Canonical payload и digest без secrets.
4. Явная re-auth requirement и confirmation method.
5. Append-only persistence/services после принятия pure contract slice.
6. Focused tests semantic separation, validation, integrity и secret handling.
7. Read-only bounded views после стабилизации model/service contract.
8. Traceability к `NormativeRevision` и source IDs.

## FIRST IMPLEMENTATION SLICE

Pure domain contract, без schema/data migration:

```text
src/apps/normatives/evidence.py
src/apps/normatives/tests/test_evidence_contract.py
```

Цель slice — зафиксировать enums, validation и canonical digest до создания persistent models. Это предотвращает преждевременное закрепление ошибочной юридической семантики в миграции.

## OUT OF SCOPE

- юридическое заключение по конкретному документу или организации;
- автоматическое определение применимости права;
- УКЭП/УНЭП, сертификаты, внешний ключ, timestamp authority;
- полноценный authority-at-action evaluator;
- предметные lifecycle ОЖ, смены, наряда, распоряжения и иных журналов;
- production retention/security/HA;
- изменение accepted preview.

## DEPENDENCIES

- `PLATFORM` — identity, audit, transactional services;
- существующие `NORMATIVES`, `DOCUMENTS`, `ORGANIZATIONS` foundations;
- `PERSONNEL-AUTHORITY-001` является downstream consumer, а не частью этой задачи.

## DOMAIN CONTRACT

1. `product_target_mode != proven_legal_mode` по смыслу и хранению.
2. Значение `VERIFY` является честным состоянием, а не ошибкой, которую нужно скрыть.
3. Non-`VERIFY` proven mode требует traceable basis, достаточный normative evidence status и закрытый local-act status.
4. Evidence event types не взаимозаменяемы.
5. `ACKNOWLEDGEMENT` не доказывает `INSTRUCTION` или `KNOWLEDGE_CHECK`.
6. `SIGNATURE` не доказывает предметное право actor; это задача authority evaluator.
7. Password re-authentication не сохраняет пароль и не объявляется квалифицированной либо неквалифицированной электронной подписью.
8. Canonical payload фиксирует только проверяемые факты и snapshots.
9. Исторические события append-only; correction создаёт новое связанное событие.
10. Доменный модуль определяет required evidence type; нормативный модуль не заменяет его lifecycle.

## LEGAL MODE / VERIFY OWNER

- Владелец product boundary: canonical decision/release plan.
- Владелец нормативного доказательства: traceable official consolidated source.
- Владелец local-act applicability: отдельный подтверждённый локальный документ организации.
- До закрытия обоих evidence layers: `proven_legal_mode = VERIFY`.
- Код не создаёт юридическое заключение автоматически.

## SOURCE IDS

```text
SRC-DEC-STAGE2
SRC-RESEARCH-SPECIALIZED
N-01
N-04
N-09
SRC-AUDIT-STAGE1
```

Дополнительные изменения актов учитываются только через проверенную консолидированную редакцию и отдельную source trace.

## COMPETITOR BENCHMARK

Применимые принятые решения:

- `D-02` — полностью электронная подпись всех участников остаётся `VERIFY`;
- `D-14` — acknowledgement нельзя приравнивать к инструктажу, проверке знаний или подписи.

Vendor claims не повышают legal mode и не становятся requirement автоматически.

## UX REFERENCES / LOCATORS

- Direction A shared shell и primitives;
- common status chips/readonly details/dialog/re-auth patterns;
- технические детали скрыты по умолчанию, но traceability доступна в evidence details;
- пользователь должен видеть точное действие: «Ознакомиться», «Пройти инструктаж», «Подтвердить действие», а не универсальную кнопку «Подписать всё».

## VIEWPORTS / STATES

```text
1440×900
1024×768
390×844
```

Состояния: loading, empty, error, readonly, long Russian data, `VERIFY`, confirmed target/proven mismatch, invalid credentials, integrity failure.

UI не входит в первый pure contract slice.

## ALLOWED FILES

```text
docs/work-items/NORMATIVE_EVIDENCE_001.md
src/apps/normatives/evidence.py
src/apps/normatives/models.py
src/apps/normatives/services.py
src/apps/normatives/admin.py
src/apps/normatives/migrations/00*.py
src/apps/normatives/tests/**
src/apps/documents/models.py
src/apps/documents/services.py
src/apps/documents/admin.py
src/apps/documents/migrations/00*.py
src/apps/documents/tests/**
src/apps/organizations/models.py
src/apps/organizations/migrations/00*.py
src/apps/organizations/tests/**
applicable canonical documentation and focused gates
```

Изменения `organizations` разрешены только при доказанной необходимости расширить audit повторной аутентификации; предпочтительно переиспользовать текущие primitives без расширения boundary.

## PROTECTED FILES

- OPJ/SHIFT/DEFECT lifecycle, templates и static;
- imports/master-data implementation;
- equipment/dispatching foundations;
- historical migrations;
- preview/deployment configuration;
- реальные enterprise/local-act/source files;
- accepted print geometry;
- release scope и shared UX contract без отдельного decision.

## FORBIDDEN CHANGES

- automatic legal conclusion;
- generic «подпись» вместо различимых evidence events;
- сохранение password/secret/token в model, payload, audit или log;
- parallel hash/signature/authentication framework;
- mutable historical evidence;
- retroactive reconstruction of authority or legal status;
- automatic publication;
- preview write;
- Ready for Review, auto-merge или merge без явной команды пользователя.

## DATA / FIXTURES

Только безопасные вымышленные fixtures. Реальные персональные данные, локальные акты, внутренние журналы и enterprise source files в Git не добавляются.

## ACCEPTANCE IDS

- `AC-NORMATIVE-LEGAL-MODES-001`;
- `AC-NORMATIVE-EVENTS-001`;
- `AC-NORMATIVE-PEP-001`.

## ACCEPTANCE CRITERIA

1. Target/proven/evidence/local-act states существуют раздельно.
2. Non-`VERIFY` proven mode без достаточного basis отклоняется.
3. Все пять event types имеют самостоятельные semantics и required evidence fields.
4. Canonical digest детерминирован.
5. Secret-like payload fields отклоняются рекурсивно.
6. Re-auth-required event не создаётся без соответствующего confirmation method.
7. Persistent records append-only и traceable к subject/actor/basis.
8. Existing document integrity/signature tests остаются зелёными.
9. PostgreSQL migration/test profile и full final gate проходят на одном exact head.
10. Accepted preview остаётся `UNTOUCHED`.
11. Пользователь принимает critical workflow отдельно до Ready/Merge.

## REQUIRED CHECKS

### First slice

- Ruff для новых файлов;
- Python compile;
- focused `apps.normatives.tests.test_evidence_contract`;
- Django system check;
- migration consistency check подтверждает отсутствие случайной schema change.

### Persistence slice

- migration consistency;
- PostgreSQL migration chain;
- focused normatives/documents tests;
- existing registration/integrity regressions;
- full Django suite на final candidate;
- стандартные exact-head workflows один раз перед merge.

## DELIVERY PROFILE

```text
first slice: no runtime delivery required
persistence/UI candidate: FULL_DEVELOPMENT
preview: UNTOUCHED
```

## COMMIT / PR RULES

- одна branch и один Draft PR на весь repair cycle;
- ordinary commits, без rebase/squash/force-push;
- PR body или machine-owned comment хранит exact head и текущее состояние;
- full suite не запускается после каждого малого repair;
- automatic merge запрещён;
- merge только после явной команды пользователя.

## REPORT FORMAT

```text
BASE
BRANCH
ISSUE
PR
EXACT HEAD
FACTUAL GAP
IMPLEMENTED SLICE
CHANGED FILE BOUNDARY
MIGRATIONS
FOCUSED CHECKS
FULL GATE
RUNTIME
PREVIEW
OPEN VERIFY
BLOCKER
NEXT ACTION
ACCEPTANCE STATE
```

## STOP CONDITIONS

- источник не позволяет повысить `VERIFY`;
- local-act applicability отсутствует или не подтверждена;
- implementation смешивает разные evidence semantics;
- требуется authority-at-action behavior за пределами этого work item;
- существующие signature/integrity primitives пришлось бы дублировать;
- changed-file boundary пересекает защищённый предметный модуль без отдельного решения;
- CI/runtime выявляет потерю append-only или secret leakage.

## PREFLIGHT VERDICT

```text
READY TO IMPLEMENT
FIRST SLICE: DOMAIN CONTRACT + FOCUSED TESTS
RUNTIME IMPACT: NONE UNTIL PERSISTENCE
PREVIEW: UNTOUCHED
MERGE: FORBIDDEN WITHOUT EXPLICIT USER COMMAND
```
