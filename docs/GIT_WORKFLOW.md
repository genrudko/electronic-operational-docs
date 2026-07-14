
# Git workflow

## Repository

- Branch: `main`
- GitHub: `genrudko/electronic-operational-docs`
- Visibility: private

## Mandatory rule

A patch is committed and pushed only after every functional and quality gate passes.

- Failed gate: no commit and no push.
- Successful commit but failed push: the local commit remains and the error is logged.
- One successful patch or repair patch: one commit.
- Force-push to `main` is prohibited.
- A test command that discovers zero tests is a failed gate.

## Standard finalization helper

The main patch normally invokes this helper itself. Manual use:

```powershell
.\.venv\Scripts\python.exe scripts\git_finalize_patch.py `
  --root "G:\\electronic-operational-docs" `
  --patch-id "patch_002_organizational_core" `
  --message "Add organizational core"
```

The helper:

1. runs `git diff --check`;
2. stages changes;
3. blocks secrets, local databases, logs, backups and key files;
4. scans staged text for GitHub tokens and private keys;
5. creates a commit;
6. pushes `main` to `origin`.
