# ЭОД — текущее состояние

**Дата проверки:** 28.07.2026

```text
repository:
genrudko/electronic-operational-docs

accepted application baseline:
main / 937d2cd2b187c17fac3088ccfc52079fc4608306

current main at work-item start:
54990c386c40dd7bd854330e61ed7285649ef120

last accepted product work item:
DEFECT-001 / PR #16 / MERGED / ACCEPTED

active work item:
DEV-FAST-001 — Trusted hot refresh from PR comment

active branch:
infra/dev-fast-001-hot-refresh

active PR:
DRAFT / NOT MERGED
```

## Accepted runtime boundary

- GitHub is the only source of code and canonical documentation.
- VPS is the only runtime contour.
- Accepted preview remains `eod-preview`, PostgreSQL `eod_preview`, loopback port `8765`.
- Active development remains `eod-development`, PostgreSQL `eod_development`, loopback port `8766`.
- The restricted account remains `eod-automation` with the existing forced SSH gateway.
- The fixed host controller remains `/usr/local/sbin/eod-development-controller`.
- Host-owned Compose, Dockerfile, entrypoint, keys, sudoers and secrets are unchanged.
- Automatic merge is absent. Preview is not a development target.

## DEV-FAST-001 V1 contract

The trusted workflow is loaded only from `main` and accepts an exact PR comment:

```text
/eod-hot-refresh <exact-lowercase-40-hex-sha>
```

It permits only added or modified regular non-executable blobs under:

```text
src/templates/**
src/static/**
```

V1 rejects deletions, renames, copies, type changes, symlinks, executable blobs, forks, closed PRs, non-main bases, stale SHA and actors without write/admin authority.

The existing controller independently fetches `refs/pull/<number>/head`, verifies the exact SHA and applies files only to the writable layer of the current `eod-development` app container. It restarts only the app; the host-owned entrypoint performs Django check and collectstatic. A local health-check is mandatory.

No image build, PostgreSQL test suite, database backup, migration, presentation seed, Compose change or preview operation occurs during hot refresh.

On any apply/restart/health/stale-ref failure, the app container is force-recreated from its current full deployment image. The simple overlay marker is stored inside the app container and therefore disappears on the next ordinary full deployment.

## Activation boundary

The issue-comment workflow cannot become trusted until merged into `main`. After merge, one controlled root activation installs only the reviewed controller file over `/usr/local/sbin/eod-development-controller`. Full bootstrap of keys, sudoers, Compose and secrets is not repeated because their contract is unchanged.

Runtime activation and canary evidence are pending. Until then DEV-FAST-001 is implemented in source but not operationally accepted.
