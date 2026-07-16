from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
os.environ.setdefault("DB_ENGINE", "sqlite")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
os.environ.setdefault("PYTHONUTF8", "1")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")

import django  # noqa: E402
from django.test.runner import DiscoverRunner  # noqa: E402

django.setup()

TEST_LABELS = [
    "apps.system.tests",
    "apps.organizations.tests",
    "apps.documents.tests",
    "apps.normatives.tests",
    "apps.equipment.tests",
    "apps.dispatching.tests",
    "apps.imports.tests",
]
MIN_TEST_COUNT = 267

runner = DiscoverRunner(verbosity=2, interactive=False)
suite = runner.build_suite(test_labels=TEST_LABELS)
count = suite.countTestCases()

print(f"DISCOVERED_TEST_COUNT={count}")
if count < MIN_TEST_COUNT:
    raise SystemExit(f"Expected at least {MIN_TEST_COUNT} tests, discovered {count}.")

failures = runner.run_tests(TEST_LABELS)
if failures:
    raise SystemExit(f"Test suite failed: {failures} failure(s).")

print("PATCH_008_4_TEST_DISCOVERY_GATE_PASSED")
