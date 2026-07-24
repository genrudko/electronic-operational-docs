from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import time
import zipfile
from collections import Counter
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def readonly_uri(path: Path) -> str:
    return f"{path.resolve().as_uri()}?mode=ro"


def sqlite_integrity(path: Path) -> str:
    with closing(sqlite3.connect(readonly_uri(path), uri=True)) as database:
        result = database.execute("PRAGMA integrity_check").fetchone()
    return str(result[0] if result else "no result")


def create_sqlite_backup(source_path: Path, backup_path: Path) -> int:
    source_check = sqlite_integrity(source_path)
    if source_check != "ok":
        raise RuntimeError(f"Source database integrity check failed: {source_check}")

    if backup_path.exists():
        backup_path.unlink()

    with closing(sqlite3.connect(readonly_uri(source_path), uri=True)) as source:
        with closing(sqlite3.connect(backup_path)) as target:
            source.backup(target)
            target.execute("PRAGMA optimize")
            target.commit()

    backup_check = sqlite_integrity(backup_path)
    if backup_check != "ok":
        raise RuntimeError(f"Backup database integrity check failed: {backup_check}")

    with closing(sqlite3.connect(readonly_uri(backup_path), uri=True)) as database:
        table_count = database.execute(
            """
            SELECT COUNT(*)
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            """
        ).fetchone()[0]

    print("Source integrity: ok")
    print("Backup integrity: ok")
    print(f"Application tables: {table_count}")
    print(f"Backup size: {backup_path.stat().st_size} bytes")
    return int(table_count)


def export_fixture(repo: Path, backup_path: Path, fixture_path: Path) -> None:
    environment = os.environ.copy()
    environment.update(
        {
            "DB_ENGINE": "sqlite",
            "EOD_DATABASE_PROFILE": "explicit",
            "EOD_ALLOW_SQLITE_PATH_OVERRIDE": "1",
            "SQLITE_PATH": str(backup_path),
            "DJANGO_SECRET_KEY": "local-snapshot-validation-only",
            "DJANGO_DEBUG": "0",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8",
        }
    )

    command = [
        sys.executable,
        "-X",
        "utf8",
        str(repo / "manage.py"),
        "dumpdata",
        "--all",
        "--natural-foreign",
        "--natural-primary",
        "--indent",
        "2",
        "--exclude",
        "contenttypes.contenttype",
        "--exclude",
        "auth.permission",
        "--exclude",
        "sessions.session",
        "--exclude",
        "admin.logentry",
    ]

    with fixture_path.open("wb") as output:
        result = subprocess.run(
            command,
            cwd=repo,
            env=environment,
            stdout=output,
            stderr=subprocess.PIPE,
            check=False,
        )

    if result.returncode != 0:
        details = result.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(
            "Django fixture export failed" + (f":\n{details}" if details else ".")
        )

    if not fixture_path.is_file() or fixture_path.stat().st_size <= 0:
        raise RuntimeError("Django fixture was not created or is empty.")


def sqlite_table_counts(database_path: Path) -> dict[str, int]:
    with closing(sqlite3.connect(readonly_uri(database_path), uri=True)) as database:
        names = [
            row[0]
            for row in database.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                  AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                """
            )
        ]
        counts: dict[str, int] = {}
        for name in names:
            escaped = name.replace('"', '""')
            counts[name] = int(
                database.execute(f'SELECT COUNT(*) FROM "{escaped}"').fetchone()[0]
            )
    return counts


def create_manifest(
    database_path: Path,
    fixture_path: Path,
    manifest_path: Path,
) -> None:
    objects = json.loads(fixture_path.read_text(encoding="utf-8"))
    if not isinstance(objects, list) or not objects:
        raise RuntimeError("Django fixture must contain a non-empty JSON list.")

    model_counts = Counter(item["model"] for item in objects)
    table_counts = sqlite_table_counts(database_path)
    database_manifest = {
        "filename": database_path.name,
        "size_bytes": database_path.stat().st_size,
        "sha256": sha256(database_path),
        "integrity_check": sqlite_integrity(database_path),
    }
    fixture_manifest = {
        "filename": fixture_path.name,
        "size_bytes": fixture_path.stat().st_size,
        "sha256": sha256(fixture_path),
        "object_count": len(objects),
        "model_count": len(model_counts),
    }
    manifest = {
        "snapshot_format": "eod.presentation.snapshot.v1",
        "created_at_utc": datetime.now(UTC).isoformat(),
        "database": database_manifest,
        "fixture": fixture_manifest,
        "model_counts": dict(sorted(model_counts.items())),
        "sqlite_table_counts": table_counts,
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Fixture objects: {len(objects)}")
    print(f"Fixture models: {len(model_counts)}")
    print(f"SQLite tables: {len(table_counts)}")
    print(f"Database SHA-256: {database_manifest['sha256']}")
    print(f"Fixture SHA-256: {fixture_manifest['sha256']}")


def file_tree_manifest(root: Path) -> dict[str, tuple[int, str]]:
    return {
        path.relative_to(root).as_posix(): (path.stat().st_size, sha256(path))
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def promote_snapshot_directory(working_dir: Path, final_dir: Path) -> None:
    last_error: OSError | None = None
    attempts = 6

    for attempt in range(1, attempts + 1):
        try:
            os.replace(working_dir, final_dir)
            print(f"Snapshot directory finalized by rename on attempt {attempt}.")
            return
        except OSError as exc:
            last_error = exc
            if final_dir.exists():
                raise RuntimeError(
                    f"Snapshot target appeared unexpectedly: {final_dir}"
                ) from exc
            if attempt < attempts:
                delay = 0.5 * attempt
                print(
                    f"Directory rename attempt {attempt}/{attempts} failed: {exc}. "
                    f"Retrying in {delay:.1f}s."
                )
                time.sleep(delay)

    print(f"Directory rename remained unavailable: {last_error}")
    print("Using verified directory copy fallback.")
    expected_files = file_tree_manifest(working_dir)

    try:
        shutil.copytree(working_dir, final_dir)
        actual_files = file_tree_manifest(final_dir)
        if actual_files != expected_files:
            raise RuntimeError(
                "Copied snapshot directory does not match the working directory."
            )
    except Exception:
        if final_dir.exists():
            shutil.rmtree(final_dir, ignore_errors=True)
        raise

    shutil.rmtree(working_dir)
    print("Snapshot directory finalized by verified copy fallback.")


def create_archive(source_dir: Path, archive_path: Path) -> None:
    with zipfile.ZipFile(
        archive_path,
        "w",
        compression=zipfile.ZIP_DEFLATED,
    ) as archive:
        for path in sorted(source_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source_dir).as_posix())


def parse_args() -> argparse.Namespace:
    default_repo = Path(__file__).resolve().parents[1]
    default_backup_root = (
        Path(r"G:\EOD_BACKUPS")
        if os.name == "nt"
        else default_repo.parent / "EOD_BACKUPS"
    )
    parser = argparse.ArgumentParser(
        description="Create a verified transferable snapshot of presentation.sqlite3."
    )
    parser.add_argument("--repo", type=Path, default=default_repo)
    parser.add_argument("--backup-root", type=Path, default=default_backup_root)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo = args.repo.resolve()
    backup_root = args.backup_root.resolve()
    source_database = repo / "data" / "presentation.sqlite3"
    media_source = repo / "media"

    if not (repo / "manage.py").is_file():
        raise RuntimeError(f"manage.py not found: {repo / 'manage.py'}")
    if not source_database.is_file() or source_database.stat().st_size <= 0:
        raise RuntimeError(f"Presentation database is missing or empty: {source_database}")

    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    snapshot_name = f"presentation_{stamp}"
    working_dir = backup_root / f"{snapshot_name}.tmp"
    final_dir = backup_root / snapshot_name
    archive_path = backup_root / f"{snapshot_name}.zip"
    hash_path = backup_root / f"{snapshot_name}.zip.sha256.txt"

    if working_dir.exists():
        shutil.rmtree(working_dir)
    if final_dir.exists() or archive_path.exists() or hash_path.exists():
        raise RuntimeError(f"Snapshot target already exists: {snapshot_name}")

    working_dir.mkdir(parents=True)
    backup_database = working_dir / "presentation.sqlite3"
    fixture_path = working_dir / "presentation_fixture.json"
    manifest_path = working_dir / "manifest.json"

    try:
        print("===== SOURCE DATABASE =====")
        print(f"Path: {source_database}")
        print(f"Size: {source_database.stat().st_size} bytes")

        print("\n===== CREATE CONSISTENT SQLITE BACKUP =====")
        create_sqlite_backup(source_database, backup_database)

        print("\n===== EXPORT DJANGO DATA =====")
        export_fixture(repo, backup_database, fixture_path)

        print("\n===== COPY MEDIA =====")
        media_files = (
            [path for path in media_source.rglob("*") if path.is_file()]
            if media_source.is_dir()
            else []
        )
        if media_files:
            shutil.copytree(media_source, working_dir / "media")
            print(f"Media copied: {len(media_files)} files")
        else:
            print("Media directory is absent or empty.")

        print("\n===== CREATE MANIFEST =====")
        create_manifest(backup_database, fixture_path, manifest_path)

        print("\n===== FINALIZE SNAPSHOT DIRECTORY =====")
        promote_snapshot_directory(working_dir, final_dir)

        print("\n===== CREATE TRANSFER ARCHIVE =====")
        create_archive(final_dir, archive_path)
        archive_hash = sha256(archive_path)
        hash_path.write_text(
            f"{archive_hash}  {archive_path.name}\n",
            encoding="ascii",
        )

        print("\n===== SNAPSHOT READY =====")
        print(f"Snapshot directory: {final_dir}")
        print(f"Transfer archive:   {archive_path}")
        print(f"Archive SHA-256:    {archive_hash}")
        print("Source database was not modified.")
        return 0
    except Exception:
        for directory in (working_dir, final_dir):
            if directory.exists():
                shutil.rmtree(directory, ignore_errors=True)
        for file_path in (archive_path, hash_path):
            if file_path.exists():
                file_path.unlink(missing_ok=True)
        raise


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
