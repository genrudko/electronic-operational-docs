# Контролируемый словарь технического английского

## Назначение

Внутренние имена моделей, полей, сервисов, импортёров и API формируются по
профессиональной англоязычной терминологии электроэнергетики. Буквальный машинный
перевод русских эксплуатационных терминов не используется.

Русские пользовательские названия, утверждённые диспетчерские наименования,
названия должностей и документов хранятся в исходной форме и не заменяются
английскими вариантами.

Машиночитаемый источник словаря:

```text
src/apps/imports/domain_glossary.py
```

## Базовые правила

1. Кодовые имена используют `snake_case`.
2. Один русский доменный термин имеет одно утверждённое внутреннее имя.
3. Тип оборудования и экземпляр оборудования — разные сущности.
4. `disconnector` используется для разъединителя, `circuit_breaker` — для выключателя,
   `earthing_switch` — для заземляющего ножа.
5. `switchgear_bay` означает ячейку распределительного устройства.
6. `cable_circuit` означает отдельную электрическую цепь кабельной линии.
7. `operational_designation` — внутреннее имя поля утверждённого диспетчерского
   наименования; само русское наименование не переводится.
8. `operational_control` и `operational_jurisdiction` не смешиваются: первое
   обозначает право непосредственного управления, второе — закреплённую компетенцию
   согласования изменения состояния или режима.
9. Новые термины сначала добавляются в словарь, затем используются в модели данных.

## Ключевые соответствия

| Русский термин | Внутреннее имя | Technical English |
|---|---|---|
| Ветровая электростанция | `wind_power_plant` | wind power plant |
| Подстанция | `substation` | substation |
| Воздушная линия | `overhead_line` | overhead line |
| Кабельная линия | `cable_circuit` | cable circuit |
| Распределительное устройство | `switchgear` | switchgear |
| Ячейка РУ | `switchgear_bay` | switchgear bay |
| Секция шин | `busbar_section` | busbar section |
| Выключатель | `circuit_breaker` | circuit breaker |
| Разъединитель | `disconnector` | disconnector |
| Заземляющий нож | `earthing_switch` | earthing switch |
| Силовой трансформатор | `power_transformer` | power transformer |
| Трансформатор собственных нужд | `station_service_transformer` | station service transformer |
| Трансформатор напряжения | `voltage_transformer` | voltage transformer |
| Трансформатор тока | `current_transformer` | current transformer |
| Релейная защита | `relay_protection` | relay protection |
| Диспетчерское наименование | `operational_designation` | operational designation |
| Диспетчерское управление | `dispatch_control` | dispatch control |
| Оперативное управление | `operational_control` | operational control |
| Оперативное ведение | `operational_jurisdiction` | operational jurisdiction |
| Оперативный журнал | `operational_log` | operational log |
| Перечень документации рабочего места | `workplace_document_register` | workplace document register |
| Группа по электробезопасности | `electrical_safety_group` | electrical safety group |
| Оперативное право | `operational_authority` | operational authority |
| Профиль данных | `data_profile` | data profile |
| Партия импорта | `import_batch` | import batch |
| Схема сопоставления | `import_mapping_template` | import mapping template |

Полный нормативный набор находится в Python-модуле и проверяется профильным gate.
