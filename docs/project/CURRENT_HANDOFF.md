# CHAT 0 — CURRENT HANDOFF

**Проект:** Электронная оперативная документация (ЭОД)  
**Репозиторий:** `genrudko/electronic-operational-docs`  
**Дата handoff:** 28.07.2026

## Непереговорные правила

- GitHub — единственный источник кода и canonical documentation.
- VPS — единственный runtime/test-контур.
- Пользователь не редактирует код и не выполняет штатные VPS-команды для функциональных PR.
- Preview не используется для разработки и не изменяется без отдельного решения.
- Automatic merge запрещён; merge выполняется только по отдельной явной команде пользователя.
- Применяется принцип минимально достаточного решения и риск-ориентированный объём проверок.

## Accepted baseline

```text
Accepted application baseline:
937d2cd2b187c17fac3088ccfc52079fc4608306

last accepted product merge:
DEFECT-001 / PR #16
883a108c8be2a8cd075846fdd175916917911ef6

main at DEV-FAST-001 start:
54990c386c40dd7bd854330e61ed7285649ef120
```

## Active work item

```text
issue:
#18 — DEV-FAST-001: Trusted hot refresh from PR comment

branch:
infra/dev-fast-001-hot-refresh

PR:
DRAFT / NOT MERGED

scope:
presentation-only V1
```

DEV-FAST-001 adds one main-controlled `issue_comment:created` workflow and one new forced-gateway command:

```text
hot-refresh <pr> <sha> <run_id>
```

The command accepts only exact live same-repository open PR heads and only added/modified `100644` blobs under `src/templates/**` and `src/static/**`. Deletions, renames, copies, symlinks and executable blobs are rejected both in GitHub validation and independently on the VPS.

The controller uses the existing repository cache, read-only deploy key, forced SSH account, host-owned Compose, current full development image, app-only restart, collectstatic entrypoint, local health-check and global controller lock. Existing release transactions are not generalized or changed.

On any runtime failure the development app is force-recreated from the current full image. Database, migrations, image build, presentation seed and preview are untouched. The overlay marker lives only inside the writable app-container layer and does not modify `current_sha`.

## Gate sequence

1. Implement and run focused validator/controller contract tests in the Draft PR.
2. Run one final full security/code gate on the final exact PR head.
3. Merge only after an explicit user command.
4. From the accepted exact `main`, perform one controlled root install of only the controller file.
5. Create a presentation-only canary PR.
6. Prove SUCCESS, repeated-command idempotency and controlled rollback.
7. Confirm development health and preview untouched.

Before controller activation, the new comment workflow is not operational. No labels, automatic merge or preview deployment are introduced.
