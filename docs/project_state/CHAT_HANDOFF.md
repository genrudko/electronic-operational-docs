# ЭОД — handoff основного интеграционного чата

## Проект

Независимый демонстрационный прототип электронной оперативной документации. Пользователь — начальник смены ВЭС и предметный эксперт, не программист.

## Формат работы

Ассистент выдаёт один полный автономный Python-patch. Пользователь запускает его локально и возвращает лог и видео. Ручные изменения кода пользователем не требуются.

## Репозиторий

```text
root: G:\electronic-operational-docs
branch: main
Repair 2 input baseline: fec8bd675f9565b0c4e398124cd22f8fabec02b4
current technical HEAD after Repair 2: read from successful patch log
port: 8765
push: not performed automatically
```

## Завершено

- Patch 011.5 — оборудование и объекты диспетчеризации;
- Patch 011.6 — персонал, права и документация рабочего места;
- Patch 011.7 Repair 1 Revision 10 — техническое ядро структурированной оперативной документации, commit `fec8bd675f9565b0c4e398124cd22f8fabec02b4`, full suite 495/495, один skipped.

## Текущий этап

Patch 011.7 Repair 2 Revision 1 исправляет архитектурную границу после визуальной проверки.


Первая попытка Repair 2 от 24.07.2026 01:21:40 остановилась на Ruff:
две E501 в `scripts/gate_patch_011_7.py` и один F401 в профильном тесте.
Rollback полный: обе БД восстановлены, worktree `fec8bd67 / clean`, commit отсутствует.
Revision 1 исправляет эти дефекты и добавляет ранний payload static contract.

Журналы не конструируются оператором. Формы устанавливаются только из утверждённых инструкций. Repair 2 отключает ручной веб-конструктор, вводит каталог source-bound форм, блокирует новые действия по техническим тестовым схемам и упрощает пользовательский интерфейс записи.

Базовый источник каталога: `И-00-007-ОР-2025 версия 2`, разделы 7–11, приложения № 4–8.

## Snapshot Repair 2

```text
archive: eod_prepatch_snapshot_20260724_004536_fec8bd67_011.7-repair2.zip
SHA-256: cdbe4fa878cc1c26d2aec2d4a93daa6b856a5f2e108ec1cce1d17d1d9eaba081
branch: main
HEAD: fec8bd675f9565b0c4e398124cd22f8fabec02b4
worktree: clean
```

## Непрерывность

- pre-patch snapshot перед каждым Patch/Repair;
- `EOD_CURRENT_CONTEXT.zip` только после визуального принятия;
- новый чат начинает работу с проверки manifest и baseline.
