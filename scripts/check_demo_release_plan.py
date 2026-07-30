#!/usr/bin/env python3
from demo_release_plan import load, validate


def main() -> int:
    errors = validate(load())
    if errors:
        print("Demo release plan contract: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    print("Demo release plan contract: OK")
    print("Modules: 27")
    print("Reference rows: 66")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
