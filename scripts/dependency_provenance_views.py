#!/usr/bin/env python3
"""Canonical sharded generated views for dependency/build inventory."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from math import ceil
from pathlib import Path
from typing import Any

from scripts.dependency_provenance_inventory import (
    INVENTORY_JSON,
    INVENTORY_MD,
    ROOT,
    build_inventory,
    render_markdown,
)

SHARD_COUNT = 4
SHARD_GLOB = "DEPENDENCY_BUILD_INVENTORY.entries.*.json"


def json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def shard_path(index: int) -> Path:
    return INVENTORY_JSON.with_name(
        f"DEPENDENCY_BUILD_INVENTORY.entries.{index:02d}.json"
    )


def build_views(root: Path = ROOT) -> dict[Path, str]:
    inventory = build_inventory(root)
    inventory["generation"]["view_generator"] = (
        "scripts/dependency_provenance_views.py"
    )
    entries = inventory.pop("entries")
    chunk_size = max(1, ceil(len(entries) / SHARD_COUNT))
    views: dict[Path, str] = {}
    shard_metadata: list[dict[str, Any]] = []

    for index in range(1, SHARD_COUNT + 1):
        start = (index - 1) * chunk_size
        selected = entries[start : start + chunk_size]
        relative = shard_path(index)
        payload = {
            "schema": inventory["schema"],
            "work_item": inventory["work_item"],
            "shard": index,
            "entry_count": len(selected),
            "entries": selected,
        }
        content = json_text(payload)
        views[relative] = content
        shard_metadata.append(
            {
                "path": relative.as_posix(),
                "entry_count": len(selected),
                "first_id": selected[0]["id"] if selected else None,
                "last_id": selected[-1]["id"] if selected else None,
                "sha256": sha256_text(content),
            }
        )

    inventory["entries_total"] = len(entries)
    inventory["entry_format"] = "full records in deterministic JSON shards"
    inventory["entry_shards"] = shard_metadata
    views[INVENTORY_JSON] = json_text(inventory)

    markdown_inventory = dict(inventory)
    markdown_inventory["entries"] = entries
    views[INVENTORY_MD] = render_markdown(markdown_inventory)
    return views


def generated_paths(root: Path = ROOT) -> set[Path]:
    directory = root / INVENTORY_JSON.parent
    existing = {
        path.relative_to(root)
        for path in directory.glob(SHARD_GLOB)
        if path.is_file()
    }
    return existing | {INVENTORY_JSON, INVENTORY_MD}


def validation_errors(root: Path = ROOT) -> list[str]:
    expected = build_views(root)
    errors: list[str] = []
    actual_paths = generated_paths(root)
    expected_paths = set(expected)

    for extra in sorted(actual_paths - expected_paths):
        errors.append(
            f"{extra}: rule=inventory-generated-view-set; "
            "expected='absent'; actual='unexpected generated shard'"
        )

    for relative, expected_content in sorted(
        expected.items(), key=lambda item: item[0].as_posix()
    ):
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
    expected = build_views(root)
    for relative in generated_paths(root) - set(expected):
        (root / relative).unlink()
    for relative, content in expected.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", choices=("check", "write"), nargs="?", default="check"
    )
    args = parser.parse_args()

    if args.command == "write":
        write_views(ROOT)
        print("Dependency provenance generated views: WROTE")
        return 0

    errors = validation_errors(ROOT)
    if errors:
        print("Dependency provenance generated views: FAILED", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        print(
            "Run: python scripts/dependency_provenance_views.py write",
            file=sys.stderr,
        )
        return 1
    print("Dependency provenance generated views: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
