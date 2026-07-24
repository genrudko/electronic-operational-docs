# ЭОД — Git workflow

## Репозиторий

```text
genrudko/electronic-operational-docs
visibility: private
default branch: main
```

## Ветки

- `main` — только принятый baseline;
- work item — отдельная branch от актуального `main`;
- branch naming: `<type>/<number>-<short-name>`;
- development checkout никогда не работает на `main`;
- stale branch перед новой работой синхронизируется с current accepted baseline.

## Commits

- commit создаёт AI-разработчик через GitHub;
- commit message описывает результат, а не действие «update files»;
- repair commits остаются в том же PR, если scope не изменился;
- пользователь не выполняет commit/push вручную;
- VPS использует read-only deploy key и только fetch/pull.

## Pull request

Каждый work item проходит PR. В PR фиксируются:

- цель и scope;
- base/head SHA;
- changed areas;
- migrations/data impact;
- tests and CI runs;
- VPS evidence;
- user acceptance;
- limitations;
- explicit merge permission;
- merge commit and post-merge gate.

## Merge

- direct push to `main` запрещён;
- force-push to `main` запрещён;
- merge выполняется только после явного разрешения пользователя;
- expected head SHA обязателен для значимого PR;
- предпочтительный метод по умолчанию — merge commit, если отдельно не принято squash/rebase;
- documentation-only branch с множеством технических file commits может быть squash merged по явному решению, чтобы сохранить один логический change в `main`.

## Tags

Tag создаётся для устойчивого принятого рубежа. Он не заменяет merge commit и не создаётся до post-merge verification.

## Запрещённые файлы

- `.env`, keys, tokens;
- databases and dumps;
- logs and backups;
- real enterprise documents/data;
- context archives containing sensitive material.

## History rewrite

History rewrite запрещён. Исключение возможно только для удаления уже попавшего секрета или чувствительных данных после отдельного решения и обязательной ротации скомпрометированных credentials.

## Локальные checkout

Локальный Windows checkout не является обязательным для разработки и не считается источником истины. Source of truth — GitHub branch and accepted `main`.

## Связанные документы

- `BRANCH_AND_PR_POLICY.md`;
- `RELEASE_PROCESS.md`;
- `../project/BASELINE_HISTORY.md`;
- `../../AGENTS.md`.