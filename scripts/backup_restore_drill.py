#!/usr/bin/env python3
"""Fail-closed PostgreSQL backup/restore acceptance drill for EOD."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

ROOT = Path(__file__).resolve().parents[1]
CERTIFICATE_SCHEMA = "eod.backup_restore_drill.certificate"
CERTIFICATE_VERSION = 1
WORK_ITEM = "BACKUP-RESTORE-DRILL-001"
RPO_TARGET_HOURS = 24
RTO_TARGET_HOURS = 4
DISPOSABLE_TARGET_CLASS = "ci-disposable"
DISPOSABLE_SENTINEL = "EOD-DISPOSABLE-RESTORE-ONLY"
TARGET_DATABASE_RE = re.compile(r"^eod_restore_drill_[a-z0-9_]{1,80}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PROTECTED_DATABASES = frozenset({"eod", "eod_preview", "eod_development", "postgres"})
REPRESENTATIVE_MODELS = (
    "organizations.Organization",
    "organizations.Workplace",
    "organizations.Employee",
    "organizations.RoleAssignment",
    "equipment.EnergySite",
    "equipment.EquipmentAsset",
)
FORBIDDEN_CERTIFICATE_KEY_PARTS = (
    "password", "secret", "token", "credential", "private_key", "dsn",
    "connection_string", "raw_dump", "dump_path", "dump_content",
)
FORBIDDEN_CERTIFICATE_TEXT = (
    "PGDMP", "BEGIN PRIVATE KEY", "BEGIN OPENSSH PRIVATE KEY",
    "postgresql://", "POSTGRES_PASSWORD", "DJANGO_SECRET_KEY",
)


class DrillError(RuntimeError):
    pass


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run(argv: Sequence[str], *, env: Mapping[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    """Run one bounded local PostgreSQL/Django/docker command without a shell."""
    try:
        return subprocess.run(
            list(argv), cwd=ROOT, env=dict(env) if env is not None else None,
            check=True, capture_output=True, text=True,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        executable = argv[0] if argv else "<empty>"
        raise DrillError(f"command failed: {executable}") from exc


def pg_environment() -> dict[str, str]:
    env = dict(os.environ)
    if env.get("POSTGRES_PASSWORD"):
        env["PGPASSWORD"] = env["POSTGRES_PASSWORD"]
    return env


def pg_tool_argv(tool: str, *args: str) -> list[str]:
    container = os.environ.get("EOD_DR_PG_CONTAINER", "").strip()
    if container:
        if not re.fullmatch(r"[0-9a-f]{12,64}", container):
            raise DrillError("PostgreSQL tool container identity is invalid")
        return ["docker", "exec", container, tool, *args]
    return [tool, *args]


def database_connection_args(database: str) -> list[str]:
    return [
        "--host", os.environ.get("POSTGRES_HOST", "127.0.0.1"),
        "--port", os.environ.get("POSTGRES_PORT", "5432"),
        "--username", os.environ.get("POSTGRES_USER", "eod"),
        "--dbname", database,
    ]


def psql_scalar(database: str, sql: str) -> str:
    result = _run(pg_tool_argv(
        "psql", *database_connection_args(database), "--no-psqlrc",
        "--tuples-only", "--no-align", "--set", "ON_ERROR_STOP=1",
        "--command", sql,
    ), env=pg_environment())
    lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if len(lines) != 1:
        raise DrillError(f"ambiguous PostgreSQL scalar result: rows={len(lines)}")
    return lines[0]


def validate_target_identity(*, source_database: str, target_database: str, target_class: str, sentinel: str) -> None:
    if not all((source_database, target_database, target_class, sentinel)):
        raise DrillError("ambiguous restore target identity")
    if target_class != DISPOSABLE_TARGET_CLASS or sentinel != DISPOSABLE_SENTINEL:
        raise DrillError("restore target is not explicitly disposable")
    if not TARGET_DATABASE_RE.fullmatch(target_database):
        raise DrillError("restore target database identity is not approved")
    if target_database in PROTECTED_DATABASES or target_database == source_database:
        raise DrillError("restore into live/source/non-disposable database is forbidden")


def database_exists(database: str) -> bool:
    if not re.fullmatch(r"[A-Za-z0-9_]+", database):
        raise DrillError("unsafe database identifier")
    count = psql_scalar("postgres", f"SELECT count(*) FROM pg_database WHERE datname = '{database}';")
    if count not in {"0", "1"}:
        raise DrillError("ambiguous database existence result")
    return count == "1"


def create_clean_target(database: str) -> None:
    if database_exists(database):
        raise DrillError("restore target already exists; clean target required")
    _run(pg_tool_argv(
        "psql", *database_connection_args("postgres"), "--no-psqlrc",
        "--set", "ON_ERROR_STOP=1", "--command",
        f'CREATE DATABASE "{database}" TEMPLATE template0;',
    ), env=pg_environment())
    if psql_scalar(database, "SELECT current_database();") != database:
        raise DrillError("restore target identity guard failed")
    tables = psql_scalar(
        database,
        "SELECT count(*) FROM pg_tables WHERE schemaname NOT IN ('pg_catalog', 'information_schema');",
    )
    if tables != "0":
        raise DrillError("restore target is not clean")


def drop_target(database: str) -> None:
    if not database_exists(database):
        return
    _run(pg_tool_argv(
        "psql", *database_connection_args("postgres"), "--no-psqlrc",
        "--set", "ON_ERROR_STOP=1", "--command",
        "SELECT pg_terminate_backend(pid) FROM pg_stat_activity "
        f"WHERE datname = '{database}' AND pid <> pg_backend_pid();",
    ), env=pg_environment())
    _run(pg_tool_argv(
        "psql", *database_connection_args("postgres"), "--no-psqlrc",
        "--set", "ON_ERROR_STOP=1", "--command", f'DROP DATABASE "{database}";',
    ), env=pg_environment())
    if database_exists(database):
        raise DrillError("disposable restore target cleanup failed")


def require_nonempty_backup(path: Path) -> int:
    if not path.is_file():
        raise DrillError("backup file is missing")
    size = path.stat().st_size
    if size <= 0:
        raise DrillError("backup file is empty")
    return size


def assert_pg_restore_readable(path: Path, *, tool_path: str | None = None) -> None:
    require_nonempty_backup(path)
    _run(pg_tool_argv("pg_restore", "--list", tool_path or str(path)), env=pg_environment())


def verify_backup_checksum(path: Path, expected_sha256: str) -> None:
    if not SHA256_RE.fullmatch(expected_sha256) or sha256_file(path) != expected_sha256:
        raise DrillError("backup checksum mismatch")


def restore_backup(path: Path, target_database: str, *, tool_path: str | None = None) -> None:
    require_nonempty_backup(path)
    _run(pg_tool_argv(
        "pg_restore", *database_connection_args(target_database), "--exit-on-error",
        "--no-owner", "--no-acl", tool_path or str(path),
    ), env=pg_environment())


def django_environment(database: str) -> dict[str, str]:
    env = dict(os.environ)
    env.update({
        "DB_ENGINE": "postgresql", "POSTGRES_DB": database,
        "EOD_DATABASE_PROFILE": "gate", "EOD_DEPLOYMENT_MODE": "ci",
        "DJANGO_DEBUG": "0", "DJANGO_ALLOWED_HOSTS": "127.0.0.1,localhost,testserver",
    })
    return env


def django_json(database: str, code: str) -> dict[str, Any]:
    result = _run([sys.executable, "manage.py", "shell", "-c", code], env=django_environment(database))
    for line in reversed([line.strip() for line in result.stdout.splitlines() if line.strip()]):
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    raise DrillError("Django verification did not emit a JSON object")


def representative_counts(database: str) -> dict[str, int]:
    labels = json.dumps(REPRESENTATIVE_MODELS)
    raw = django_json(database, (
        "import json; from django.apps import apps; "
        f"labels={labels}; "
        "print(json.dumps({label: apps.get_model(label).objects.count() for label in labels}, sort_keys=True))"
    ))
    counts: dict[str, int] = {}
    for label in REPRESENTATIVE_MODELS:
        value = raw.get(label)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise DrillError(f"invalid representative count for {label}")
        counts[label] = value
    return counts


def validate_representative_counts(before: Mapping[str, int], after: Mapping[str, int]) -> None:
    expected = set(REPRESENTATIVE_MODELS)
    if set(before) != expected or set(after) != expected:
        raise DrillError("representative count set is incomplete")
    if dict(before) != dict(after):
        raise DrillError("representative object counts changed after restore")
    empty = [label for label, count in before.items() if count <= 0]
    if empty:
        raise DrillError(f"representative source data is insufficient: {empty}")


def django_post_restore_checks(database: str) -> None:
    env = django_environment(database)
    _run([sys.executable, "manage.py", "migrate", "--noinput"], env=env)
    _run([sys.executable, "manage.py", "check"], env=env)
    ready = django_json(
        database,
        "import json; from eod_config.health import _deployment_dependencies_ready; "
        "print(json.dumps({'ready': bool(_deployment_dependencies_ready())}))",
    )
    if ready.get("ready") is not True:
        raise DrillError("restored database readiness check failed")


def postgres_versions(source_database: str) -> dict[str, str]:
    return {
        "server": psql_scalar(source_database, "SHOW server_version;"),
        "pg_dump": _run(pg_tool_argv("pg_dump", "--version")).stdout.strip(),
        "pg_restore": _run(pg_tool_argv("pg_restore", "--version")).stdout.strip(),
    }


def _walk(value: Any, path: str = "$") -> Iterable[tuple[str, Any]]:
    yield path, value
    if isinstance(value, dict):
        for key, item in value.items():
            yield from _walk(item, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from _walk(item, f"{path}[{index}]")


def validate_certificate_payload(payload: Mapping[str, Any]) -> None:
    for path, value in _walk(payload):
        key = path.rsplit(".", 1)[-1].lower()
        if any(part in key for part in FORBIDDEN_CERTIFICATE_KEY_PARTS):
            raise DrillError(f"certificate contains forbidden sensitive field: {path}")
        if isinstance(value, str) and any(marker in value for marker in FORBIDDEN_CERTIFICATE_TEXT):
            raise DrillError(f"certificate contains forbidden raw/secret material: {path}")
    if payload.get("schema") != CERTIFICATE_SCHEMA or payload.get("schema_version") != CERTIFICATE_VERSION:
        raise DrillError("restore certificate schema/version mismatch")
    if payload.get("work_item") != WORK_ITEM or payload.get("overall") != "PASS":
        raise DrillError("restore certificate is not passing")
    repo, backup, target = payload.get("repository"), payload.get("backup"), payload.get("restore_target")
    verification, objectives, timing = payload.get("verification"), payload.get("objectives"), payload.get("timing")
    if not all(isinstance(item, dict) for item in (repo, backup, target, verification, objectives, timing)):
        raise DrillError("restore certificate sections are incomplete")
    if not re.fullmatch(r"[0-9a-f]{40}", str(repo.get("exact_head", ""))):
        raise DrillError("restore certificate exact head is invalid")
    if backup.get("format") != "postgresql-custom" or backup.get("pg_restore_list") != "PASS" or backup.get("checksum_verification") != "PASS":
        raise DrillError("backup verification did not pass")
    if not isinstance(backup.get("size_bytes"), int) or backup["size_bytes"] <= 0 or not SHA256_RE.fullmatch(str(backup.get("sha256", ""))):
        raise DrillError("backup evidence is invalid")
    if target.get("class") != DISPOSABLE_TARGET_CLASS:
        raise DrillError("restore target class is invalid")
    for field in ("identity_guard", "clean_target", "cleanup"):
        if target.get(field) != "PASS":
            raise DrillError(f"restore target {field} did not pass")
    for field in ("restore", "migrations", "system_check", "database_identity", "readiness", "counts", "integrity"):
        if verification.get(field) != "PASS":
            raise DrillError(f"verification {field} did not pass")
    before, after = payload.get("pre_restore_counts"), payload.get("post_restore_counts")
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise DrillError("representative counts are missing")
    validate_representative_counts(before, after)
    if objectives.get("rpo_target_hours") != RPO_TARGET_HOURS or objectives.get("rto_target_hours") != RTO_TARGET_HOURS:
        raise DrillError("RPO/RTO target drift")
    if objectives.get("production_rto_status") != "TARGET_SLO_NOT_PROVEN_BY_CI":
        raise DrillError("CI restore time must not be claimed as production RTO")
    for field in ("restore_seconds", "drill_seconds"):
        value = timing.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0:
            raise DrillError(f"timing {field} is invalid")


def write_certificate(payload: Mapping[str, Any], path: Path, checksum_path: Path) -> str:
    validate_certificate_payload(payload)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(canonical_json(payload), encoding="utf-8")
    digest = sha256_file(path)
    checksum_path.write_text(f"{digest}  {path.name}\n", encoding="utf-8")
    return digest


def verify_certificate_files(path: Path, checksum_path: Path) -> str:
    if not path.is_file() or not checksum_path.is_file():
        raise DrillError("certificate or certificate checksum is missing")
    lines = [line.strip() for line in checksum_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) != 1:
        raise DrillError("certificate checksum evidence is ambiguous")
    match = re.fullmatch(r"([0-9a-f]{64})  ([^/\\]+)", lines[0])
    if not match or match.group(2) != path.name or sha256_file(path) != match.group(1):
        raise DrillError("certificate checksum mismatch")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise DrillError("restore certificate JSON is unreadable") from exc
    if not isinstance(payload, dict):
        raise DrillError("restore certificate root must be an object")
    validate_certificate_payload(payload)
    return match.group(1)


def run_restore_drill(args: argparse.Namespace) -> int:
    source = os.environ.get("POSTGRES_DB", "").strip()
    validate_target_identity(
        source_database=source, target_database=args.target_database,
        target_class=args.target_class, sentinel=args.disposable_sentinel,
    )
    if psql_scalar(source, "SELECT current_database();") != source:
        raise DrillError("source database identity mismatch")
    exact_head = (os.environ.get("EOD_EXACT_HEAD") or os.environ.get("GITHUB_SHA") or "").strip()
    if not re.fullmatch(r"[0-9a-f]{40}", exact_head):
        raise DrillError("exact repository head is required")

    work_dir = Path(args.work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)
    dump_path = work_dir / "recovery-point.dump"
    pg_container = os.environ.get("EOD_DR_PG_CONTAINER", "").strip()
    tool_dump = f"/tmp/{args.target_database}.dump" if pg_container else str(dump_path)
    certificate = Path(args.certificate).resolve()
    certificate_checksum = Path(args.certificate_checksum).resolve()
    started = time.monotonic()
    target_created = False
    try:
        versions = postgres_versions(source)
        before = representative_counts(source)
        validate_representative_counts(before, before)
        _run(pg_tool_argv(
            "pg_dump", *database_connection_args(source), "--format=custom",
            "--no-owner", "--no-acl", "--file", tool_dump,
        ), env=pg_environment())
        if pg_container:
            _run(["docker", "cp", f"{pg_container}:{tool_dump}", str(dump_path)])
        dump_size = require_nonempty_backup(dump_path)
        assert_pg_restore_readable(dump_path, tool_path=tool_dump)
        dump_sha = sha256_file(dump_path)
        verify_backup_checksum(dump_path, dump_sha)
        create_clean_target(args.target_database)
        target_created = True
        restore_started = time.monotonic()
        restore_backup(dump_path, args.target_database, tool_path=tool_dump)
        restore_seconds = time.monotonic() - restore_started
        if psql_scalar(args.target_database, "SELECT current_database();") != args.target_database:
            raise DrillError("post-restore database identity mismatch")
        django_post_restore_checks(args.target_database)
        after = representative_counts(args.target_database)
        validate_representative_counts(before, after)
        drop_target(args.target_database)
        target_created = False
        drill_seconds = time.monotonic() - started
        payload: dict[str, Any] = {
            "schema": CERTIFICATE_SCHEMA,
            "schema_version": CERTIFICATE_VERSION,
            "work_item": WORK_ITEM,
            "repository": {"name": "genrudko/electronic-operational-docs", "exact_head": exact_head},
            "recovery_point": {
                "source_class": args.source_class,
                "source_database_identity": source,
                "representative_dataset": "DEMO-ORGANIZATION-PLUS-DR-EQUIPMENT-V1",
            },
            "backup": {
                "format": "postgresql-custom", "sha256": dump_sha, "size_bytes": dump_size,
                "pg_restore_list": "PASS", "checksum_verification": "PASS",
            },
            "postgresql": versions,
            "restore_target": {
                "class": args.target_class, "database_identity": args.target_database,
                "identity_guard": "PASS", "clean_target": "PASS", "cleanup": "PASS",
            },
            "verification": {
                "restore": "PASS", "migrations": "PASS", "system_check": "PASS",
                "database_identity": "PASS", "readiness": "PASS", "counts": "PASS", "integrity": "PASS",
            },
            "pre_restore_counts": before,
            "post_restore_counts": after,
            "objectives": {
                "rpo_target_hours": RPO_TARGET_HOURS, "rto_target_hours": RTO_TARGET_HOURS,
                "production_rto_status": "TARGET_SLO_NOT_PROVEN_BY_CI",
            },
            "timing": {"restore_seconds": round(restore_seconds, 3), "drill_seconds": round(drill_seconds, 3)},
            "overall": "PASS",
        }
        cert_sha = write_certificate(payload, certificate, certificate_checksum)
        if verify_certificate_files(certificate, certificate_checksum) != cert_sha:
            raise DrillError("certificate verifier digest mismatch")
        print(canonical_json({
            "overall": "PASS", "backup_sha256": dump_sha, "backup_size_bytes": dump_size,
            "certificate_sha256": cert_sha, "restore_seconds": round(restore_seconds, 3),
            "drill_seconds": round(drill_seconds, 3),
        }).strip())
        return 0
    finally:
        dump_path.unlink(missing_ok=True)
        if pg_container:
            try:
                _run(["docker", "exec", pg_container, "rm", "-f", tool_dump])
            except DrillError:
                pass
        if target_created:
            try:
                drop_target(args.target_database)
            except DrillError:
                pass


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("--work-dir", required=True)
    run.add_argument("--certificate", required=True)
    run.add_argument("--certificate-checksum", required=True)
    run.add_argument("--source-class", default="ci-representative")
    run.add_argument("--target-database", required=True)
    run.add_argument("--target-class", required=True)
    run.add_argument("--disposable-sentinel", required=True)
    verify = commands.add_parser("verify-certificate")
    verify.add_argument("--certificate", required=True)
    verify.add_argument("--certificate-checksum", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "run":
            return run_restore_drill(args)
        digest = verify_certificate_files(Path(args.certificate), Path(args.certificate_checksum))
        print(f"RESTORE_CERTIFICATE_VERIFIED=PASS sha256={digest}")
        return 0
    except DrillError as exc:
        print(f"BACKUP_RESTORE_DRILL=FAIL reason={exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
