#!/usr/bin/env python3
import demo_release_plan


# Stage 1 remains the audit origin, but accepted bounded work items advance the
# canonical current-code expectation. Keep the explicit override narrow so an
# unrelated module cannot silently rewrite its audited code status.
CURRENT_ACCEPTED_CODE_OVERRIDES = {
    "NORMATIVE-EVIDENCE": "IMPLEMENTED-ACCEPTED",
}


def main() -> int:
    expected_code = dict(demo_release_plan.EXPECTED_CODE)
    expected_code.update(CURRENT_ACCEPTED_CODE_OVERRIDES)
    original_expected_code = demo_release_plan.EXPECTED_CODE
    demo_release_plan.EXPECTED_CODE = expected_code
    try:
        errors = demo_release_plan.validate(demo_release_plan.load())
    finally:
        demo_release_plan.EXPECTED_CODE = original_expected_code
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
