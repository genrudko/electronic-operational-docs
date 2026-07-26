from __future__ import annotations

import csv
import json
import zipfile
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Any

from .core import digest, sanitize


def write_csv(
    path: Path,
    fields: Sequence[str],
    rows: Iterable[dict[str, Any]],
) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=list(fields),
            extrasaction="ignore",
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        json.dumps(value, ensure_ascii=False, sort_keys=True)
                        if isinstance(value, (dict, list))
                        else value
                    )
                    for key, value in row.items()
                }
            )


def _table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    def render(value: Any) -> str:
        return (
            str(value if value is not None else "")
            .replace("|", "\\|")
            .replace("\n", "<br>")
        )

    lines = [
        "| " + " | ".join(render(item) for item in headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    lines.extend(
        "| " + " | ".join(render(item) for item in row) + " |" for row in rows
    )
    return "\n".join(lines)


def render_report(data: dict[str, Any]) -> str:
    project = data["project"]
    commands = data["commands"]
    lines = [
        "# PLAN-001 — доказательный снимок фактической реализации",
        "",
        f"**PR / exact head:** `#{project['pr_number']} / {project['head_sha']}`",
        "",
        f"**Trusted main:** `{project['trusted_main_head']}`",
        "",
        (
            "**Accepted application baseline:** "
            f"`{project['accepted_application_baseline']}`"
        ),
        "",
        f"**Generated:** `{project['generated_at']}`",
        "",
        (
            "> Автоматический аудит фиксирует наблюдаемые факты. "
            "Он не объявляет модуль готовым, не подтверждает "
            "предметную приёмку и не выбирает vertical slice."
        ),
        "",
        "## Технический срез",
        "",
        _table(
            ("Показатель", "Значение"),
            (
                ("Python", project["python_version"]),
                ("Django", project["django_version"]),
                ("Database", data["database"]["current_database"]),
                ("Apps", len(data["apps"])),
                ("Models", len(data["models"])),
                ("Pending migrations", len(data["migrations"]["pending"])),
                ("Routes", len(data["routes"])),
                ("Views modules", len(data["python"]["views"])),
                ("Forms modules", len(data["python"]["forms"])),
                ("Services modules", len(data["python"]["services"])),
                ("Executed tests", commands["django_tests"]["executed_test_count"]),
                ("Fixture objects", data["fixtures"]["total_objects"]),
            ),
        ),
        "",
        "## Исполняемые gates",
        "",
        _table(
            ("Gate", "RC", "Timeout", "Executed tests", "Последняя строка"),
            [
                (
                    name,
                    result["returncode"],
                    result["timed_out"],
                    result["executed_test_count"],
                    (
                        result["output"].strip().splitlines()[-1]
                        if result["output"].strip()
                        else ""
                    ),
                )
                for name, result in commands.items()
            ],
        ),
        "",
        "## Evidence matrix",
        "",
        _table(
            (
                "Область",
                "Models",
                "Services",
                "UI",
                "Tests",
                "Data",
                "Acceptance",
            ),
            [
                (
                    row["requirement"],
                    len(row["models"]),
                    len(row["services"]),
                    len(row["routes"]) + len(row["views"]),
                    row["static_test_method_count"],
                    "yes" if row["presentation_present"] else "not evidenced",
                    row["subject_acceptance"],
                )
                for row in data["evidence_matrix"]
            ],
        ),
        "",
        "## Документационная согласованность",
        "",
        (
            "- Missing mandatory docs: `"
            + (
                ", ".join(data["documentation"]["missing_mandatory_files"])
                or "none"
            )
            + "`"
        ),
        (
            "- Stale AUTO-001 claims: `"
            + (
                ", ".join(data["documentation"]["stale_auto001_claim_files"])
                or "none detected automatically"
            )
            + "`"
        ),
        "",
        "## Ограничения",
        "",
        (
            "- Text classification может давать ложные совпадения "
            "и пропуски."
        ),
        "- Row count не доказывает качество presentation data.",
        "- Global test success не доказывает lifecycle конкретного журнала.",
        "- Runtime smoke не заменяет браузерную и предметную приёмку.",
        "",
        "```text",
        "first journal vertical slice: NOT SELECTED",
        "merge authorization: ABSENT",
        "```",
        "",
    ]
    return "\n".join(lines)


def build_manifest(output_dir: Path, data: dict[str, Any]) -> dict[str, Any]:
    files = []
    for path in sorted(output_dir.rglob("*")):
        if path.is_file() and path.name != "manifest.json":
            payload = path.read_bytes()
            files.append(
                {
                    "path": path.relative_to(output_dir).as_posix(),
                    "bytes": len(payload),
                    "sha256": digest(payload),
                }
            )
    return {
        "schema_version": 2,
        "package": "PLAN-001-evidence-audit",
        "generated_at": data["project"]["generated_at"],
        "head_sha": data["project"]["head_sha"],
        "files": files,
    }


def verify_manifest(output_dir: Path, payload: dict[str, Any]) -> None:
    expected = set()
    for entry in payload["files"]:
        expected.add(entry["path"])
        path = output_dir / entry["path"]
        if not path.is_file():
            raise RuntimeError(f"manifest file is missing: {entry['path']}")
        content = path.read_bytes()
        if len(content) != entry["bytes"]:
            raise RuntimeError(f"manifest size mismatch: {entry['path']}")
        if digest(content) != entry["sha256"]:
            raise RuntimeError(f"manifest checksum mismatch: {entry['path']}")
    actual = {
        path.relative_to(output_dir).as_posix()
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    }
    if actual != expected:
        raise RuntimeError("manifest file set mismatch")


def scan_for_secret_leaks(output_dir: Path, secrets: Sequence[str]) -> None:
    forbidden = [item for item in secrets if len(item) >= 6]
    forbidden.append("PLAN001_SECRET_MARKER_DO_NOT_LEAK")
    for path in output_dir.rglob("*"):
        if not path.is_file():
            continue
        payload = path.read_bytes()
        for value in forbidden:
            if value.encode("utf-8") in payload:
                raise RuntimeError(
                    f"secret-like marker leaked into package: {path.name}"
                )


def write_package(
    output_dir: Path,
    data: dict[str, Any],
    secrets: Sequence[str],
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    data = sanitize(data, secrets)
    (output_dir / "audit.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    (output_dir / "REPORT.md").write_text(render_report(data), encoding="utf-8")
    write_csv(
        output_dir / "apps.csv",
        ("label", "name", "verbose_name", "path", "model_count", "migration_files"),
        data["apps"],
    )
    write_csv(
        output_dir / "models.csv",
        (
            "label",
            "verbose_name",
            "db_table",
            "db_table_exists",
            "managed",
            "proxy",
            "source_file",
            "fields",
            "constraints",
            "indexes",
            "row_count",
            "count_error",
        ),
        data["models"],
    )
    write_csv(
        output_dir / "routes.csv",
        ("route", "name", "namespace", "qualified_name", "callback", "lookup_str"),
        data["routes"],
    )
    write_csv(
        output_dir / "evidence_matrix.csv",
        (
            "area",
            "requirement",
            "models",
            "migration_disk_total",
            "pending_migrations_total",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
            "test_files",
            "static_test_method_count",
            "global_executed_test_count",
            "presentation_files",
            "classified_row_count",
            "runtime_evidence",
            "subject_acceptance",
            "remaining_deficit",
        ),
        data["evidence_matrix"],
    )
    write_csv(
        output_dir / "domain_hits.csv",
        ("area", "path", "line", "token", "excerpt"),
        (hit for hits in data["domain_hits"].values() for hit in hits),
    )
    write_csv(
        output_dir / "python_modules.csv",
        (
            "category",
            "path",
            "bytes",
            "sha256",
            "classes",
            "functions",
            "test_method_count",
            "parse_error",
        ),
        (
            {"category": category, **row}
            for category, rows in data["python"].items()
            for row in rows
        ),
    )
    write_csv(
        output_dir / "runtime_smoke.csv",
        ("path", "status_code", "location", "error"),
        data["runtime_smoke"],
    )
    command_dir = output_dir / "commands"
    command_dir.mkdir(exist_ok=True)
    for name, result in data["commands"].items():
        (command_dir / f"{name}.log").write_text(
            result["output"],
            encoding="utf-8",
        )
    scan_for_secret_leaks(output_dir, secrets)
    package_manifest = build_manifest(output_dir, data)
    (output_dir / "manifest.json").write_text(
        json.dumps(package_manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    verify_manifest(output_dir, package_manifest)
    archive = output_dir.parent / f"{output_dir.name}.zip"
    if archive.exists():
        archive.unlink()
    with zipfile.ZipFile(
        archive,
        "w",
        zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as target:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                target.write(
                    path,
                    f"{output_dir.name}/{path.relative_to(output_dir).as_posix()}",
                )
    archive.with_suffix(archive.suffix + ".sha256").write_text(
        f"{digest(archive.read_bytes())}  {archive.name}\n",
        encoding="utf-8",
    )
    return archive
