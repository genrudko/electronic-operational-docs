# UX-001 v0.3 — индекс консолидированного пакета

> **Пакет:** UX-001 v0.3  
> **Дата консолидации:** 25.07.2026  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Metadata note:** DOCS-002 — отдельный follow-up; его SHA не подменяет application baseline.  
> **Статус:** проектный контракт; production code, domain model и lifecycle этим пакетом не изменяются.

## 1. Назначение

Пакет сводит без противоречий:

1. исходный brief UX-001;
2. UX-001 v0.2;
3. runtime-видео текущего интерфейса длительностью 3:29.7;
4. актуальное продуктовое решение о визуальной эволюции интерфейса.

Ключевое решение v0.3:

> **Сохранить сильные рабочие механики, но провести полноценную эволюцию визуального языка: от технической административной системы к современной операционной платформе энергетического предприятия.**

Это не big-bang rewrite и не косметическая перекраска. Изменения должны внедряться через реальные vertical slices, не останавливая продуктовую разработку.

## 2. Принятые ограничения

- Журнал дефектов — сильный кандидат на первый reference vertical slice, но не считается окончательно утверждённым до завершения PLAN-001.
- Журнал ключей остаётся paper-first; полный электронный lifecycle не входит в обязательный внутренний прототип.
- UI/UX-контур не меняет domain model, не утверждает lifecycle документов и не пишет production code.
- Интерфейс только русский; технический английский допускается во внутренних моделях, API, importers и diagnostic/provenance mode.
- Visual identity полностью самостоятельна. Запрещено создавать впечатление официальной связи с какой-либо компанией или группой компаний.

## 3. Состав

| Файл | Назначение |
|---|---|
| `UI_AUDIT.md` | консолидированный системный аудит |
| `VIDEO_EVIDENCE_AUDIT.md` | timestamped runtime evidence |
| `VISUAL_DIRECTION.md` | самостоятельное визуальное направление |
| `UI_PRINCIPLES.md` | проверяемые продуктовые UI-принципы |
| `DESIGN_TOKENS.md` | candidate tokens и правила их валидации |
| `COMPONENT_CONTRACT.md` | компоненты, состояния и визуальная иерархия |
| `INTERACTION_CONTRACT.md` | keyboard, focus, save, overlays, navigation |
| `PAGE_ARCHETYPES.md` | устойчивые типы страниц |
| `REFERENCE_SCREENS.md` | три согласованных reference screen contracts |
| `UX_IMPLEMENTATION_ROADMAP.md` | поэтапное внедрение без остановки разработки |
| `manifest.json` | размеры и SHA-256 всех документов, кроме manifest |

## 4. Что изменено относительно v0.2

1. Удалён тезис, что текущему visual language достаточно локальной нормализации.
2. Зафиксировано восприятие UI как слишком технического и административного.
3. Добавлен самостоятельный visual direction с холодной сине-циановой природно-технологической атмосферой.
4. Все конкретные HEX, размеры, радиусы, тени и breakpoints переведены в статус `candidate`.
5. Исправлено правило таблиц: управляемый horizontal scroll допустим для вторичных колонок.
6. Введена единая модель доказательности.
7. Созданы три полноценные reference specifications:
   - application shell;
   - defect list/form/detail family;
   - operational journal workspace.
8. Roadmap сделан условным по отношению к PLAN-001 и не присваивает окончательный первый vertical slice.
9. Manifest не содержит собственный hash и размер.

## 5. Acceptance status

| Gate | Статус |
|---|---|
| Baseline metadata актуальны | ✅ |
| v0.2 и новое визуальное решение сведены | ✅ |
| Visual direction отражён во всех зависимых документах | ✅ |
| Candidate tokens не выданы за стандарт | ✅ |
| Три reference contracts согласованы | ✅ |
| Runtime evidence отделён от inference | ✅ |
| Manifest self-consistent | ✅ проверяется скриптом при сборке |
| Открытые domain questions перечислены | ✅ |
| Roadmap не блокирует продуктовую разработку | ✅ |

## 6. Открытые вопросы для основного интеграционного контура

1. Какой journal vertical slice окончательно выбирается после PLAN-001?
2. Каков утверждённый lifecycle дефекта и какие переходы допустимы в прототипе?
3. Какие поля source form обязательны для defect journal?
4. Какие роли вправе создавать, назначать, изменять статус и закрывать дефект?
5. Какой desktop viewport считается основным для внутреннего показа?
6. Нужен ли dark theme к внутреннему прототипу или только к полной демонстрационной версии?
7. Какие audit/integrity сведения обязательны в обычном рабочем режиме, а какие можно скрыть в provenance disclosure?

## FOR_MAIN_INTEGRATION_CHAT

- Использовать `main / e18872face7f27f489056b72fed31e5586121b0c` как application baseline.
- Не использовать DOCS-002 SHA как replacement baseline.
- Не утверждать defect journal до PLAN-001.
- Принять visual evolution как продуктовую цель, а не palette-only task.
- Проводить внедрение через foundation + выбранный real vertical slice + parallel journal stabilization.
