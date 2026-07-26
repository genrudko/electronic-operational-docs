#!/usr/bin/env python
from __future__ import annotations

import argparse
import os
import platform
import sys
import traceback
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from plan_001_audit.core import (
    DEFAULT_APP_ROOT,
    DEFAULT_REPO_ROOT,
    FULL_TEST_COMMAND,
    digest,
    now,
    relative,
    repo_files,
    run_command,
    secret_values,
    validate_sha,
)
from plan_001_audit.django_evidence import (
    app_and_model_inventory,
    database_inventory,
    migration_inventory,
    route_inventory,
    runtime_smoke,
    setup_django,
)
from plan_001_audit.package import write_package
from plan_001_audit.source_evidence import (
    asset_inventory,
    build_evidence_matrix,
    documentation_inventory,
    domain_hits,
    fixture_inventory,
    python_inventory,
)


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a sanitised exact-SHA PLAN-001 evidence package."
    )
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--pr-number", required=True, type=int)
    parser.add_argument("--head-sha", required=True)
    parser.add_argument("--trusted-main-head", required=True)
    parser.add_argument("--accepted-application-baseline", required=True)
    parser.add_argument("--image-ref", required=True)
    parser.add_argument("--repo-root", type=Path, default=DEFAULT_REPO_ROOT)
    parser.add_argument("--app-root", type=Path, default=DEFAULT_APP_ROOT)
    parser.add_argument("--command-timeout", type=int, default=3600)
    args = parser.parse_args(argv)
    if args.pr_number <= 0:
        parser.error("--pr-number must be positive")
    for field in ("head_sha", "trusted_main_head", "accepted_application_baseline"):
        try:
            setattr(args, field, validate_sha(getattr(args, field), f"--{field.replace('_', '-') }"))
        except argparse.ArgumentTypeError as exc:
            parser.error(str(exc))
    expected_image = f"eod-development-app:{args.head_sha}"
    if args.image_ref != expected_image:
        parser.error(f"--image-ref must be {expected_image}")
    if args.command_timeout < 60:
        parser.error("--command-timeout must be at least 60 seconds")
    return args


def source_parity(repo_root: Path, app_root: Path) -> dict[str, Any]:
    release_src = repo_root / "src"
    image_src = app_root / "src"
    release = {
        relative(path, release_src): digest(path.read_bytes())
        for path in repo_files(release_src)
    }
    image = {
        relative(path, image_src): digest(path.read_bytes())
        for path in repo_files(image_src)
        if "electronic_operational_docs.egg-info" not in path.parts
    }
    missing_from_image = sorted(set(release) - set(image))
    extra_in_image = sorted(set(image) - set(release))
    changed = sorted(
        path for path in set(release) & set(image) if release[path] != image[path]
    )
    return {
        "release_file_count": len(release),
        "image_file_count": len(image),
        "missing_from_image": missing_from_image,
        "extra_in_image": extra_in_image,
        "changed": changed,
        "matches": not missing_from_image and not extra_in_image and not changed,
    }


def command_set(
    repo_root: Path,
    app_root: Path,
    secrets: Sequence[str],
    timeout: int,
) -> dict[str, dict[str, Any]]:
    commands = {
        "django_check": [sys.executable, "manage.py", "check"],
        "migration_drift": [
            sys.executable,
            "manage.py",
            "makemigrations",
            "--check",
            "--dry-run",
        ],
        "pending_migration_gate": [
            sys.executable,
            "manage.py",
            "migrate",
            "--check",
        ],
        "architecture_gate": [
            sys.executable,
            str(repo_root / "scripts/gate_patch_011_7.py"),
        ],
        "django_tests": list(FULL_TEST_COMMAND),
    }
    return {
        name: run_command(
            command,
            cwd=app_root,
            secrets=secrets,
            timeout=timeout,
        )
        for name, command in commands.items()
    }


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    repo_root = args.repo_root.resolve()
    app_root = args.app_root.resolve()
    if not (repo_root / "scripts/plan_001_evidence_audit.py").is_file():
        raise SystemExit(f"PLAN-001 release root is invalid: {repo_root}")
    if not (app_root / "manage.py").is_file():
        raise SystemExit(f"Application image root is invalid: {app_root}")

    django = setup_django(app_root)
    database = database_inventory()
    if database["vendor"] != "postgresql":
        raise SystemExit("PLAN-001 audit requires PostgreSQL")
    if database["current_database"] != "eod_development":
        raise SystemExit(
            "PLAN-001 audit is allowed only against database eod_development"
        )
    if database["deployment_mode"] != "development":
        raise SystemExit("PLAN-001 audit requires EOD_DEPLOYMENT_MODE=development")
    if database["database_profile"] != "development":
        raise SystemExit("PLAN-001 audit requires EOD_DATABASE_PROFILE=development")

    parity = source_parity(repo_root, app_root)
    if not parity["matches"]:
        raise SystemExit("Release source and exact-SHA application image do not match")

    secrets = secret_values()
    commands = command_set(
        repo_root,
        app_root,
        secrets,
        args.command_timeout,
    )
    apps, models = app_and_model_inventory(app_root)
    migrations = migration_inventory()
    routes = route_inventory()
    python_rows = python_inventory(repo_root)
    assets = asset_inventory(repo_root)
    fixtures = fixture_inventory(repo_root, assets["fixtures"])
    smoke = runtime_smoke()
    hits = domain_hits(repo_root)
    matrix = build_evidence_matrix(
        models,
        migrations,
        routes,
        python_rows,
        assets,
        commands,
        smoke,
        hits,
    )
    docs = documentation_inventory(
        repo_root,
        args.trusted_main_head,
        args.accepted_application_baseline,
    )

    data = {
        "schema_version": 2,
        "project": {
            "generated_at": now(),
            "repository": "genrudko/electronic-operational-docs",
            "pr_number": args.pr_number,
            "head_sha": args.head_sha,
            "trusted_main_head": args.trusted_main_head,
            "accepted_application_baseline": args.accepted_application_baseline,
            "image_ref": args.image_ref,
            "python_version": platform.python_version(),
            "django_version": django.get_version(),
            "platform": platform.platform(),
            "release_root": "/repo",
            "application_root": "/app",
            "source_parity": parity,
        },
        "database": database,
        "documentation": docs,
        "apps": apps,
        "models": models,
        "migrations": migrations,
        "routes": routes,
        "python": python_rows,
        "assets": assets,
        "fixtures": fixtures,
        "runtime_smoke": smoke,
        "domain_hits": hits,
        "evidence_matrix": matrix,
        "commands": commands,
    }
    archive = write_package(args.output_dir.resolve(), data, secrets)
    print(f"PLAN-001 exact head: {args.head_sha}")
    print(f"PLAN-001 audit directory: {args.output_dir.resolve()}")
    print(f"PLAN-001 audit archive: {archive.resolve()}")
    print(f"PLAN-001 archive checksum: {archive.with_suffix(archive.suffix + '.sha256').resolve()}")
    print(
        "PLAN-001 executed tests: "
        f"{commands['django_tests']['executed_test_count']}"
    )

    failed = [
        name
        for name, result in commands.items()
        if result["timed_out"] or result["returncode"] != 0
    ]
    if migrations["pending"]:
        failed.append("pending_migrations_inventory")
    if commands["django_tests"]["executed_test_count"] in (None, 0):
        failed.append("nonzero_test_count")
    if failed:
        print(
            "WARNING: failed executable evidence gates: " + ", ".join(failed),
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        raise SystemExit(1) from None
