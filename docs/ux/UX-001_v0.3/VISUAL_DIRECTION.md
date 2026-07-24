# VISUAL_DIRECTION — самостоятельное визуальное направление ЭОД

> **Пакет:** UX-001 v0.3  
> **Дата консолидации:** 25.07.2026  
> **Accepted application baseline:** `main / e18872face7f27f489056b72fed31e5586121b0c`  
> **Статус:** product/design direction; не юридическое заключение и не brand approval.

## 1. Позиционирование

`[PRODUCT]`

> **Самостоятельная визуальная система для цифровой платформы энергетической отрасли, использующая холодную сине-циановую природно-технологическую палитру.**

Система должна восприниматься как спокойная, точная и современная операционная среда. Она не должна выглядеть как:

- SCADA;
- Django Admin;
- банковский dashboard;
- корпоративный лендинг;
- буквальная копия бумажного журнала;
- брендированный продукт сторонней организации.

## 2. Целевой баланс

```text
лёгкий shell и навигация
+ спокойные формы и detail pages
+ высокая контролируемая плотность в журналах и реестрах
```

Лёгкость не означает разреженность. На длинной смене оператор должен видеть достаточный объём данных без постоянных переходов.

## 3. Границы независимой identity

### Запрещено

- использовать чужие логотипы, знаки и товарные обозначения;
- воспроизводить ленту Мебиуса или сходную узнаваемую композицию;
- копировать шаблон сайта, фирменную графику или точный градиент;
- помещать название конкретной компании в shell, splash, footer или product copy;
- заявлять официальную принадлежность, одобрение или внедрение;
- описывать palette в репозитории как основанную на корпоративной айдентике;
- использовать символику, создающую вероятность ошибочной идентификации продукта.

### Допустимо как общее направление

- холодные blue/cyan hues;
- светлые neutral surfaces;
- ассоциации с воздухом, водой, чистой энергией и технологичностью;
- абстрактная геометрия без узнаваемого чужого знака;
- собственное текстовое обозначение `ЭОД` как рабочее имя прототипа.

Этот документ не является юридическим заключением. При официальном внедрении branding и naming должны пройти отдельное согласование.

## 4. Visual DNA

### 4.1 Свет и поверхности

- основная рабочая поверхность светлая;
- shell легче текущего и не выглядит почти чёрной инженерной консолью;
- elevated surfaces используются только для overlays и самостоятельных областей;
- borders не рисуют каждую группу;
- hierarchy создаётся typography, whitespace, alignment и selective background.

### 4.2 Цвет

Цвет применяется как сигнал:

- active section;
- primary action;
- focus;
- selection;
- relation;
- lifecycle state;
- integrity incident;
- progress.

Цвет не применяется для декоративной заливки десятков cards.

Candidate guideline для светлой темы:

```text
80–90% neutral surfaces
8–15% quiet blue hierarchy
2–5% semantic accents
```

Это ориентир для reference screens, не нормативная формула.

### 4.3 Типографика

- предметное содержание визуально сильнее captions и metadata;
- title scale ограничен: продукт не должен выглядеть как маркетинговый сайт;
- tabular numerals применяются к времени, номерам и измерениям;
- длинные русские наименования допускают перенос и раскрытие;
- uppercase используется только для коротких technical labels, но не как основной стиль UI.

### 4.4 Форма

- moderate radii, не «пузырчатый» consumer UI;
- минимальные тени;
- преимущественно flat hierarchy;
- тонкие разделители вместо множества bordered cards;
- status indicators компактны и сопровождаются текстом.

### 4.5 Иконография

- единый outline family;
- иконка не заменяет непонятное действие;
- critical actions имеют текст;
- decorative energy/wind icons не используются в рабочих таблицах;
- никакой графики, сходной с чужим товарным знаком.

### 4.6 Движение

- motion короткий и функциональный;
- не анимировать tables, long journal pages и critical state changes;
- respect reduced motion;
- transitions не должны создавать ощущение consumer dashboard.

## 5. Shell

### Сохраняется

- постоянная идентификация системы;
- current area;
- user/session controls;
- доступ к справочникам и настройкам.

### Изменяется

- уменьшается визуальная тяжесть topbar;
- top-level areas ограничиваются устойчивыми рабочими областями;
- module catalog переносится во вторичную навигацию;
- active area получает точечный blue/cyan signal;
- technical/admin areas отделяются от everyday work;
- current shift/workplace context доступен без перегрузки header.

### Candidate structure

```text
[ЭОД] [Рабочее место] [Оперативная документация] [Документы] [Справочники]
                                         [Поиск] [Состояние смены] [Пользователь]
```

Названия областей требуют отдельного product confirmation.

## 6. Forms и detail pages

### Forms

- одна основная column flow;
- source-bound sections сохраняют порядок источника;
- secondary sections раскрываются по необходимости;
- sticky action area допускается только для длинной формы;
- disabled controls не используются как способ показать read-only document;
- help text короткий, подробности по запросу.

### Detail

```text
identity + state
subject summary
current responsibility / next action
core facts
relations and lifecycle
provenance / audit disclosure
```

Карточка используется только когда block имеет самостоятельный background, action set или scroll context.

## 7. Tables и registries

- header и controls компактны;
- primary operational columns остаются в первом viewport;
- secondary columns могут уходить в controlled horizontal scroll;
- row identity и subject stronger than metadata;
- vertical grid lines минимальны;
- status не должен превращать таблицу в набор разноцветных pills;
- selected, focused, hovered и critical states различаются;
- user may hide optional columns;
- full value длинного русского наименования всегда доступно.

## 8. Operational journal

Целевой образ — рабочий документ с цифровыми преимуществами.

- page/spread remains primary surface;
- inactive entries почти не показывают editor chrome;
- active entry показывает save truth и необходимые commands;
- anomalies остаются видимыми;
- relation markers единообразны;
- ribbon содержит compact core и expandable secondary commands;
- settings не должны reflow document geometry;
- clean copy визуально отделён от draft workspace.

## 9. Dark theme

Dark theme не является инверсией light theme.

- dark surfaces остаются нейтрально-синими, не чёрными;
- cyan не используется как large-area glow;
- data density и separators проверяются отдельно;
- status colors не теряют meaning;
- paper-like journal может сохранять светлую page surface даже в dark shell — это open design option.

## 10. Tone of voice

- короткие предметные формулировки;
- глагол действия вместо generic `Выполнить`;
- нормальный русский язык без кальки с internal model;
- diagnostic vocabulary раскрывается отдельно;
- сообщения называют объект, состояние и следующее действие.

Пример:

```text
Не сохранено: запись изменена другим пользователем.
Открыть сравнение
```

вместо:

```text
Ошибка выполнения операции. Conflict.
```

## 11. Reference validation

Visual direction принимается только после проверки на:

1. application shell;
2. defect list/form/detail family или другом утверждённом structured vertical slice;
3. operational journal workspace.

Для каждого нужны target desktop, long Russian fixture, normal/error/empty/loading/read-only, keyboard focus map и light theme. Dark theme проверяется, если входит в release gate.

## 12. Критерии принятия

- пользователь не описывает screen как административную панель;
- предметная задача определяется за 3–5 секунд без чтения технических labels;
- primary action однозначен;
- audit/provenance не конкурирует с рабочим содержанием;
- color не является единственным носителем состояния;
- нет элементов, создающих впечатление официальной принадлежности сторонней организации;
- density остаётся достаточной для сменной работы;
- visual language согласован на всех трёх reference families.
