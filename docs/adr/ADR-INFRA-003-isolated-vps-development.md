# ADR-INFRA-003: Isolated VPS development contour

- Status: proposed
- Date: 2026-07-24
- Baseline: `main / ded4571dcacd973184d3121b19c8db8c70e7b08a / INFRA-002 accepted`

## Context

The accepted private preview now runs continuously on the VPS from `/srv/eod/repository`, branch `main`, with PostgreSQL and the application exposed only through `127.0.0.1:8765`.

The previous development workflow still depended on a Windows workstation for Python, SQLite, patch execution, visual testing, and snapshot creation. The user needs to be able to apply and verify assistant-generated patches from Termux on a smartphone without risking the accepted preview.

Using the preview checkout as a development worktree would couple incomplete code, migrations, and data changes to the demonstration environment. A second isolated contour is therefore required.

## Decision

Create a separate VPS development contour with these fixed roles:

- checkout: `/srv/eod/development`;
- Compose project: `eod-development`;
- active branch: any explicit working branch, never `main`;
- application port: `127.0.0.1:8766`;
- PostgreSQL database and user: `eod_development`;
- secrets: `/srv/eod/secrets/development.env`;
- independent PostgreSQL named volume and Docker networks;
- source bind mounts for `manage.py` and `src` so ordinary code patches do not require image rebuilds;
- Django development server with automatic source reload;
- fail-closed startup validation for the exact development database, user, host, port, profile, deployment mode, and SQLite override;
- repository-owned controller for bootstrap, refresh, rebuild, checks, tests, migrations, status, logs, and shutdown;
- repository-owned reset operation that copies accepted preview data into development only after creating a development backup and verifying both checkout roles.

The existing preview remains unchanged:

- checkout: `/srv/eod/repository`;
- branch: `main`;
- Compose project: `eod-preview`;
- port: `127.0.0.1:8765`;
- PostgreSQL database: `eod_preview`.

The VPS GitHub deploy key remains read-only. Pull requests, merge operations, tags, and other repository writes are not performed from the VPS.

## Patch workflow

The user may download an autonomous patch on Android, upload it through Termux/SCP to `/srv/eod/patches`, apply it in `/srv/eod/development`, and refresh the development application.

Code-only patches use the bind-mounted source and do not rebuild dependencies. Changes to dependencies, Dockerfiles, or startup scripts require the explicit `rebuild` command.

The application is inspected through an SSH local-forward tunnel to port `8766` in any browser on the client device.

## Safety properties

- Development startup refuses `main` through the controller.
- Development startup refuses the preview database name and user.
- Preview and development Compose projects have separate names, networks, containers, and volumes.
- Neither PostgreSQL port is exposed on the host.
- Development database reset validates preview=`main`, development!=`main`, and distinct exact database names before any restore.
- Development reset backs up the previous development database before replacing it.
- Development reset is read-only with respect to preview PostgreSQL.

## Consequences

### Positive

- The Windows workstation is no longer required for routine patch execution, Django runtime, PostgreSQL, tests, or visual verification.
- Termux becomes a viable operational client for the development workflow.
- Runtime parity improves because development and preview both use Linux, Docker, Python 3.13, and PostgreSQL 18.
- Incomplete migrations or broken UI changes cannot directly damage the accepted preview.
- Development data can be reset from the accepted presentation state reproducibly.

### Negative

- The VPS now runs a second PostgreSQL/application stack and consumes additional memory and disk space.
- Development remains reachable only through an SSH tunnel; this is intentional.
- A phone is sufficient for patch application and browser checks but is less comfortable for long log review or desktop-layout inspection.
- Local dirty changes on the VPS cannot be pushed with the read-only deploy key and must be reconciled through the controlled integration workflow.

## Out of scope

- Public domain, HTTPS, or reverse proxy for development;
- browser IDE or code-server;
- write-capable GitHub credentials on the VPS;
- automatic merge or deployment to preview;
- production monitoring;
- shared multi-developer environment.
