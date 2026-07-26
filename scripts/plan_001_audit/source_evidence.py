from __future__ import annotations

import ast
import json
import re
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .core import (
    SECRET_KEY_RE,
    TEXT_SUFFIXES,
    digest,
    read_text,
    relative,
    repo_files,
    sanitize_text,
)

SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
MANDATORY_DOCS = (
    "README.md",
    "AGENTS.md",
    "docs/INDEX.md",
    "docs/project/CURRENT_STATE.md",
    "docs/project/CURRENT_HANDOFF.md",
    "docs/project/DOMAIN_INVARIANTS.md",
    "docs/project/MASTER_PLAN.md",
    "docs/project/ROADMAP.md",
    "docs/project/OPEN_ITEMS.md",
    "docs/project/BASELINE_HISTORY.md",
    "docs/project/ACCEPTANCE_HISTORY.md",
    "docs/process/PROJECT_OPERATING_SYSTEM.md",
    "docs/process/DEVELOPMENT_WORKFLOW.md",
)
DOMAIN_AREAS: dict[str, tuple[str, tuple[str, ...]]] = {
    "structured_journal_core": (
        "Общее ядро структурированных журналов",
        (
            "structured_journal",
            "journalentry",
            "source_bound",
            "структурированн",
            "рабочая форма",
        ),
    ),
    "operational_journal": (
        "Оперативный журнал",
        ("operational_journal", "оперативный журнал", "оперативн", "смен"),
    ),
    "defect_journal": (
        "Журнал дефектов",
        ("defect", "дефект", "неисправност"),
    ),
    "application_journal": (
        "Журнал заявок",
        ("application", "request", "заявк"),
    ),
    "disposition_journal": (
        "Журнал распоряжений",
        ("disposition", "распоряж", "work order"),
    ),
    "equipment_commissioning": (
        "Ввод оборудования в работу",
        ("commissioning", "ввод оборудования", "ввод в работу"),
    ),
    "relay_automation": (
        "РЗА и телемеханика",
        ("relay protection", "telemechan", "rza", "рза", "телемехан"),
    ),
    "work_permit": (
        "Наряды, распоряжения и допуски",
        ("work_permit", "permit", "наряд", "допуск", "бригада"),
    ),
    "keys_journal": (
        "Журнал ключей",
        ("key_journal", "key issue", "журнал ключ", "возврат ключ"),
    ),
    "switching_documents": (
        "Документы переключений",
        ("switching", "переключ", "тбп", "тпп"),
    ),
    "equipment_registry": (
        "Оборудование и объекты диспетчеризации",
        ("equipment", "dispatching", "оборудован", "диспетчер", "щпт", "шот"),
    ),
    "personnel_rights": (
        "Персонал и права",
        ("personnel", "employee", "permission", "персонал", "прав"),
    ),
}


def python_inventory(root: Path) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "views": [],
        "forms": [],
        "services": [],
        "management_commands": [],
        "tests": [],
        "other_python": [],
    }
    for path in repo_files(root, {".py"}):
        rel = relative(path, root)
        lowered = f"/{rel.lower()}/"
        if path.name.lower() == "views.py" or "/views/" in lowered:
            category = "views"
        elif path.name.lower() == "forms.py" or "/forms/" in lowered:
            category = "forms"
        elif path.name.lower() == "services.py" or "/services/" in lowered:
            category = "services"
        elif "/management/commands/" in lowered:
            category = "management_commands"
        elif path.name.lower().startswith("test") or "/tests/" in lowered:
            category = "tests"
        else:
            category = "other_python"
        try:
            tree = ast.parse(read_text(path), filename=rel)
            classes = [
                {"name": node.name, "line": node.lineno}
                for node in tree.body
                if isinstance(node, ast.ClassDef)
            ]
            functions = [
                {"name": node.name, "line": node.lineno}
                for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            ]
            test_methods = sum(
                1
                for node in ast.walk(tree)
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name.startswith("test")
            )
            parse_error = None
        except SyntaxError as exc:
            classes, functions, test_methods = [], [], 0
            parse_error = str(exc)
        groups[category].append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": digest(path.read_bytes()),
                "classes": classes,
                "functions": functions,
                "test_method_count": test_methods,
                "parse_error": parse_error,
            }
        )
    for rows in groups.values():
        rows.sort(key=lambda item: item["path"])
    return groups


def asset_inventory(root: Path) -> dict[str, list[dict[str, Any]]]:
    groups = {
        "templates": [],
        "javascript": [],
        "stylesheets": [],
        "fixtures": [],
        "presentation_candidates": [],
    }
    presentation_tokens = ("fixture", "presentation", "demo", "seed", "sample", "import")
    for path in repo_files(root):
        rel = relative(path, root)
        payload = path.read_bytes()
        row = {
            "path": rel,
            "bytes": len(payload),
            "sha256": digest(payload),
            "lines": payload.count(b"\n") + (1 if payload else 0),
        }
        suffix = path.suffix.lower()
        if suffix == ".html":
            groups["templates"].append(row)
        elif suffix == ".js":
            groups["javascript"].append(row)
        elif suffix == ".css":
            groups["stylesheets"].append(row)
        elif suffix == ".json" and "fixture" in rel.lower():
            groups["fixtures"].append(row)
        if any(token in rel.lower() for token in presentation_tokens):
            groups["presentation_candidates"].append(row)
    for rows in groups.values():
        rows.sort(key=lambda item: item["path"])
    return groups


def fixture_inventory(root: Path, rows: list[dict[str, Any]]) -> dict[str, Any]:
    totals: Counter[str] = Counter()
    files = []
    for row in rows:
        path = root / row["path"]
        try:
            payload = json.loads(read_text(path))
        except (OSError, json.JSONDecodeError) as exc:
            files.append({"path": row["path"], "error": f"{exc.__class__.__name__}: {exc}"})
            continue
        if not isinstance(payload, list):
            files.append({"path": row["path"], "error": "fixture root is not a list"})
            continue
        counts: Counter[str] = Counter()
        for item in payload:
            if isinstance(item, dict) and isinstance(item.get("model"), str):
                counts[item["model"]] += 1
                totals[item["model"]] += 1
        files.append(
            {
                "path": row["path"],
                "objects": sum(counts.values()),
                "models": dict(sorted(counts.items())),
            }
        )
    return {
        "files": files,
        "total_objects": sum(totals.values()),
        "models": dict(sorted(totals.items())),
    }


def documentation_inventory(root: Path, main_head: str, baseline: str) -> dict[str, Any]:
    rows = []
    missing = []
    for rel in MANDATORY_DOCS:
        path = root / rel
        if not path.is_file():
            missing.append(rel)
            continue
        content = read_text(path)
        shas = sorted(set(SHA_RE.findall(content)))
        lowered = content.lower()
        rows.append(
            {
                "path": rel,
                "bytes": path.stat().st_size,
                "sha256": digest(path.read_bytes()),
                "mentioned_shas": shas,
                "mentions_main_head": main_head in shas,
                "mentions_baseline": baseline in shas,
                "stale_auto001_claim": (
                    "auto-001" in lowered
                    and any(
                        token in lowered
                        for token in ("not started", "absent", "отсутств")
                    )
                ),
            }
        )
    automation = [
        {
            "path": relative(path, root),
            "bytes": path.stat().st_size,
            "sha256": digest(path.read_bytes()),
        }
        for path in sorted((root / "docs/automation").glob("*.md"))
    ]
    return {
        "mandatory_files": rows,
        "missing_mandatory_files": missing,
        "automation_files": automation,
        "stale_auto001_claim_files": [
            row["path"] for row in rows if row["stale_auto001_claim"]
        ],
    }


def domain_hits(root: Path, limit: int = 160) -> dict[str, list[dict[str, Any]]]:
    result = {area: [] for area in DOMAIN_AREAS}
    for path in repo_files(root, TEXT_SUFFIXES):
        if path.stat().st_size > 2_000_000:
            continue
        rel = relative(path, root)
        for number, line in enumerate(read_text(path).splitlines(), start=1):
            lowered = line.lower()
            for area, (_display, tokens) in DOMAIN_AREAS.items():
                if len(result[area]) >= limit:
                    continue
                token = next((item for item in tokens if item in lowered), None)
                if token is None:
                    continue
                excerpt = line.strip()[:240]
                if SECRET_KEY_RE.search(excerpt):
                    excerpt = "<redacted secret-like line>"
                result[area].append(
                    {
                        "area": area,
                        "path": rel,
                        "line": number,
                        "token": token,
                        "excerpt": sanitize_text(excerpt),
                    }
                )
    return result


def _classify(
    rows: Sequence[dict[str, Any]],
    fields: Sequence[str],
) -> dict[str, list[dict[str, Any]]]:
    result = {area: [] for area in DOMAIN_AREAS}
    for row in rows:
        text = " ".join(str(row.get(field) or "") for field in fields).lower()
        for area, (_display, tokens) in DOMAIN_AREAS.items():
            if any(token in text for token in tokens):
                result[area].append(row)
    return result


def build_evidence_matrix(
    model_rows: list[dict[str, Any]],
    migration_rows: dict[str, Any],
    route_rows: list[dict[str, Any]],
    python_rows: dict[str, list[dict[str, Any]]],
    assets: dict[str, list[dict[str, Any]]],
    commands: dict[str, dict[str, Any]],
    smoke: list[dict[str, Any]],
    hits: dict[str, list[dict[str, Any]]],
) -> list[dict[str, Any]]:
    maps = {
        "models": _classify(
            model_rows,
            ("label", "verbose_name", "verbose_name_plural", "source_file"),
        ),
        "routes": _classify(
            route_rows,
            ("route", "qualified_name", "callback", "lookup_str"),
        ),
        "services": _classify(python_rows["services"], ("path",)),
        "forms": _classify(python_rows["forms"], ("path",)),
        "views": _classify(python_rows["views"], ("path",)),
        "templates": _classify(assets["templates"], ("path",)),
        "tests": _classify(python_rows["tests"], ("path",)),
        "presentation": _classify(assets["presentation_candidates"], ("path",)),
    }
    gates_passed = all(
        not result["timed_out"] and result["returncode"] == 0
        for result in commands.values()
    )
    rows = []
    for area, (display, _tokens) in DOMAIN_AREAS.items():
        models = maps["models"][area]
        tests = maps["tests"][area]
        presentation_present = bool(maps["presentation"][area]) or any(
            (row.get("row_count") or 0) > 0 for row in models
        )
        deficits = []
        for key, label in (
            ("models", "models"),
            ("services", "services"),
            ("routes", "routes"),
            ("tests", "area-specific tests"),
        ):
            if not maps[key][area]:
                deficits.append(f"{label} not classified automatically")
        if not presentation_present:
            deficits.append("presentation data not evidenced automatically")
        deficits.append("manual domain acceptance requires Chat 0 review")
        rows.append(
            {
                "area": area,
                "requirement": display,
                "models": [row["label"] for row in models],
                "migration_disk_total": len(migration_rows["disk"]),
                "pending_migrations_total": len(migration_rows["pending"]),
                "services": [row["path"] for row in maps["services"][area]],
                "forms": [row["path"] for row in maps["forms"][area]],
                "views": [row["path"] for row in maps["views"][area]],
                "routes": [
                    row["qualified_name"] or row["route"]
                    for row in maps["routes"][area]
                ],
                "templates": [row["path"] for row in maps["templates"][area]],
                "test_files": [row["path"] for row in tests],
                "static_test_method_count": sum(
                    row["test_method_count"] for row in tests
                ),
                "global_executed_test_count": commands["django_tests"][
                    "executed_test_count"
                ],
                "presentation_files": [
                    row["path"] for row in maps["presentation"][area]
                ],
                "classified_row_count": sum(
                    row["row_count"] or 0 for row in models
                ),
                "runtime_evidence": (
                    "global executable gates passed"
                    if gates_passed
                    else "global gates failed"
                ),
                "runtime_smoke": smoke,
                "subject_acceptance": "not established by automatic audit",
                "text_hit_count": len(hits[area]),
                "presentation_present": presentation_present,
                "remaining_deficit": deficits,
            }
        )
    return rows
