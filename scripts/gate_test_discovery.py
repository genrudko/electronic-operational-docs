
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")

import django  # noqa: E402
from django.test.runner import DiscoverRunner  # noqa: E402

django.setup()

runner = DiscoverRunner(verbosity=2, interactive=False)
suite = runner.build_suite(test_labels=["apps.system.tests"])
count = suite.countTestCases()

print(f"DISCOVERED_TEST_COUNT={count}")
if count < 2:
    raise SystemExit(
        f"Expected at least 2 tests, discovered {count}."
    )

failures = runner.run_tests(["apps.system.tests"])
if failures:
    raise SystemExit(f"Test suite failed: {failures} failure(s).")

print("PATCH_001_5_TEST_DISCOVERY_GATE_PASSED")
