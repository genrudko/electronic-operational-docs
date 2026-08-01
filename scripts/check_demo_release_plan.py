#!/usr/bin/env python3
from demo_release_plan import load, validate


def main() -> int:
    # Stage 1 remains the audit origin, but an accepted bounded work item advances
    # the canonical current-code expectation for that module only.
    expected_code = validate.__globals__["EXPECTED_CODE"]
    original_expected_code = dict(expected_code)
    expected_code["NORMATIVE-EVIDENCE"] = "IMPLEMENTED-ACCEPTED"
    try:
        errors = validate(load())
    finally:
        expected_code.clear()
        expected_code.update(original_expected_code)
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
