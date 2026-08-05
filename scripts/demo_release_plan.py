#!/usr/bin/env python3
"""Public entry point for canonical planning-state validation and generation."""

from __future__ import annotations

try:
    from .release_plan_model import PROGRAM_PATH, ROOT, load_plan, load_program
    from .release_plan_validation import validate_repository
    from .release_plan_views import (
        render_checklist,
        render_module_map,
        render_program_markdown,
        render_sequence,
    )
except ImportError:
    from release_plan_model import PROGRAM_PATH, ROOT, load_plan, load_program
    from release_plan_validation import validate_repository
    from release_plan_views import (
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
    "validate_repository",
]


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
