from __future__ import annotations

import importlib.util
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "scripts/git_finalize_patch.py"

spec = importlib.util.spec_from_file_location("eod_git_finalize", HELPER_PATH)
if spec is None or spec.loader is None:
    raise SystemExit("Cannot load Git finalization helper.")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)

for path in (
    "src/apps/system/views.py",
    "scripts/gate_patch_006_2_repository_security.py",
    "docs/adr/ADR-006-2-repository-history-sanitization.md",
    "README.md",
):
    if not helper.in_allowlist(path):
        raise SystemExit(f"Expected allowlisted path was rejected: {path}")

for path in (
    "Инструкции/оперативная инструкция.docx",
    "ChatGPT-export.md",
    "EOD_full_project_plan_v2_1_ru.md",
    "docs/real-document.pdf",
    "logs/patch.log",
    ".env",
):
    if not helper.blocked(path):
        raise SystemExit(f"Sensitive path was not blocked: {path}")

try:
    helper.validate_allowlisted(["foreign-material.txt"])
except RuntimeError:
    pass
else:
    raise SystemExit("Tracked foreign path unexpectedly passed the allowlist.")


def run(command: list[str]) -> str:
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(
            f"Command failed ({result.returncode}): {' '.join(command)}\n"
            f"{result.stdout}\n{result.stderr}"
        )
    return result.stdout


history = run(["git", "log", "--all", "--name-only", "--pretty=format:", "-z"])
history_paths = [path.replace("\\", "/") for path in history.split("\0") if path]
for path in history_paths:
    if helper.blocked(path):
        raise SystemExit(f"Blocked path remains in reachable Git history: {path}")

tracked = run(["git", "ls-files", "-z"])
tracked_paths = [path.replace("\\", "/") for path in tracked.split("\0") if path]
for path in tracked_paths:
    if helper.blocked(path):
        raise SystemExit(f"Blocked path remains tracked: {path}")

helper.verify_repository(ROOT)
helper.verify_private_repository(ROOT)

print(f"REACHABLE_HISTORY_PATH_COUNT={len(set(history_paths))}")
print("REPOSITORY_VISIBILITY_PRIVATE=PASSED")
print("FULL_STAGED_PATH_ALLOWLIST=PASSED")
print("SENSITIVE_HISTORY_PATHS_REMOVED=PASSED")
print("PATCH_006_2_REPOSITORY_HISTORY_SECURITY_GATE_PASSED")
