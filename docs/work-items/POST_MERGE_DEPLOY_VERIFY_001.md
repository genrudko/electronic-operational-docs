# POST-MERGE-DEPLOY-VERIFY-001 — execution package

**Issue:** #44

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

## FACTUAL BLOCKER

Trusted controller принимает запрос только от открытого same-repository PR.
Попытка повторного запуска из merged PR #43 была отклонена policy gate:

```text
AUTO-001B BLOCKED: Pull request must still be open.
run: 30761934328
```

Поэтому этот Draft PR является только post-merge deployment carrier. Он начинается
точно от merge commit PR #43 и не изменяет product code, schema, migrations,
workflow или controller.

## ALLOWED BOUNDARY

```text
docs/work-items/POST_MERGE_DEPLOY_VERIFY_001.md
docs/project/CURRENT_STATE.md
PR / issue coordination metadata
trusted full-development rebuild
```

## FORBIDDEN BOUNDARY

- product/runtime source changes;
- schema or migration changes;
- workflow/controller changes;
- preview write;
- automatic merge;
- merge этого carrier PR без отдельной команды пользователя.

## DELIVERY

```text
change class: STANDARD
risk profile: DOCS
runtime delivery: FULL_DEVELOPMENT (explicit verification request)
preview: UNTOUCHED
```

## ACCEPTANCE

- пять exact-head workflows успешны;
- trusted controller использует exact carrier head;
- carrier tree содержит принятый merge commit PR #43;
- VPS tests завершены успешно;
- live SHA совпадает с requested SHA;
- migrations/system check/health успешны;
- rollback отсутствует;
- пользователь получает acceptance routes для проверки.
