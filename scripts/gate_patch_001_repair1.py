from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

expected = [
    "src/eod_config/settings.py",
    "src/apps/system/views.py",
    "src/apps/system/tests.py",
    "src/templates/system/home.html",
    "scripts/run_dev.ps1",
    "scripts/run_postgres.ps1",
    "docs/adr/ADR-001-local-sqlite-profile.md",
]

missing = [item for item in expected if not (ROOT / item).is_file()]
if missing:
    print("GATE FAILED: отсутствуют файлы")
    for item in missing:
        print(" -", item)
    raise SystemExit(1)

settings_text = (ROOT / "src/eod_config/settings.py").read_text(encoding="utf-8")
required_markers = [
    'DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")',
    "django.db.backends.sqlite3",
    "django.db.backends.postgresql",
    "load_env_file(BASE_DIR / \".env\")",
]
for marker in required_markers:
    if marker not in settings_text:
        print("GATE FAILED: отсутствует marker", marker)
        raise SystemExit(1)

env_text = (ROOT / ".env").read_text(encoding="utf-8")
if "DB_ENGINE=sqlite" not in env_text:
    print("GATE FAILED: .env не переключён на SQLite")
    raise SystemExit(1)

os.environ["DB_ENGINE"] = "sqlite"
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.db import connection  # noqa: E402

if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
    print("GATE FAILED: активен не SQLite")
    raise SystemExit(1)

with connection.cursor() as cursor:
    cursor.execute("SELECT 1")
    if cursor.fetchone() != (1,):
        print("GATE FAILED: SELECT 1")
        raise SystemExit(1)

print("Database vendor:", connection.vendor)
print("PATCH_001_REPAIR1_GATE_PASSED")
