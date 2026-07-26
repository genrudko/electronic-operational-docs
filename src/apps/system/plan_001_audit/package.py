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


def _component_state(row: dict[str, Any], component: str) -> str:
    return str(row["component_states"][component]["status"])


def render_report(data: dict[str, Any]) -> str:
    project = data["project"]
    commands = data["commands"]
    decision = data["integration_decision"]
    runtime_categories = data["runtime_data_classification"]["categories"]
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
            "> Автоматический аудит фиксирует наблюдаемые факты по explicit "
            "ownership map. Он не объявляет модуль готовым и не подтверждает "
            "предметную приёмку."
        ),
        "",
        "## Ручное решение интеграционного Чата 0",
        "",
        (
            "> Этот раздел является зафиксированным integration decision, "
            "**не machine verdict**. Он основан на независимо принятом evidence "
            f"package `{decision['evidence_package_sha256']}` для exact head "
            f"`{decision['evidence_exact_head']}`."
        ),
        "",
        _table(
            ("Область", "Решение"),
            [
                (row["area"], row["verdict"])
                for row in decision["verdicts"]
            ],
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
        "## Runtime data classification",
        "",
        (
            "> Классификация разделяет canonical, staging/import, "
            "presentation/demo и system/internal. Непомеченные строки остаются "
            "`unknown`; staging не повышается до canonical."
        ),
        "",
        _table(
            ("Класс данных", "Состояние", "Row count", "Примечание"),
            [
                (
                    name,
                    payload["status"],
                    payload["row_count"],
                    payload["note"],
                )
                for name, payload in runtime_categories.items()
            ],
        ),
        "",
        "## Evidence matrix",
        "",
        (
            "> Статусы компонентов: `present`, `absent`, `unknown`, "
            "`not applicable`. Числовой ноль не используется как замена "
            "неизвестности."
        ),
        "",
        _table(
            (
                "Область",
                "Models",
                "Services",
                "Routes",
                "Tests",
                "Presentation",
                "Catalog",
                "Published type",
                "Records",
                "Acceptance",
            ),
            [
                (
                    row["requirement"],
                    _component_state(row, "models"),
                    _component_state(row, "services"),
                    _component_state(row, "routes"),
                    _component_state(row, "tests"),
                    _component_state(row, "presentation"),
                    row["source_catalog_state"],
                    row["published_type_state"],
                    row["records_state"],
                    row["subject_acceptance"],
                )
                for row in data["evidence_matrix"]
            ],
        ),
        "",
        "## Source-bound forms",
        "",
        _table(
            (
                "Code",
                "Name",
                "Catalog",
                "Installed types",
                "Published types",
                "Records",
            ),
            [
                (
                    row["code"],
                    row["name"],
                    "present" if row["catalog_present"] else "absent",
                    row["installed_type_count"],
                    row["published_type_count"],
                    row["record_count"],
                )
                for row in data["source_bound_forms"]
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
        (
            "- PLAN-001 acceptance references: `"
            + (
                ", ".join(data["documentation"]["plan001_acceptance_files"])
                or "none detected automatically"
            )
            + "`"
        ),
        "",
        "## Ограничения",
        "",
        (
            "- Discovery text hits остаются поисковым указателем и не влияют "
            "на ownership/readiness."
        ),
        (
            "- Наличие source catalog code не подменяет installed published "
            "type или runtime records."
        ),
        (
            "- Runtime row provenance без явного marker остаётся `unknown`; "
            "seed-код не доказывает repeatable presentation dataset."
        ),
        "- Global test success не доказывает lifecycle конкретного журнала.",
        "- Runtime smoke не заменяет браузерную и предметную приёмку.",
        "",
        "```text",
        "recommended first vertical slice: DEFECT JOURNAL",
        "decision source: permanent integration Chat 0",
        "automatic subject acceptance: NOT ESTABLISHED",
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
        "schema_version": 3,
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


def _matrix_csv_rows(data: dict[str, Any]) -> Iterable[dict[str, Any]]:
    for row in data["evidence_matrix"]:
        yield {
            **row,
            **{
                f"{component}_state": row["component_states"][component]["status"]
                for component in (
                    "models",
                    "services",
                    "forms",
                    "views",
                    "routes",
                    "templates",
                    "tests",
                    "presentation",
                )
            },
        }


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
    (output_dir / "integration_decision.json").write_text(
        json.dumps(
            data["integration_decision"],
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    write_csv(
        output_dir / "apps.csv",
        ("label", "name", "verbose_name", "path", "model_count", "migration_files"),
        data["apps"],
    )
    write_csv(
        output_dir / "models.csv",
        (
            "label",
            "app_label",
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
        output_dir / "runtime_data.csv",
        (
            "model",
            "app_label",
            "row_count",
            "data_class",
            "classification_reason",
        ),
        data["runtime_data_classification"]["models"],
    )
    write_csv(
        output_dir / "source_bound_forms.csv",
        (
            "code",
            "name",
            "purpose",
            "source_document",
            "source_section",
            "source_appendix",
            "catalog_present",
            "installed_type_count",
            "published_revision_count",
            "published_type_count",
            "record_count",
        ),
        data["source_bound_forms"],
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
            "ownership",
            "models_state",
            "services_state",
            "forms_state",
            "views_state",
            "routes_state",
            "templates_state",
            "tests_state",
            "presentation_state",
            "models",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
            "test_files",
            "static_test_method_count",
            "global_executed_test_count",
            "presentation_files",
            "source_bound_profiles",
            "source_catalog_state",
            "published_type_state",
            "records_state",
            "runtime_evidence",
            "subject_acceptance",
            "remaining_deficit",
        ),
        _matrix_csv_rows(data),
    )
    write_csv(
        output_dir / "domain_hits.csv",
        ("area", "path", "line", "token", "excerpt", "evidence_role"),
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
        json.dumps(package_manifest, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
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
