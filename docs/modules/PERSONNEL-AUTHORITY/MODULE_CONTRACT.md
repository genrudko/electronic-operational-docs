# PERSONNEL-AUTHORITY — module contract

## MODULE ID

`PERSONNEL-AUTHORITY` — персонал и оперативные полномочия.

## НАЗНАЧЕНИЕ

Модуль хранит организационную структуру, штатный персонал, квалификацию,
опубликованные права, условия, область и срок их действия, отдельные контуры
внешнего оперативного взаимодействия и подрядного персонала, а также объяснимую
проверку полномочия на момент действия.

## КРИТИЧЕСКИЕ СЦЕНАРИИ

- вручную создать или изменить карточку сотрудника без потери истории;
- пакетно загрузить XLSX, проверить дубликаты и опубликовать выбранные строки;
- опубликовать утверждённую редакцию списка лиц с предоставлением прав;
- увидеть полный профиль прав сотрудника в структуре подразделений;
- определить всех лиц, которым предоставлено выбранное право;
- учесть квалификацию, область, срок и дополнительное условие;
- вести диспетчерский/оперативный персонал ОДУ, РДУ, ЦУС, смежной организации,
  смежного энергообъекта и коммерческого ДЦ отдельно от штатной матрицы;
- проверить полномочие в момент действия и сохранить объяснимый результат;
- учесть только явно ограниченное замещение.

## PRIMARY FACTS / DERIVED VIEWS

Primary facts:

- организация, вид её отношения к держателю справочника, иерархия
  подразделений, рабочее место и сотрудник;
- рабочие контакты и режим доступности сотрудника;
- квалификация по электробезопасности: категория персонала, группа, класс
  напряжения и область электроустановок;
- самостоятельные специальные квалификации: категория РЗА, группа допуска к
  работам на высоте, допуск к работам под напряжением и иные виды;
- опубликованная редакция списка лиц с предоставлением прав;
- положительная ячейка матрицы `EmployeeOperationalRight` с marker, condition,
  scope, validity, source reference, source hash и source row;
- машинная проекция опубликованной ячейки `OperationalAuthorityGrant` для
  action-time evaluator;
- внешний оперативный контакт, подрядный допуск, ограниченное замещение и
  результат проверки;
- пакет импорта и append-only история ручных/пакетных изменений.

Derived views:

- дерево подразделений и матрица прав штатного персонала;
- представление «кто имеет право»;
- полный профиль и экран редактирования сотрудника;
- реестры диспетчерских центров, ЦУС, смежных организаций/объектов,
  коммерческого ДЦ и подрядного персонала;
- предварительный просмотр XLSX с CREATE/UPDATE/error и выбором строк/блоков;
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

Изменение опубликованного права или квалификации не переписывает запись на
месте: прежняя редакция закрывается, а новая создаётся с новым периодом и
основанием. Старые проверки продолжают ссылаться на прежний snapshot.

## PERSONNEL MANAGEMENT CONTRACT

Ручной контур поддерживает create/edit/deactivate для существующих и новых
карточек. Редактируются организация, подразделение, должность, рабочее место,
контакты, режим доступности, квалификации, специальные допуски, права, scope,
validity, condition и basis. Физическое удаление карточки и audit trail
запрещено; прекращение работы выполняется деактивацией.

Пакетный импорт выполняется только как:

```text
XLSX upload
  → parse and validate
  → duplicate matching
  → preview CREATE / UPDATE / ERROR
  → selection of rows or organizational blocks
  → explicit publication
  → immutable change records
```

Поддерживаются два нормализованных шаблона: матрица штатного персонала и внешний
оперативный справочник. Повторный файл определяется по SHA-256. Отсутствие лица
в новой загрузке не деактивирует существующую карточку автоматически. Реальные
XLSX и персональные данные не сохраняются в Git.

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

Не смешиваются три разных контура:

1. штатная матрица организации;
2. внешний оперативный справочник: диспетчерский/оперативный персонал,
   руководство, ЦУС, смежные энергообъекты и коммерческий ДЦ;
3. подрядный или командированный персонал с временным home→host допуском.

Для внешнего оперативного контакта фиксируются home organization, host
organization, relation kind, подразделение или объект, контакты, schedule,
operational scope, authority summary, validity и basis. При импорте широкого
списка пользователь выбирает нужные блоки и строки; все лица источника
автоматически не публикуются.

## PERSISTENCE / EVIDENCE CONTRACT

- `EmployeeContactProfile` — рабочие контакты и доступность.
- `OrganizationOperationalProfile` — роль организации в справочнике.
- `EmployeeQualification` — категория и группа по электробезопасности.
- `EmployeeSpecialQualification` — отдельная шкала РЗА/высоты/спецдопуска.
- `EmployeeOperationalRight` — опубликованное право штатного сотрудника и
  traceable source fact одновременно.
- `OperationalAuthorityGrant` — нормализованная action/scope-проекция для
  evaluator; для штатной матрицы обязательна ссылка на source right.
- `ExternalOperationalContact` — диспетчерское/оперативное взаимодействие со
  смежной организацией или объектом.
- `ExternalPersonnelEngagement` — допуск подрядного или командированного лица.
- `OperationalAuthoritySubstitution` — только явно перечисленные actions/scope;
  автоматическое копирование всех прав запрещено.
- `PersonnelImportBatch` — SHA-256, preview, errors, author and publication.
- `PersonnelChangeRecord` append-only; physical delete and in-place update are
  prohibited.
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
Утверждённые пользовательские таблицы и списки использованы для восстановления
структуры данных, видов внешних контуров и рабочих сценариев. Реальные ФИО,
телефоны, локальные акты и workbook в Git не помещаются.

## USER EXPERIENCE CONTRACT

Основное представление — не плоский список grants, а иерархическая матрица:

```text
организация
  └─ подразделение
      └─ подчинённое подразделение
          └─ сотрудник × колонки опубликованных прав
```

Обязательны sticky identity columns, grouped rights header, читаемая единая
типографика, сворачивание дерева, поиск, фильтры по категории/группе/праву,
marker states и переход в карточку сотрудника. Группа всегда подписывается как
«группа по электробезопасности». АТП, ОП, ОРП, РП и АТП/ОП расшифровываются в
доступной легенде. Представление «кто имеет право» использует то же дерево и
показывает область, условие, срок и основание.

Редактор карточки доступен из пользовательского интерфейса, а не через
параллельную техническую admin-панель. XLSX preview показывает совпадения,
ошибки, новые и изменяемые карточки и позволяет выбирать подразделения/объекты
или отдельные строки до публикации. Технические IDs и snapshot скрыты в audit
section.

## DEMO / POST-DEMO

`DEMO-BOUNDED`: 17 синтетических штатных сотрудников в иерархии, 22 вида прав,
квалификация, более 100 положительных ячеек, linked evaluator projections,
отдельный contractor scenario и результаты `ALLOW / DENY / VERIFY`.

Management candidate дополнительно предоставляет ручной create/edit/deactivate,
XLSX templates, preview/publish, special qualifications and external operational
contacts без загрузки реальных персональных данных.

Post-demo: controlled publication реальных редакций, history diff, granular
withdrawal, production import profiles для конкретных форм ОДУ/РДУ/ПМЭС/КДЦ,
HR/AD/СКУД integration и downstream action requirements.

## DEPENDENCIES / UX CONTRACT

Dependencies: `MASTER-DATA`, `NORMATIVE-EVIDENCE`. Direction A; основной UX —
организационное дерево и матрица, отдельные режимы «Кто имеет право», внешний
персонал, карточка/редактор сотрудника, import preview и история проверок.
Проверяются populated/empty/error, create/update/deactivate, duplicate match,
plain/conditional markers, hierarchy, long scope/basis, internal/external,
light/dark и responsive states.

## CURRENT CODE STATUS / CAPABILITIES

`IMPLEMENTED-CANDIDATE`; release `IN_PROGRESS`; active work item
`PERSONNEL-AUTHORITY-001`, issue #42, Draft PR #43.

- `CAP-PERSONNEL-REGISTRY`: hierarchy, contacts, qualification, matrix,
  employee profile and create/edit/deactivate; `AC-PERSONNEL-REGISTRY-001` —
  candidate.
- `CAP-AUTHORITY-GRANTS`: published cell → linked structured evaluator
  projection and versioned edit; `AC-AUTHORITY-GRANTS-001` — candidate.
- `CAP-AUTHORITY-ACTION-TIME`: explainable `ALLOW / DENY / VERIFY`, append-only
  snapshot, digest and correction link; `AC-AUTHORITY-ACTION-TIME-001` —
  candidate.
- `CAP-AUTHORITY-EXTERNAL`: separate external operational directory,
  contractor engagement and bounded substitution; `AC-AUTHORITY-EXTERNAL-001`
  — candidate.
- controlled personnel XLSX preview/publish is implemented inside the bounded
  registry capability and does not replace the general imports module.

## OPEN VERIFY ITEMS / FORBIDDEN ASSUMPTIONS

VERIFY: production catalog of right columns; exact local meaning of every
conditional marker; authoritative current height groups; current RZA assignments;
source-specific header mapping for each production list; downstream action
requirements.

Forbidden:

- считать application role или должность operational right;
- создавать второе ручное назначение поверх опубликованной матрицы;
- автоматически переносить все права при замещении;
- автоматически публиковать все лица широкого внешнего списка;
- смешивать штатную матрицу, внешний operational directory и подрядный допуск;
- удалять карточку или историю физически;
- объявлять `VERIFY` разрешением;
- подключать OPJ/SHIFT/DEFECT/work-permit/switching lifecycles в этом PR;
- писать в preview или выполнять merge без команды пользователя.
