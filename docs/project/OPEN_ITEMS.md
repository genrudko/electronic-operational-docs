# ЭОД — открытые вопросы и отложенные задачи

**Актуализировано:** 28.07.2026

## Current active item — DEV-FAST-001

```text
issue:
#18 — Trusted hot refresh from PR comment

branch:
infra/dev-fast-001-hot-refresh

state:
IMPLEMENTATION IN DRAFT PR / NOT MERGED / NOT ACTIVATED
```

### Fixed V1 decisions

- trigger: exact main-controlled PR conversation comment;
- command: `/eod-hot-refresh <exact-head-sha>`;
- gateway: one added command `hot-refresh <pr> <sha> <run_id>`;
- paths: only `src/templates/**` and `src/static/**`;
- statuses: only added and modified;
- Git objects: only regular `100644` blobs;
- deletions, renames, copies, type changes, symlinks and executable blobs: forbidden;
- runtime: writable layer of the current `eod-development` app container only;
- refresh: app restart, host-owned collectstatic/check entrypoint, local health;
- rollback: force-recreate app from current full image;
- marker: separate file inside the app container, not deployment `current_sha`;
- database, migrations, image build, Compose, presentation reset and preview: untouched;
- normal release transaction model: unchanged;
- concurrency: existing GitHub group and controller `flock`;
- automatic merge: absent.

### Remaining DEV-FAST-001 gates

1. Focused workflow/validator/controller tests on the final PR head.
2. One final full security/code gate before merge.
3. Explicit user merge authorization.
4. One controlled root activation of only `/usr/local/sbin/eod-development-controller` from accepted exact `main`.
5. Presentation-only canary PR proving success, idempotency and rollback.
6. Development health and preview-untouched evidence.

## Deferred and out of scope

- deletions or renames in hot refresh;
- executable or generated presentation artifacts;
- persistent host-side overlay transactions or backups;
- generic overlay engine;
- CI-OPT-001;
- HTTPS/nginx/Certbot;
- public preview changes;
- product business logic, models or migrations.

## Product backlog after DEV-FAST-001

- minimal reusable UX/UI foundation based on the accepted equipment defect journal;
- PRODUCT-D2 — Журнал заявок;
- PRODUCT-D3 — Журнал распоряжений;
- Operational Journal lifecycle and editor stabilization;
- later source-bound journals and normative work-permit decisions.
