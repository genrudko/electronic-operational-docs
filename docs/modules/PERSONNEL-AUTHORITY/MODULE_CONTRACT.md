# PERSONNEL-AUTHORITY — module contract

## MODULE ID

`PERSONNEL-AUTHORITY` — персонал и оперативные полномочия.

## НАЗНАЧЕНИЕ

Модуль хранит организационную структуру, штатный персонал, квалификацию,
опубликованные права, условия, область и срок их действия, а также отдельный
контур внешнего персонала и объяснимую проверку полномочия на момент действия.

## КРИТИЧЕСКИЕ СЦЕНАРИИ

- опубликовать утверждённую редакцию списка лиц с предоставлением прав;
- увидеть полный профиль прав сотрудника в структуре подразделений;
- определить всех лиц, которым предоставлено выбранное право;
- учесть квалификацию, область, срок и дополнительное условие;
- проверить полномочие в момент действия и сохранить объяснимый результат;
- отдельно проверить подрядный или командированный персонал;
- учесть только явно ограниченное замещение.

## PRIMARY FACTS / DERIVED VIEWS

Primary facts:

- организация, иерархия подразделений, рабочее место и сотрудник;
- квалификация: категория персонала, группа по электробезопасности, класс
  напряжения и область электроустановок;
- опубликованная редакция списка лиц с предоставлением прав;
- положительная ячейка матрицы `EmployeeOperationalRight` с marker, condition,
  scope, validity, source reference, source hash и source row;
- машинная проекция опубликованной ячейки `OperationalAuthorityGrant` для
  action-time evaluator;
- внешний допуск, ограниченное замещение и результат проверки.

Derived views:

- дерево подразделений и матрица прав штатного персонала;
- представление «кто имеет право»;
- полный профиль сотрудника;
- отдельный реестр внешнего персонала;
- `ALLOW / DENY / VERIFY`, причины и неизменяемый снимок проверки.

## PUBLICATION CONTRACT

Утверждённая редакция матрицы является документом предоставления прав штатному
персоналу. Для действующей редакции:

- `+` означает предоставленное право;
- `+1`, `+2`, `+3` означают предоставленное право с дополнительным условием;
- пустая ячейка или `-` не предоставляет право;
- строка сотрудника, колонка права, marker, qualifier, scope и документ-основание
  образуют структурированный факт предоставления;
- `OperationalAuthorityGrant` не является вторым независимым назначением: он
  материализуется из опубликованной ячейки и ссылается на неё через
  `source_operational_right`;
- условное право участвует в проверке и возвращает `VERIFY`, пока условие нельзя
  подтвердить автоматически.

## РОЛИ И ПОЛНОМОЧИЯ

Application role, должность, категория персонала, квалификация, объектовый
допуск и опубликованное operational right разделены. Должность или роль
приложения сами по себе не дают `ALLOW`. Проверка выполняется server-side по
фактам, действовавшим в момент действия.

## ДОКУМЕНТЫ И LEGAL MODE

Утверждённая редакция списка лиц и документ, которым она введена, являются
основанием публикации прав штатного персонала. Knowledge check, инструктаж,
подтверждение предметного действия и authority evaluation остаются разными
evidence objects. Результат проверки полномочия не заменяет `EvidenceEvent`
предметного действия и не объявляет сам по себе юридическую значимость.

## EXTERNAL PERSONNEL

Подрядный, командированный и иной внешний персонал не включается в штатную
матрицу принимающей организации. Для него отдельно фиксируются home/host
organization, relation kind, scope, validity, basis и собственная
квалификация. Внешний допуск не создаёт право без подходящего operational grant.

## PERSISTENCE / EVIDENCE CONTRACT

- `EmployeeOperationalRight` — опубликованное право штатного сотрудника и
  traceable source fact одновременно.
- `OperationalAuthorityGrant` — нормализованная action/scope-проекция для
  evaluator; для штатной матрицы обязательна ссылка на source right.
- `ExternalPersonnelEngagement` — связь направляющей и принимающей организаций.
- `OperationalAuthoritySubstitution` — только явно перечисленные actions/scope;
  автоматическое копирование всех прав запрещено.
- `AuthorityEvaluationRecord` append-only; исправление создаёт новый связанный
  record.
- Snapshot и SHA-256 используют принятый normative-evidence canonicalization
  contract; secret-like keys запрещены.

## СВЯЗИ

Модуль использует `MASTER-DATA` для организации, сотрудников и объектов и
`NORMATIVE-EVIDENCE` для прослеживаемости оснований и неизменяемых снимков.
Результат будет потребляться controlled actions последующих OPJ, SHIFT,
DEFECT, work-permit и switching модулей, но такие связи в этом work item не
подключаются.

## SOURCE IDS / BENCHMARK

`REF-OD-051`, `REF-OD-052`, `REF-OD-053`, `SRC-DEC-STAGE2`.
Утверждённая пользовательская матрица использована только для восстановления
структуры данных и рабочих сценариев; реальные ФИО, локальный акт и workbook в
Git не помещаются.

## USER EXPERIENCE CONTRACT

Основное представление — не плоский список grants, а иерархическая матрица:

```text
организация
  └─ подразделение
      └─ подчинённое подразделение
          └─ сотрудник × колонки опубликованных прав
```

Обязательны sticky identity columns, grouped rights header, сворачивание дерева,
поиск, фильтры по категории/группе/праву, marker states и переход в карточку
сотрудника. Представление «кто имеет право» использует то же дерево и показывает
область, условие, срок и основание. Технические IDs и snapshot скрыты в audit
section.

## DEMO / POST-DEMO

`DEMO-BOUNDED`: 17 синтетических штатных сотрудников в иерархии, 22 вида прав,
квалификация, более 100 положительных ячеек, linked evaluator projections,
отдельный contractor scenario и результаты `ALLOW / DENY / VERIFY`.

Post-demo: controlled publication реальных редакций, история редакций, diff и
отзыв прав, интеграция HR/AD/СКУД, production catalogs условий и downstream
action requirements.

## DEPENDENCIES / UX CONTRACT

Dependencies: `MASTER-DATA`, `NORMATIVE-EVIDENCE`. Direction A; основной UX —
организационное дерево и матрица, отдельные режимы «Кто имеет право», внешний
персонал, карточка сотрудника и история проверок. Проверяются populated/empty,
plain/conditional markers, hierarchy, long scope/basis, internal/external,
light/dark и responsive states.

## CURRENT CODE STATUS / CAPABILITIES

`IMPLEMENTED-CANDIDATE`; release `IN_PROGRESS`; active work item
`PERSONNEL-AUTHORITY-001`, issue #42, Draft PR #43.

- `CAP-PERSONNEL-REGISTRY`: hierarchy, qualification, matrix and employee
  profile; `AC-PERSONNEL-REGISTRY-001` — candidate.
- `CAP-AUTHORITY-GRANTS`: published cell → linked structured evaluator
  projection; `AC-AUTHORITY-GRANTS-001` — candidate.
- `CAP-AUTHORITY-ACTION-TIME`: explainable `ALLOW / DENY / VERIFY`, append-only
  snapshot, digest and correction link; `AC-AUTHORITY-ACTION-TIME-001` —
  candidate.
- `CAP-AUTHORITY-EXTERNAL`: separate external engagement and bounded
  substitution; `AC-AUTHORITY-EXTERNAL-001` — candidate.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS

VERIFY: production catalog of right columns; exact local meaning of every
conditional marker; history and withdrawal semantics for published revisions;
qualification requirements per controlled action; external-personnel local
acts; downstream action requirements.

Forbidden:

- считать application role или должность operational right;
- создавать второе ручное назначение поверх опубликованной матрицы;
- автоматически переносить все права при замещении;
- смешивать штатную матрицу и внешний персонал;
- объявлять `VERIFY` разрешением;
- подключать OPJ/SHIFT/DEFECT/work-permit/switching lifecycles в этом PR;
- писать в preview или выполнять merge без команды пользователя.
