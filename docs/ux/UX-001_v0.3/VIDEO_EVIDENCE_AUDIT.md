# VIDEO_EVIDENCE_AUDIT — аудит актуального runtime-видео

> **Пакет:** UX-001 v0.3  
> **Дата консолидации:** 25.07.2026  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Статус:** только наблюдаемое runtime evidence.

## 1. Источник и границы

- Файл: `2026-07-24-15-53-34-67f6.mp4`
- Длительность: приблизительно 3:29.7
- Разрешение: 2560×1392
- Частота: 60 fps
- Аудио: отсутствует
- Показанный режим: desktop, light theme, преимущественно mouse-driven

Этот документ фиксирует только наблюдаемое. Выводы о keyboard, focus sequence, screen reader, dark theme и narrow viewport здесь не делаются.

## 2. Timestamp map

| Время | Наблюдаемый экран/действие |
|---:|---|
| 00:00 | главная рабочая страница |
| 00:05 | зарегистрированный документ и integrity state |
| 00:20 | черновик документа |
| 00:30 | иерархия оборудования |
| 00:35 | реестр оборудования |
| 00:40 | карточка оборудования |
| 00:55 | import review |
| 01:25 | управление и ведение |
| 01:35 | организация и персонал |
| 02:15 | зарегистрированный оперативный журнал |
| 02:20 | рабочая смена и book workspace |
| 02:30 | длинные записи и повторяющиеся markers |
| 02:35 | relation popovers |
| 02:45 | drawer смены и редактора |
| 02:55 | browser print preview |
| 03:15 | structured journals registry |
| 03:20 | forms registry |
| 03:28 | structured record detail |

## 3. Наблюдения

### V-01 — shell последователен, но визуально тяжёл

`[RUNTIME]` Верхняя тёмная панель остаётся постоянной и содержит много first-level navigation. Это подтверждает визуальный вес и ограниченную масштабируемость при добавлении разделов.

### V-02 — главная выглядит как каталог модулей

`[RUNTIME]` Основную область занимают cards разделов и пояснения.

### V-03 — lifecycle и integrity показаны одновременно

`[RUNTIME]` Видны зелёный статус регистрации и сообщение о нарушенной целостности. Видео подтверждает конфликт визуальной иерархии, но не ошибку domain state.

### V-04 — internal identifiers присутствуют в ordinary UI

`[RUNTIME]` Наблюдаются UUID-like identifier, `DEMO-*`, English internal codes и technical hashes.

### V-05 — реестры используют banners, metrics, filters и table

`[RUNTIME]` До данных располагается несколько вертикальных уровней интерфейса.

### V-06 — управление и ведение визуально различены

`[RUNTIME]` Две предметные колонки позволяют сравнить тип, субъект и уровень. Это сильный существующий pattern.

### V-07 — operational journal имеет специализированную рабочую область

`[RUNTIME]` Наблюдаются книжная таблица, command bar, editor controls, режимы просмотра и drawer.

### V-08 — повторяющиеся semantic markers видны

`[RUNTIME]` В одной из длинных записей remarks area содержит серию повторяющихся красных icons/markers. Видео не показывает точную последовательность copy/paste, но подтверждает конечное дефектное состояние.

### V-09 — relation popover предметно полезен

`[RUNTIME]` Popover показывает человека или оборудование и действия открытия/изменения связи. Keyboard доступность не показана.

### V-10 — drawer объединяет разнородные функции

`[RUNTIME]` В одном drawer видны состав смены, display settings, typography controls, page size, draft state и removed entries.

### V-11 — открытие drawer меняет доступную ширину workspace

`[RUNTIME]` Рабочая область перераспределяется при открытии правой панели. Видео не доказывает изменение page count, но подтверждает риск reflow.

### V-12 — print content читаем, browser chrome остаётся

`[RUNTIME]` Табличная печатная форма читается; header/footer браузера содержат дату, URL и page count.

### V-13 — structured registry визуально предшествует данным

`[RUNTIME]` Source notice, warning, metrics и filters занимают большую область перед коротким list.

### V-14 — structured records выглядят как реальные рабочие записи

`[RUNTIME]` Technical/demo records имеют правдоподобные номера, статусы и содержание. Page-level warning присутствует, но record-level distinction визуально слабее основного содержания.

## 4. Что видео не подтверждает

- caret placement;
- `Ctrl+Left/Right/Home/End`;
- `PgUp/PgDown`;
- keyboard opening/closing popovers;
- focus return;
- Tab order;
- screen-reader announcements;
- dark theme;
- responsive behavior;
- contrast compliance;
- autosave network/error behavior;
- exact cause marker duplication.

## 5. Вывод по visual quality

`[RUNTIME]` UI не выглядит сломанным или стилистически случайным.

`[PRODUCT]` Пользователь считает его слишком техническим.

Оба утверждения совместимы:

```text
аккуратная реализация
≠
правильный продуктовый визуальный образ
```

Требуется эволюция hierarchy, surfaces, navigation, metadata disclosure и color behavior, а не только исправление отдельных CSS defects.
