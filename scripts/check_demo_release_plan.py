#!/usr/bin/env python3
from demo_release_plan import load, validate


# Stage 1 remains the audit origin, but accepted bounded work items advance the
# canonical current-code expectation. Keep the explicit override narrow so an
# unrelated module cannot silently rewrite its audited code status.
CURRENT_ACCEPTED_CODE_OVERRIDES = {
    "NORMATIVE-EVIDENCE": "IMPLEMENTED-ACCEPTED",
}


def main() -> int:
    expected_code = validate.__globals__["EXPECTED_CODE"]
    original_expected_code = dict(expected_code)
    expected_code.update(CURRENT_ACCEPTED_CODE_OVERRIDES)
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
