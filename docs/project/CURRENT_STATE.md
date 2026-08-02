# ЭОД — текущее состояние

**Дата factual check:** 02.08.2026

**Единственный владелец:** accepted main baseline, active work item/issue/PR/branch
и runtime state.

```text
repository: genrudko/electronic-operational-docs
accepted main baseline: main / 2a2013a51bfdc9de602b095adcb28a51b8d4487e
active work item: POST-MERGE-DEPLOY-VERIFY-001
active issue: #44
active PR: #45 / OPEN / DRAFT / NOT MERGED
active branch: ops/post-merge-deploy-verify-001
runtime impact: DEVELOPMENT
preview: UNTOUCHED
```

`PERSONNEL-AUTHORITY-001` принят и merged обычным merge commit:

```text
accepted PR: #43 / CLOSED / MERGED
accepted exact head: d659ab949db2942c064eec3c298d031a9684c67d
merge commit: 2a2013a51bfdc9de602b095adcb28a51b8d4487e
issue: #42 / CLOSED / COMPLETED
```

Принятый baseline включает:

- structured personnel authority grants и action-time `ALLOW / DENY / VERIFY`;
- организационную структуру, матрицу прав и карточки сотрудников;
- ручное создание, редактирование, versioned rights/qualifications и деактивацию;
- controlled XLSX preview/publish;
- внешние оперативные справочники и contractor semantics;
- Onest Variable как фирменную интерфейсную гарнитуру;
- принятый логотип ЭОД и canonical EOD Outline 24 iconography;
- узкий принятый repair выключателя, заземляющего разъединителя, переносного
  заземления и приёма/передачи смены.

До merge все пять обязательных workflows на accepted head были успешны. Preview
не затрагивался.

## Active post-merge verification

Пользователь потребовал развернуть и проверить принятый результат на VPS.
Trusted controller не допускает запрос из merged PR: run `30761934328` был
заблокирован точной причиной:

```text
AUTO-001B BLOCKED: Pull request must still be open.
```

Поэтому Draft PR #45 создан от точного merge commit `main` как same-repository
deployment carrier.

Первый carrier head `0a48cfc484a2917fd0f76c32bb9750a7c5e96a2c` прошёл пять
mandatory workflows. Trusted run `30762341525` затем подтвердил validation,
image build, Django checks и отсутствие migration drift, но isolated VPS suite
остановился на одном repository-only test:

```text
tests discovered: 675
failed: 1
skipped: 1
primary cause: /app/docs/ux/EQUIPMENT_PICTOGRAM_GOST_BASIS_V1.md absent
live deployment: NOT APPLIED
pending development transaction: NONE
previous development runtime: PRESERVED
```

Development image намеренно содержит executable source, но не repository docs.
Исправление ограничено тестовым контрактом: Markdown boundary остаётся
обязательным в repository CI, а в runtime image пропускается как repository-only.
Product behavior, SVG catalog, schema, migrations, workflow и controller не
меняются.

Следующий обязательный порядок:

```text
5 exact-head workflows after test-boundary repair
→ trusted full-development rebuild
→ VPS tests and migrations summary
→ Django system check and health-check
→ LIVE_SHA = exact PR #45 head
→ preview UNTOUCHED
→ user acceptance
```

Merge PR #45 без отдельной прямой команды пользователя запрещён.

Release/module/capability/work-item planning state остаётся в
[`DEMO_RELEASE_PLAN.yaml`](DEMO_RELEASE_PLAN.yaml). Navigation без дублирования
volatile values остаётся в [`CURRENT_HANDOFF.md`](CURRENT_HANDOFF.md).
