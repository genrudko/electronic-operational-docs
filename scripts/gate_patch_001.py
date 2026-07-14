from __future__ import annotations

import compileall
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

EXPECTED = [
    "pyproject.toml",
    "compose.yaml",
    "manage.py",
    "src/eod_config/settings.py",
    "src/apps/system/views.py",
    "src/apps/system/tests.py",
    "src/templates/system/home.html",
    "src/static/system/app.css",
    "docs/FINAL_DEVELOPMENT_PLAN.md",
]

missing = [item for item in EXPECTED if not (ROOT / item).is_file()]
if missing:
    print("GATE FAILED: отсутствуют файлы:")
    for item in missing:
        print(" -", item)
    raise SystemExit(1)

if not compileall.compile_dir(ROOT / "src", quiet=1):
    print("GATE FAILED: ошибка компиляции Python")
    raise SystemExit(1)

print("Static gate: OK")
print("Expected files:", len(EXPECTED))
print("Python:", sys.version.split()[0])
print("PATCH_001_STATIC_GATE_PASSED")
