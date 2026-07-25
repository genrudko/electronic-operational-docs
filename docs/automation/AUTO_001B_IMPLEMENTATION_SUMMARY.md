# AUTO-001B — Restricted VPS Controller

```text
status: Draft PR candidate
base: b9fe794955af33843aee9b553ae73c06352e0929
VPS operations before merge: none
preview impact: none
application baseline impact: none
merge: requires separate explicit user decision
```

AUTO-001B installs one restricted root-owned development controller after merge. It verifies exact PR SHA using an isolated PostgreSQL test database, backs up `eod_development` before migrations, updates only the development contour and restores the previous database/image on failure or stale SHA.

User actions after merge:

1. run `sudo bash deploy/automation/bootstrap_auto001b.sh` on the VPS;
2. add the printed public Deploy Key with write access disabled;
3. rerun bootstrap and add the four printed GitHub Actions secrets;
4. run one safe unmerged canary PR.

No automatic merge is implemented.
