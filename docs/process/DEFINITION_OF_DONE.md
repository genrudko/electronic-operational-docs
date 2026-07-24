# ЭОД — Definition of Done

Work item считается завершённым только после выполнения всех применимых требований.

## Scope

- [ ] цель и границы определены;
- [ ] acceptance criteria сформулированы;
- [ ] связанные domain invariants проверены;
- [ ] out-of-scope явно указан;
- [ ] data and migration impact оценены.

## Implementation

- [ ] change выполнен в отдельной branch;
- [ ] code complete, без placeholders и ручных шагов пользователя;
- [ ] migrations согласованы с models;
- [ ] tests покрывают positive and negative paths;
- [ ] presentation data обновлены, если это нужно сценарию;
- [ ] canonical docs обновлены в той же ветке;
- [ ] secrets and real data отсутствуют.

## Automated gates

- [ ] diff checked;
- [ ] Ruff success;
- [ ] compileall success;
- [ ] Django check success;
- [ ] migration consistency success;
- [ ] PostgreSQL migrations success;
- [ ] profile gates success;
- [ ] full current test suite success;
- [ ] container/documentation/security gates success, если применимы;
- [ ] current exact head has green CI.

## VPS development

- [ ] active branch and exact head verified;
- [ ] worktree clean;
- [ ] refresh/rebuild complete;
- [ ] app and db healthy;
- [ ] database identity correct;
- [ ] health endpoint success;
- [ ] main page HTTP 200;
- [ ] preview remains unaffected;
- [ ] migrations/data reset verified, если применимо.

## Acceptance

- [ ] пользователь прошёл заданный scenario;
- [ ] предметная логика подтверждена;
- [ ] UX and visual result accepted;
- [ ] regressions checked;
- [ ] known limitations recorded;
- [ ] follow-up defects captured;
- [ ] explicit merge permission received.

## Merge and release

- [ ] expected head SHA used;
- [ ] PR merged;
- [ ] merge commit recorded;
- [ ] preview checkout synchronized;
- [ ] required backup/migrations/rebuild completed;
- [ ] post-merge preview health success;
- [ ] accepted baseline updated;
- [ ] current state/handoff/baseline/acceptance/release notes updated.

## Неприменимые пункты

Пункт может быть отмечен `N/A` только с объяснением в PR. Пропуск без объяснения не считается выполнением.

## Technical success vs acceptance

Зелёный CI означает только техническую готовность к следующему gate. Work item не становится `done`, пока пользователь не подтвердил результат и accepted preview не проверен после merge.