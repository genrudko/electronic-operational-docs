#!/usr/bin/env python
from __future__ import annotations

import os
import secrets
import sys
from pathlib import Path


def _inject_process_local_test_demo_credential() -> None:
    if len(sys.argv) < 2 or sys.argv[1] != "test":
        return
    if os.environ.get("EOD_DEMO_USER_PASSWORD", "").strip():
        return
    os.environ["EOD_DEMO_USER_PASSWORD"] = "Tt1!" + secrets.token_urlsafe(32)


def main() -> None:
    root = Path(__file__).resolve().parent
    sys.path.insert(0, str(root / "src"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
    _inject_process_local_test_demo_credential()
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
