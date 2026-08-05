#!/usr/bin/env python3
from pathlib import Path

from demo_release_plan import validate_repository

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    errors = validate_repository(ROOT)
    if errors:
        print("Demo release / industrialization state contract: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Demo release / industrialization state contract: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
