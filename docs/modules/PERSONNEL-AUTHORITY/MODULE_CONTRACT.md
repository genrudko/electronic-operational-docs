# PERSONNEL-AUTHORITY — module contract

## MODULE ID

`PERSONNEL-AUTHORITY` — персонал и оперативные полномочия.

## НАЗНАЧЕНИЕ

Модуль хранит организационную структуру, штатный персонал, квалификацию,
опубликованные права, условия, область и срок их действия, а также отдельный
контур внешнего персонала и объяснимую проверку полномочия на момент действия.

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

## DEMO / PRESENTATION DATA

Conditional reversible migration выполняется только при наличии
`Organization(code="DEMO")`; на иных БД — no-op. Создаются исключительно
синтетические данные:

- 17 штатных сотрудников в иерархии подразделений;
- 22 вида прав по структуре утверждённой матрицы;
- квалификация каждого сотрудника;
- более 100 положительных ячеек, включая `+1`, `+2`, `+3`;
- linked evaluator projections;
- отдельный contractor scenario;
- `ALLOW`, `DENY`, `VERIFY` и external `ALLOW`.

Реальные ФИО, локальные акты и production workbook в Git не помещаются.

## DEPENDENCIES / BOUNDARY

Dependencies: `MASTER-DATA`, `NORMATIVE-EVIDENCE`.

Forbidden in this work item:

- подключать OPJ/SHIFT/DEFECT/work-permit/switching lifecycles;
- считать application role или должность operational right;
- создавать второе ручное назначение поверх опубликованной матрицы;
- автоматически переносить все права при замещении;
- смешивать штатную матрицу и внешний персонал;
- объявлять `VERIFY` разрешением;
- писать в preview или выполнять merge без команды пользователя.

## CURRENT CODE STATUS / CAPABILITIES

`IMPLEMENTED-CANDIDATE`; release `IN_PROGRESS`; active work item
`PERSONNEL-AUTHORITY-001`, issue #42, Draft PR #43.

- `CAP-PERSONNEL-REGISTRY`: hierarchy, qualification, matrix and employee profile.
- `CAP-AUTHORITY-GRANTS`: published cell → linked structured evaluator projection.
- `CAP-AUTHORITY-ACTION-TIME`: explainable `ALLOW / DENY / VERIFY`, append-only
  snapshot, digest and correction link.
- `CAP-AUTHORITY-EXTERNAL`: separate external engagement and bounded substitution.
