# UI_PRINCIPLES — принципы интерфейса ЭОД

> **Пакет:** UX-001 v0.3  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`

## P-01. Операционная задача важнее структуры системы

Пользователь видит событие, документ, оборудование и следующее действие, а не внутреннюю модель records/revisions/relations.

**Проверка:** обычный пользователь описывает назначение screen без знания database terminology.

## P-02. Современная операционная среда, не administrative console

Сильные механики сохраняются, visual language меняется.

**Проверка:** reference screens не напоминают Django Admin, SCADA или module catalog.

## P-03. Контекст не теряется

Фильтры, сортировка, page, selected row, scroll anchor, workplace и shift context восстанавливаются после detail/overlay/back.

## P-04. Одно доминирующее следующее действие

Primary action определяется состоянием объекта и задачей screen. На одном уровне нет двух визуально равных primary buttons.

## P-05. Иерархия раньше контейнеров

Typography, alignment и spacing используются до добавления card/border. Удаление border не должно разрушать понимание структуры.

## P-06. Контролируемая плотность

Journal и registry могут быть плотными; shell, detail и form остаются спокойными. Target desktop показывает основные рабочие данные без избыточного scrolling, но не превращается в мелкую техническую таблицу.

## P-07. Рабочие данные сильнее audit metadata

Subject, equipment, state, owner и next action визуально доминируют над UUID, hash, revision и raw source values.

## P-08. Цвет — сигнал, не декорация

Color применяется к focus, selection, state, relation и action; не заливает десятки равноправных blocks. Grayscale view сохраняет hierarchy.

## P-09. Source и provenance доступны, но не навязаны

Source-bound nature не скрывается. Подробности раскрываются по запросу или при проблеме.

## P-10. Draft, registered и integrity — разные измерения

Lifecycle state, editability и integrity не смешиваются. Registered record с integrity incident не выглядит как обычный success.

## P-11. Keyboard сохраняет нативное редактирование

Native text editing имеет приоритет над workspace shortcuts.

## P-12. Focus является частью состояния

Focus visible, predictable и возвращается к invoker после overlay.

## P-13. Overlay не становится вторым приложением

Popover — короткий context, drawer — вспомогательная inspection/adjustment, modal — краткое blocking decision.

## P-14. Semantic relation остаётся редактируемой

Relation сохраняет предметный target и human-readable text; технический marker не дублируется. Copy/paste, undo/redo, target change, save/reload и print проходят regression suite.

## P-15. Длинные русские данные — normal case

Ф.И.О., должности, диспетчерские наименования и названия документов не считаются edge case.

## P-16. Горизонтальная прокрутка управляется, а не запрещается

Основные operational columns доступны сразу. Secondary columns могут использовать controlled horizontal scroll или disclosure. Нельзя терять плотность ради формального отсутствия scroll.

## P-17. Mobile — вспомогательный режим

Smartphone поддерживает read/search/status/relations и отдельно утверждённые safe actions. Полный journal editing не обещается автоматически.

## P-18. Visual identity самостоятельна

UI не использует чужие logos, marks, compositions или naming и не создаёт впечатление официальной связи.

## P-19. Не обобщать раньше двух реальных применений

Shared component извлекается после проверки минимум на двух domain usages, кроме базовых primitives.

## P-20. Evidence определяет степень уверенности

Runtime observation, source-derived finding, recommendation, inference и open question не смешиваются. Каждый high-impact conclusion имеет evidence label.
