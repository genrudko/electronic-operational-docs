# ЭОД — текущее состояние

**Дата проверки:** 29.07.2026

## 1. Фактическая контрольная точка

```text
repository:
genrudko/electronic-operational-docs

accepted UX/application merge:
a880a632b750309c7fbfb918af15b49d99b5a93f

accepted UX source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

active work item:
OPJ-UX-001

active issue / Draft PR:
#24 / #25

active branch:
ux/opj-ux-001

current deployed candidate head:
663086c9c0b0dfa0d4e970185f0f52269be20a61

preview:
UNTOUCHED
```

Documentation-only commits after the accepted application merge do not create a new application baseline.

## 2. Project boundary

ЭОД — независимый демонстрационный прототип электронной оперативной документации для энергетики.

Не используются:

- production systems работодателя;
- реальные оперативные записи;
- реальные персональные данные;
- enterprise secrets;
- материалы без права публикации.

GitHub является source of truth. VPS используется только для runtime/test evidence.

## 3. Accepted foundation

Accepted and verified:

- Linux/PostgreSQL CI and isolated preview/development;
- canonical documentation and project operating system;
- full Django test discovery;
- trusted exact-SHA development controller;
- presentation-only trusted hot refresh;
- PLAN-001 evidence audit;
- DEFECT-001 source-bound equipment defect journal;
- UX-FOUNDATION-001 / Direction A.

### UX-FOUNDATION-001

```text
issue:
#22 / CLOSED

PR:
#23 / MERGED

source head:
688ca4ed3f306bcb6e32d145c0da6f32d5f37c89

merge commit:
a880a632b750309c7fbfb918af15b49d99b5a93f

full suite:
557 / OK

user acceptance:
mobile + desktop CONFIRMED
```

Direction A является общесистемным visual language, а не feature-local стилем журнала дефектов.

## 4. Runtime contours

### Accepted preview

```text
checkout: /srv/eod/repository
branch: main only
compose: eod-preview
app: 127.0.0.1:8765
database: eod_preview
```

### Active development

```text
compose: eod-development
app: 127.0.0.1:8766
database: eod_development
controller: /usr/local/sbin/eod-development-controller
```

Development никогда не остаётся на `main`. Product PR не пишет в preview.

## 5. Active OPJ-UX-001

Цель:

- сделать оперативный журнал вторым реальным потребителем Direction A;
- выделить минимальный shared system layer;
- выровнять одинаковые элементы главной страницы, журнала дефектов и operational journal routes;
- сохранить специализированный editor, ribbon, лист/разворот и трёхграфную форму.

Current Draft PR #25:

```text
exact candidate head:
663086c9c0b0dfa0d4e970185f0f52269be20a61

changed files:
14

models/migrations/services/routes:
UNCHANGED

five exact-head workflows:
SUCCESS

PostgreSQL suite:
564 / OK

trusted development delivery:
SUCCESS

rollback:
NOT REQUIRED

preview:
UNTOUCHED
```

Текущий gate — пользовательская desktop/mobile приёмка и repairs в том же PR. Новый parallel product PR не создаётся.

Не входят в OPJ-UX-001:

- draft registration;
- shift handover lifecycle;
- close shift;
- templates/abbreviations/suggestions;
- automatic events;
- action management;
- offline;
- SCADA;
- новые модели и migrations.

## 6. Product and research decisions

Исследование вертикальных продуктов принято как decision input:

```text
products/modules:
16

sources:
27

UX patterns:
18

preliminary decisions:
16
```

Canonical documents:

```text
docs/research/VERTICAL_PRODUCTS_RESEARCH_20260729.md
docs/research/VERTICAL_PRODUCTS_SOURCE_CATALOG_20260729.csv
docs/research/VERTICAL_PRODUCTS_DECISION_MATRIX_20260729.csv
docs/project/PRODUCT_UX_PRINCIPLES.md
```

Accepted principles:

- best-of-breed critical path;
- один первичный объект — несколько представлений;
- authoring отдельно от lifecycle;
- передача смены — отдельный workflow;
- обход — отдельная маршрутная сущность;
- SCADA — optional integration;
- одинаковые UI elements используют shared contract;
- evidence `ADOPT/ADAPT/REJECT/DEFER/VERIFY`.

Research observation не становится requirement автоматически.

## 7. Development process

Current accepted process:

```text
factual preflight
→ one issue/branch/Draft PR
→ focused/profile checks
→ trusted delivery
→ user acceptance
→ repairs
→ one full final gate
→ explicit merge
```

Presentation repair:

```text
templates/static commit
→ focused tests
→ hot refresh
→ acceptance
```

Planned after OPJ-UX-001:

1. `CI-OPT-001` — убрать повтор полного suite на GitHub и VPS при доказанном same exact SHA;
2. `DEV-EVIDENCE-001` — один machine-owned evidence comment;
3. `UI-CONTRACT-001` — browser/source contract shared UI;
4. `WORKITEM-BOOTSTRAP-001` — manifest-driven issue/PR/checklist bootstrap.

Это не блокирует текущую OPJ-UX приёмку.

## 8. Functional readiness

### Accepted

- organizations, personnel, workplaces;
- equipment/import foundation;
- document core;
- workplace documentation registry;
- specialized operational journal core/editor;
- generic operational-document core;
- DEFECT-001;
- Direction A UX foundation;
- trusted development automation.

### Advanced but lifecycle incomplete

- operational journal:
  - drafts and revisions;
  - registered immutable entries;
  - shift model;
  - editor schema v4;
  - semantic references;
  - missing connected draft registration and full handover/close lifecycle.

### Not implemented as complete vertical slices

- applications;
- dispositions/orders;
- work permits and work register;
- switching-document minimum;
- rounds;
- grounding;
- RZA/TM;
- offline;
- SCADA integration.

## 9. Non-negotiable rules

- end-user UI is Russian;
- internals use professional English;
- operational journal remains specialized;
- source-bound forms are not arbitrary user constructors;
- registered/history states are immutable;
- same-purpose UI is shared system behavior;
- SCADA is not mandatory;
- paper/hybrid/electronic modes are not declared legally equivalent without evidence;
- user performs product/UX acceptance, not programming;
- automatic merge is absent.
