#!/usr/bin/env python3
"""Deterministic dependency/build-input inventory for DEPENDENCY-PROVENANCE-001."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from scripts import dependency_provenance_core as core

ROOT = Path(__file__).resolve().parents[1]
WORK_ITEM_DIR = Path("docs/work-items/active/DEPENDENCY-PROVENANCE-001")
INVENTORY_JSON = WORK_ITEM_DIR / "DEPENDENCY_BUILD_INVENTORY.json"
INVENTORY_MD = WORK_ITEM_DIR / "DEPENDENCY_BUILD_INVENTORY.md"

EXACT_SOURCE_EXCLUSIONS = core.EXACT_SOURCE_EXCLUSIONS
ExecutableSource = core.ExecutableSource
TrackedFile = core.TrackedFile
discover_executable_sources = core.discover_executable_sources
scan_actions = core.scan_actions
scan_images = core.scan_images
scan_operations = core.scan_operations
sha256_text = core.sha256_text
tracked_file_records = core.tracked_file_records
tracked_files = core.tracked_files


def build_inventory(root: Path = ROOT) -> dict[str, Any]:
    return core.build_inventory(root)


def render_json(inventory: dict[str, Any]) -> str:
    return json.dumps(inventory, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def md_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def render_markdown(inventory: dict[str, Any]) -> str:
    totals = inventory["totals"]
    contours = inventory["contours"]
    executable = contours["executable_sources"]
    lines = [
        "# Dependency/build inventory",
        "",
        (
            "> GENERATED VIEW из `scripts/dependency_provenance_inventory.py`. "
            "Ручное изменение отклоняется побайтной проверкой."
        ),
        "",
        "## Итог",
        "",
        f"- tracked files: `{totals['tracked_files']}`;",
        f"- inventory entries: `{totals['inventory_entries']}`;",
        f"- floating inputs: `{totals['floating_inputs']}`;",
        f"- immutable inputs: `{totals['immutable_inputs']}`;",
        f"- duplicate owner groups: `{totals['duplicate_owner_groups']}`;",
        f"- conflicting owner groups: `{totals['conflicting_owner_groups']}`;",
        (
            "- source files with dependency/build evidence: "
            f"`{totals['source_files']}`;"
        ),
        (
            "- applicable executable/config sources: "
            f"`{totals['applicable_executable_sources']}`;"
        ),
        (
            "- source completeness digests: "
            f"`{totals['source_completeness_digests']}`."
        ),
        "",
        "## Executable/config source completeness",
        "",
        f"- applicable paths: `{executable['applicable_count']}`;",
        f"- source kinds: `{executable['source_kinds']}`;",
        f"- uncovered paths: `{executable['uncovered_paths'] or 'NONE'}`;",
        f"- exact exclusions: `{executable['exact_exclusions'] or 'NONE'}`.",
        "",
        "## Контуры",
        "",
        (
            "- Python: "
            f"pyproject=`{contours['python']['pyproject_present']}`, "
            f"requirements={contours['python']['requirements_files'] or 'NONE'}, "
            f"locks={contours['python']['lock_files'] or 'NONE'}, "
            f"profiles={contours['python']['accepted_profiles']}, "
            "hashed lock="
            f"`{contours['python']['integrity_hashed_lock_present']}`."
        ),
        (
            "- JavaScript: package/lock files="
            f"{contours['javascript']['package_or_lock_files'] or 'NONE'}; "
            "separate frontend contour="
            f"`{contours['javascript']['separate_frontend_dependency_contour']}`."
        ),
        (
            "- Browser: Playwright declared="
            f"`{contours['browser']['python_playwright_declared']}`; "
            "binary install operations="
            f"{contours['browser']['browser_binary_install_operations'] or 'NONE'}; "
            "integrity contract="
            f"`{contours['browser']['binary_integrity_contract_present']}`."
        ),
        (
            "- Containers: Dockerfiles="
            f"{contours['containers']['dockerfiles']}; "
            f"Compose={contours['containers']['compose_files']}."
        ),
        (
            "- GitHub Actions: workflows="
            f"`{len(contours['github_actions']['workflow_files'])}`; "
            "temporary="
            f"{contours['github_actions']['temporary_workflow_files'] or 'NONE'}."
        ),
        (
            "- External downloads: "
            f"`{contours['external_downloads']['download_operation_count']}`; "
            "local runtime probes excluded="
            f"`{contours['external_downloads']['local_runtime_probes_excluded']}`."
        ),
        (
            "- Static assets: tracked="
            f"`{contours['assets']['tracked_static_file_count']}`; "
            "external references="
            f"`{contours['assets']['external_asset_reference_count']}`."
        ),
        "",
        "## Totals by class",
        "",
        "| Class | Count |",
        "|---|---:|",
    ]
    for input_class, count in totals["by_class"].items():
        lines.append(f"| `{input_class}` | {count} |")
    lines.extend(
        [
            "",
            "## Inputs",
            "",
            (
                "| ID | Class | Path:line | Scope | Declaration | Immutable | "
                "Hash | Reproducibility | Risk | Proposed owner |"
            ),
            "|---|---|---|---|---|---:|---|---|---|---|",
        ]
    )
    for item in inventory["entries"]:
        location = item["path"] + (
            f":{item['line']}" if item["line"] else ""
        )
        cells = [
            f"`{md_cell(item['id'])}`",
            f"`{md_cell(item['class'])}`",
            f"`{md_cell(location)}`",
            md_cell(item["dependency_scope"]),
            f"`{md_cell(item['declaration'])}`",
            "yes" if item["immutable"] else "no",
            md_cell(item["hash_coverage"]),
            md_cell(item["current_reproducibility"]),
            md_cell(item["risk"]),
            md_cell(item["proposed_owner"]),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    lines.extend(["", "## Duplicate owner groups", ""])
    if inventory["duplicate_owner_groups"]:
        for group in inventory["duplicate_owner_groups"]:
            conflict = (
                "conflicting" if group["conflicting_declarations"] else "repeated"
            )
            paths = ", ".join(group["paths"])
            lines.append(
                f"- `{group['class']}:{group['name']}` — "
                f"{group['occurrences']} {conflict} references in {paths}."
            )
    else:
        lines.append("- NONE.")
    lines.extend(["", "## Ограничения", ""])
    lines.extend(f"- {item}" for item in inventory["limitations"])
    return "\n".join(lines).rstrip() + "\n"


def validation_errors(root: Path = ROOT) -> list[str]:
    inventory = build_inventory(root)
    errors: list[str] = []
    temporary = inventory["contours"]["github_actions"][
        "temporary_workflow_files"
    ]
    if temporary:
        errors.append(
            ".github/workflows: rule=temporary-workflow-absent; "
            f"expected=[]; actual={temporary!r}"
        )
    uncovered = inventory["contours"]["executable_sources"]["uncovered_paths"]
    if uncovered:
        errors.append(
            "repository: rule=inventory-source-completeness; "
            f"expected=[]; actual={uncovered!r}"
        )
    expected = (
        (INVENTORY_JSON, render_json(inventory)),
        (INVENTORY_MD, render_markdown(inventory)),
    )
    for relative, expected_content in expected:
        path = root / relative
        if not path.is_file():
            errors.append(
                f"{relative}: rule=inventory-generated-view-present; "
                "expected='tracked exact view'; actual='missing'"
            )
            continue
        actual_content = path.read_text(encoding="utf-8")
        if actual_content != expected_content:
            errors.append(
                f"{relative}: rule=inventory-generated-view-exact; "
                f"expected_sha256='{sha256_text(expected_content)}'; "
                f"actual_sha256='{sha256_text(actual_content)}'"
            )
    return errors


def write_views(root: Path = ROOT) -> None:
    inventory = build_inventory(root)
    for relative, content in (
        (INVENTORY_JSON, render_json(inventory)),
        (INVENTORY_MD, render_markdown(inventory)),
    ):
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command",
        choices=("check", "summary", "write"),
        nargs="?",
        default="check",
    )
    args = parser.parse_args()
    if args.command == "write":
        write_views(ROOT)
        print(f"WROTE {INVENTORY_JSON} and {INVENTORY_MD}")
        return 0
    inventory = build_inventory(ROOT)
    if args.command == "summary":
        print(json.dumps(inventory["totals"], ensure_ascii=False, sort_keys=True))
        return 0
    errors = validation_errors(ROOT)
    if errors:
        print("Dependency provenance inventory: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print(
            "Run: python scripts/dependency_provenance_inventory.py write",
            file=sys.stderr,
        )
        return 1
    print("Dependency provenance inventory: OK")
    print(json.dumps(inventory["totals"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "EXACT_SOURCE_EXCLUSIONS",
    "ExecutableSource",
    "ROOT",
    "TrackedFile",
    "build_inventory",
    "discover_executable_sources",
    "render_markdown",
    "scan_actions",
    "scan_images",
    "scan_operations",
    "tracked_file_records",
    "tracked_files",
    "validation_errors",
]
