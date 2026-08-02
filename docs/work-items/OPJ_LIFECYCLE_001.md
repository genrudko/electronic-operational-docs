# OPJ-LIFECYCLE-001 — жизненный цикл записей оперативного журнала

## Состояние

```text
work item: OPJ-LIFECYCLE-001
issue: #46
branch: feature/opj-lifecycle-001
PR: PENDING
baseline main tip: 17663cf67d12c02d24177e554d6eb7d364e405e4
status: IMPLEMENTATION IN PROGRESS
preview: UNTOUCHED
merge authorization: ABSENT
```

## Цель

Завершить bounded Demo-контур специализированного оперативного журнала: сохранить принятый редактор и черновики, обеспечить неизменяемую регистрацию, append-only исправления/отмены и отдельные структурированные факты оперативных переговоров.

## Принятые архитектурные границы

1. `OperationalLogEntry` остаётся неизменяемым оригиналом.
2. Исправление и отмена создаются только новым связанным событием с собственным снимком и digest.
3. Оперативный разговор является отдельным фактом и не подменяет запись другого модуля.
4. На каждое предметное действие сохраняется action-time evaluation полномочия; `DENY` не создаёт факт, `VERIFY` отображается явно и не выдаётся за доказанное право.
5. Direction A, Onest Variable и EOD Outline 24 используются без второй дизайн-системы.
6. Shift handover, generic cross-document relations, SCADA и offline merge остаются вне задачи.

## Acceptance criteria

- оригинал нельзя изменить или удалить;
- correction/cancellation образуют append-only историю;
- communication хранит время, направление, канал, участника/организацию и содержание;
- authority evaluation/snapshot привязан к действию;
- integrity проверяется по canonical snapshot/digest;
- карточка показывает оригинал, актуальное представление и историю;
- существующие draft/revision/autosave/print contracts сохранены;
- desktop 1440×900, compact 1024×768 и mobile 390×844 работают в light/dark/system;
- миграции, focused/full tests, пять exact-head workflows и trusted development deployment успешны;
- merge и Ready for Review выполняются только по отдельной команде пользователя.
