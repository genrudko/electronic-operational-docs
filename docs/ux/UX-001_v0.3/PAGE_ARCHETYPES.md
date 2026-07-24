# PAGE_ARCHETYPES — устойчивые типы страниц ЭОД

> **Пакет:** UX-001 v0.3  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

## 1. Общая анатомия

```text
application shell
context path
page identity + state + primary action
critical limitation only when needed
primary working surface
supporting details
provenance/audit disclosure
```

Layout width зависит от archetype; единый max-width для всех pages запрещён.

## A-01. Application home/workspace

Purpose:

- показать current shift/workplace;
- unresolved operational work;
- critical incidents;
- continue recent task;
- открыть рабочую область.

Module catalog — secondary.

## A-02. Operational journal workspace

Specialized book/page surface with compact journal context, command hierarchy, page/spread, active-entry toolbar, relation overlays, stable settings/shift panel and clean copy/print route.

Document content dominates editor chrome.

## A-03. Structured journal registry

```text
context + journal title + primary action
compact state/source line
search/common filters/active chips
data grid
pagination
```

Primary columns fit target desktop. Secondary columns may use controlled horizontal scroll.

## A-04. Structured record detail

Hierarchy:

1. identity/state/integrity;
2. subject summary;
3. next action/owner;
4. key facts;
5. lifecycle/relations;
6. provenance/audit.

Avoid equal card wall.

## A-05. Structured record form

- source-bound order;
- error summary;
- main fields;
- equipment/participants/documents;
- sticky save for long form;
- dirty state;
- explicit save;
- registered edit prohibited.

## A-06. Cross-document timeline

Chronological/causal view of accepted domain relations. Event time and registration time remain distinct. No invented lifecycle events.

## A-07. Cross-type document registry

Search across documents and structured records with explicit type/status/source distinction. Preview drawer preserves list context.

## A-08. Directory

Concise registry + effective state/history. Normal users see Russian domain names; technical IDs in provenance/diagnostic disclosure.

## A-09. Import/staging/review

Higher technical density is acceptable:

- raw vs normalized;
- source;
- conflict groups;
- decision;
- publication preview;
- progress.

Still requires hierarchy and no uncontrolled technical wall.

## A-10. Administrative configuration

Draft revision → compare → validate → publish → effective period → audit. Permission boundary strong. Publication is not a switch.

## A-11. Read-only registered document

Rendered content, lifecycle and integrity as separate dimensions, correction path, source and audit disclosure.

## 2. Width and density by archetype

| Archetype | Density | Overflow |
|---|---|---|
| home | calm | vertical only |
| detail | calm/medium | wrapping/disclosure |
| form | medium | no horizontal form scroll |
| registry | medium/high | controlled horizontal for optional columns |
| journal | high | specialised page geometry |
| import | high | controlled table/panel overflow |
| admin | medium/high | desktop-first |

Concrete widths remain candidate in `DESIGN_TOKENS.md`.

## 3. Shared states

Every archetype specifies loading, empty, partial/permission-limited, error, read-only, stale/conflict, integrity incident, long data and narrow viewport.

## 4. Long-data fixture

- `ПС 330 кВ Барсуки. ОРУ 330 кВ. Выключатель В-330 кВ № 3 присоединения ВЛ 330 кВ Барсуки — Невинномысск`;
- `ВЭУ № 07. Щит управления преобразователя частоты, секция 690 В, шкаф контроллера системы охлаждения силовых модулей`;
- `Инструкция по ведению оперативной документации оперативным персоналом ЦОТУиЭ ВЭС Невинномысск, приложение № 12`;
- `Александров Александр Александрович — начальник смены ветровой электрической станции`.

Pass:

- identity not lost;
- full value available;
- no control overlap;
- row height remains understandable;
- sorting/filtering uses canonical value;
- truncation is not the only access to data.

## 5. Paper-first boundary

Журнал ключей может использовать registry/reference/electronic-copy archetype, но UX-001 не предполагает полный electronic lifecycle. UI должен явно показывать статус оригинала без заявления о замене бумаги.
