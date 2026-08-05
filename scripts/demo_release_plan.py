#!/usr/bin/env python3
"""Public entry point for canonical planning-state validation and generation."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    from .module_contract_status_projection import (
        validate_module_contract_status_projections,
    )
    from .release_plan_compat_validation import (
        validate_release_plan_compatibility,
    )
    from .release_plan_model import PROGRAM_PATH, ROOT, load_plan, load_program
    from .industrialization_execution import (
        load_raw as load_execution_raw,
        render_execution_backlog,
        validate_execution_contract,
        validate_execution_view,
    )
    from .release_plan_validation import (
        validate_repository as validate_industrialization_repository,
    )
    from .release_plan_views import (
        render_checklist,
        render_module_map,
        render_program_markdown,
        render_sequence,
    )
except ImportError:
    repository_root = str(Path(__file__).resolve().parents[1])
    if repository_root not in sys.path:
        sys.path.insert(0, repository_root)
    from scripts.module_contract_status_projection import (
        validate_module_contract_status_projections,
    )
    from scripts.release_plan_compat_validation import (
        validate_release_plan_compatibility,
    )
    from scripts.release_plan_model import PROGRAM_PATH, ROOT, load_plan, load_program
    from scripts.industrialization_execution import (
        load_raw as load_execution_raw,
        render_execution_backlog,
        validate_execution_contract,
        validate_execution_view,
    )
    from scripts.release_plan_validation import (
        validate_repository as validate_industrialization_repository,
    )
    from scripts.release_plan_views import (
        render_checklist,
        render_module_map,
        render_program_markdown,
        render_sequence,
    )

__all__ = [
    "PROGRAM_PATH",
    "load_plan",
    "load_program",
    "render_checklist",
    "render_module_map",
    "render_program_markdown",
    "render_sequence",
    "render_execution_backlog",
    "validate_repository",
]


def validate_repository(root: Path = ROOT) -> list[str]:
    """Run restored release, module projection and industrialization rules."""
    plan = load_plan(root)
    errors = validate_release_plan_compatibility(plan, root)
    errors.extend(validate_module_contract_status_projections(plan, root))
    errors.extend(validate_industrialization_repository(root))
    program_raw, execution_plan = load_execution_raw(root)
    errors.extend(validate_execution_contract(program_raw, execution_plan, root))
    errors.extend(validate_execution_view(program_raw, execution_plan, root))
    return errors


def main() -> int:
    errors = validate_repository(ROOT)
    if errors:
        print("Demo release / industrialization state contract: FAILED")
        for error in errors:
            print(f"- {error}")
        return 1
    plan = load_plan(ROOT)
    program = load_program(ROOT)
    print("Demo release / industrialization state contract: OK")
    print(f"Modules: {len(plan['modules'])}")
    print(f"Work-item status projections: {len(plan['work_items'])}")
    print(f"Industrialization work items: {len(program.items)}")
    print(
        "PILOT-READY mandatory core: "
        f"{len(program.gates['PILOT-READY'].required)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
