from __future__ import annotations

import check_demo_release_plan
import check_documentation_contract_core as core


def main() -> int:
    result = core.main()
    if result:
        return result
    return check_demo_release_plan.main()


if __name__ == "__main__":
    raise SystemExit(main())
