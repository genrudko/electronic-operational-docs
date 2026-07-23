# ЭОД — история патчей

## Принятый baseline перед Patch 011.7

```text
main / b73510a5b64b4f7faf9d80996c8ad3dba4822d6f / clean
```

### Patch 011.6.2 Repair 4

- результат: технически и визуально принят;
- commit: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- полный тестовый набор: 485, один skipped;
- push: не выполнялся.

## Patch 011.7 — первая попытка

- запуск: 23.07.2026 17:48:23 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_operational_documentation_core_20260723_174823.log`;
- результат: отказ на Ruff до миграций и тестов;
- дефекты: три E501, три отсутствующих `__str__`, один неиспользуемый `typing.Any`;
- обе runtime DB восстановлены;
- все новые файлы удалены;
- rollback: clean;
- commit не создавался.

## Patch 011.7 Repair 1

- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- исправляет подтверждённые Ruff-дефекты в исходном полном payload;
- добавляет постоянный `docs/project_state/` и менеджер context package;
- первая дистрибуция Repair 1 была запущена 23.07.2026 в 20:08:52 +03:00;
- отказ произошёл в preflight до backup, миграций, изменений файлов и БД;
- причина: патч ошибочно требовал SHA конкретной старой сборки snapshot, хотя новый
  корректный snapshot имел тот же branch, HEAD, clean worktree и назначение;
- файловый лог не создался, потому что logger подключался только после preflight;
- исправленная ревизия 1 подключает лог до preflight и проверяет snapshot по
  самосогласованным manifest, sidecar SHA-256, branch, HEAD и назначению;
- окончательный технический результат определяется новым patch-логом;
- окончательная приёмка определяется отдельной визуальной проверкой.

## Patch 011.7 Repair 1 Revision 1

- запуск: 23.07.2026 20:18:08 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision1_operational_documentation_core_20260723_201808.log`;
- snapshot `011.7-repair1` и его самосогласованный SHA-256 успешно проверены;
- отказ произошёл в preflight до backup, изменений файлов, миграций и обращения к БД;
- причина: `docs/project_state/DECISION_LOG.md` во встроенном payload завершался двумя LF
  вместо требуемого одного;
- файловый лог был создан корректно до preflight;
- rollback не требовался, commit не создавался, baseline остался clean;
- Revision 2 нормализует окончание файла и повторно проверяет окончания всех 35 payload-файлов.

## Patch 011.7 Repair 1 Revision 2

- запуск: 23.07.2026 20:29:27 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision2_operational_documentation_core_20260723_202927.log`;
- snapshot, baseline-хеши, payload, backup и ранние contract checks прошли;
- отказ произошёл на общем Ruff до миграций и тестов;
- причина: в новом `scripts/eod_context_manager.py` оставались I001 и B904;
- обе runtime DB восстановлены из проверенных backup;
- все 35 файлов откатаны, worktree после rollback clean;
- commit не создавался;
- Revision 3 исправляет импорт datetime и явную цепочку исключения, а также проверяет
  эти условия до общего Ruff.

## Patch 011.7 Repair 1 Revision 3

- запуск: 23.07.2026 20:54:02 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision3_operational_documentation_core_20260723_205402.log`;
- snapshot, baseline-хеши, payload, backup и ранние contract checks прошли;
- B904 был устранён, но общий Ruff повторно выявил I001 в import block context manager;
- обе runtime DB восстановлены из проверенных backup;
- все 35 файлов откатаны, worktree после rollback clean;
- миграции и тесты не запускались, commit не создавался;
- Revision 4 добавляет поддерживаемый `# isort: skip_file` только в автономный context manager,
  сохраняя проверки E, F, B, UP и DJ для файла и общий Ruff для всего проекта.

## Patch 011.7 Repair 1 Revision 4

- запуск: 23.07.2026 21:14:05 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision4_operational_documentation_core_20260723_211405.log`;
- snapshot, payload, backup, Ruff, compileall, static gate, Django checks и миграции
  чистой, presentation и development БД прошли;
- профильные тесты: 10 запущено, 1 failure и 7 errors;
- основная причина семи errors: `Workplace` не имеет поля `public_id`, но оно
  использовалось в каноническом снимке записи;
- связанный скрытый дефект: фильтр рабочего места и HTML option также использовали
  отсутствующий `public_id`;
- причина failure мастера типов: `searchable initial=True` делал пустые дополнительные
  формы связанными и невалидными;
- обе runtime DB восстановлены из проверенных backup;
- все 35 файлов откатаны, worktree после rollback clean;
- commit не создавался;
- Revision 5 использует `Workplace.code` как устойчивый идентификатор внутри организации
  и устраняет ложную изменённость пустых дополнительных строк formset.

## Patch 011.7 Repair 1 Revision 5

- запуск: 23.07.2026 21:36:18 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision5_operational_documentation_core_20260723_213618.log`;
- snapshot, payload, backup, Ruff, compileall, static gate, Django checks, миграции
  чистой, presentation и development БД и все предыдущие профильные gate прошли;
- профильные тесты Patch 011.7: 10 запущено, 9 прошло, 1 failure;
- продуктовая фильтрация по организации, рабочему месту и оборудованию работала;
- причина failure находилась в синтетическом тесте: запрос `теплов` отсутствовал в
  заголовке, сводке, поисковых динамических полях, участниках, оборудовании и документах
  созданной записи, поэтому substring-поиск корректно вернул пустой результат;
- обе runtime DB восстановлены из проверенных backup;
- все 35 файлов откатаны, worktree после rollback clean;
- commit не создавался;
- Revision 6 заменяет тестовый запрос на `нагрев`, реально присутствующий в поисковом
  динамическом поле DESCRIPTION, и закрепляет это условие в static gate.

## Patch 011.7 Repair 1 Revision 6

- запуск: 23.07.2026 22:24:10 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision6_operational_documentation_core_20260723_222410.log`;
- snapshot, payload, backup, Ruff, compileall, static gate, Django checks, миграции
  чистой, presentation и development БД и все предыдущие профильные gate прошли;
- профильные тесты Patch 011.7: 10 запущено, 9 прошло, 1 failure;
- запрос `нагрев` действительно присутствовал в динамическом поле, однако сохранённый
  индекс содержал `Нагрев`, а SQLite `icontains` не выполняет Unicode casefold для кириллицы;
- обе runtime DB восстановлены из проверенных backup;
- все 35 файлов откатаны, worktree после rollback clean;
- commit не создавался;
- Revision 7 сохраняет индекс и запрос в NFKC + casefold и проверяет поиск запросом
  `НАГРЕВ`, чтобы контракт не зависел от регистра кириллицы.

## Patch 011.7 Repair 1 Revision 7

- запуск: 23.07.2026 22:55:01 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision7_operational_documentation_core_20260723_225501.log`;
- snapshot, payload, backup, Ruff, compileall, static gate, Django checks, миграции
  чистой, presentation и development БД и предыдущие профильные gate прошли;
- профильные тесты Patch 011.7: 10/10; тесты импортера 011.6.2: 21/21;
- следующий существующий regression-тест оперативного журнала остановился на
  cache-busting contract: `base.html` содержал `app.css?v=011700`, а константа
  `SYSTEM_CSS_REVISION` оставалась `011610`;
- обе runtime DB восстановлены из проверенных backup;
- все 35 файлов откатаны, worktree после rollback clean; commit не создавался;
- Revision 8 включает существующий тест в payload и backup-контракт, синхронизирует
  CSS revision и проверяет её согласованность до дорогостоящих миграций.

## Patch 011.7 Repair 1 Revision 8

- запуск: 23.07.2026 23:10:15 +03:00;
- Ruff, compileall, static gate, Django checks и чистая миграция прошли;
- ранние runtime asset tests: 4/4;
- профильные тесты Patch 011.7: 10/10;
- тесты импортера 011.6.2: 21/21;
- targeted dependencies: 173/173, один skipped;
- discovery: 495 тестов;
- полный suite выявил один устаревший smoke-контракт главной страницы: тест ожидал `Базовые реестры готовы к демонстрации`, тогда как Patch 011.7 намеренно заменил hero на `Единое ядро оперативной документации готово к наполнению`;
- параллельный runner дополнительно скрыл нормальный traceback из-за отсутствия `tblib`;
- обе runtime DB восстановлены, все файлы откатаны, rollback clean, commit не создан.

## Patch 011.7 Repair 1 Revision 9

- запуск: 23.07.2026 23:29:05 +03:00;
- исходный HEAD: `b73510a5b64b4f7faf9d80996c8ad3dba4822d6f`;
- лог: `patch_011_7_repair1_revision9_operational_documentation_core_20260723_232905.log`;
- Ruff, compileall, static gate, system smoke 2/2, runtime assets 4/4, профильные тесты 011.7 10/10, импортер 21/21 и targeted-набор 173/173 прошли;
- полный последовательный suite: 495/495, один skipped;
- миграции presentation и development БД и обе профильные диагностики прошли;
- отказ произошёл перед commit на `git diff --cached --check`: четыре trailing whitespace в `ADR-011-7-operational-documentation-core.md` и `CURRENT_STATE.md`;
- обе runtime DB восстановлены из проверенных backup, все файлы откатаны, worktree после rollback clean, commit не создавался;
- Revision 10 нормализует trailing whitespace во всём текстовом payload и проверяет его в preflight до backup и применения изменений.
