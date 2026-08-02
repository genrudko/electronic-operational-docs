# POST-MERGE-DEPLOY-VERIFY-001 — execution package

**Issue:** #44

**PR:** #45

**Branch:** `ops/post-merge-deploy-verify-001`

**Starting main:** `2a2013a51bfdc9de602b095adcb28a51b8d4487e`

## GOAL

Развернуть на isolated development VPS принятый результат
`PERSONNEL-AUTHORITY-001` после merge PR #43 и подтвердить:

- exact deployed SHA;
- применение актуальных migrations;
- полный VPS test profile;
- Django system check и health-check;
- отсутствие rollback;
- preview `UNTOUCHED`.

## CLOSED-PR POLICY BLOCKER

Trusted controller принимает запрос только от открытого same-repository PR.
Попытка повторного запуска из merged PR #43 была отклонена policy gate:

```text
AUTO-001B BLOCKED: Pull request must still be open.
run: 30761934328
```

Поэтому Draft PR #45 является post-merge deployment carrier и начинается точно
от merge commit PR #43.

## FIRST CARRIER DEPLOYMENT ATTEMPT

Exact carrier head `0a48cfc484a2917fd0f76c32bb9750a7c5e96a2c` прошёл пять
mandatory workflows, но trusted run `30762341525` остановился на isolated VPS
suite:

```text
validation job: SUCCESS
image build: SUCCESS
Django system check: SUCCESS
migration drift: NONE
tests discovered: 675
passed before failure: 674
error: FileNotFoundError /app/docs/ux/EQUIPMENT_PICTOGRAM_GOST_BASIS_V1.md
live deployment: NOT APPLIED
pending transaction: NONE
previous development runtime: PRESERVED
```

Причина: runtime image намеренно содержит `src`, но не repository documentation.
Один repository contract-test ошибочно считал Markdown-файл runtime dependency.
Product logic, SVG catalog и migrations не падали.

## MINIMAL REPAIR

`test_gost_boundary_is_documented_without_false_compliance_claim` остаётся
обязательным в repository CI, где `docs/ux/**` присутствует. В минимальном
runtime image он честно пропускается как repository-only check. Все executable
SVG semantics продолжают проверяться VPS-тестами.

## ALLOWED BOUNDARY

```text
docs/work-items/POST_MERGE_DEPLOY_VERIFY_001.md
docs/project/CURRENT_STATE.md
src/apps/organizations/tests/test_iconography_refinement_contract.py
PR / issue coordination metadata
trusted full-development rebuild
```

## FORBIDDEN BOUNDARY

- product behavior changes;
- schema or migration changes;
- workflow/controller changes;
- inclusion всей repository documentation в runtime image;
- preview write;
- automatic merge;
- merge этого carrier PR без отдельной команды пользователя.

## DELIVERY

```text
change class: STANDARD
risk profile: TEST_CONTRACT
runtime delivery: FULL_DEVELOPMENT (explicit verification request)
preview: UNTOUCHED
```

## ACCEPTANCE

- пять exact-head workflows успешны после repair;
- repository CI реально проверяет GOST-boundary Markdown;
- runtime suite пропускает только отсутствующий repository-only Markdown;
- trusted controller использует exact carrier head;
- carrier tree содержит принятый merge commit PR #43;
- VPS tests завершены успешно;
- live SHA совпадает с requested SHA;
- migrations/system check/health успешны;
- rollback отсутствует;
- пользователь получает acceptance routes для проверки.
