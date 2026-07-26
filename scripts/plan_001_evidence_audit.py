#!/usr/bin/env python
from __future__ import annotations

import traceback

from apps.system.plan_001_audit.cli import main

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        raise SystemExit(1) from None
