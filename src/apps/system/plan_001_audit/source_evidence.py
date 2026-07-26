from __future__ import annotations

import ast
import json
import re
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
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

PRESENT = "present"
ABSENT = "absent"
UNKNOWN = "unknown"
NOT_APPLICABLE = "not applicable"

COMPONENTS = (
    "models",
    "services",
    "forms",
    "views",
    "routes",
    "templates",
    "tests",
    "presentation",
)

CHAT0_INTEGRATION_DECISION = {
    "source": "Постоянный интеграционный Чат 0",
    "decision_date": "2026-07-26",
    "evidence_exact_head": "fb313f270254720b0f7d7815fffc2cb05d577901",
    "evidence_package_sha256": (
        "58df47f83d1758d2e6aa8b32e1d5a70efb8c453454d8759e25d913e7f031619a"
    ),
    "machine_verdict": False,
    "verdicts": (
        {
            "area": "generic structured-journal core",
            "verdict": "SUBSTANTIALLY IMPLEMENTED",
        },
        {
            "area": "structured journals pack",
            "verdict": "NOT COMPLETE",
        },
        {
            "area": "operational journal",
            "verdict": "ADVANCED BUT LIFECYCLE INCOMPLETE",
        },
        {
            "area": "work permits/orders",
            "verdict": "NOT IMPLEMENTED AS VERTICAL SLICE",
        },
        {
            "area": "switching documents",
            "verdict": "NOT IMPLEMENTED AS VERTICAL SLICE",
        },
        {
            "area": "repeatable presentation dataset",
            "verdict": "BLOCKING GAP",
        },
        {
            "area": "recommended first vertical slice",
            "verdict": "DEFECT JOURNAL",
        },
    ),
}


@dataclass(frozen=True, slots=True)
class DomainOwnership:
    display: str
    app_labels: tuple[str, ...] = ()
    model_label_prefixes: tuple[str, ...] = ()
    path_prefixes: tuple[str, ...] = ()
    exact_paths: tuple[str, ...] = ()
    route_namespaces: tuple[str, ...] = ()
    source_bound_codes: tuple[str, ...] = ()
    not_applicable_components: tuple[str, ...] = ()
    absence_is_conclusive: bool = False
    evidence_note: str = ""


DOMAIN_OWNERSHIP: dict[str, DomainOwnership] = {
    "structured_journal_core": DomainOwnership(
        display="Общее ядро структурированных журналов",
        app_labels=("operational_documents",),
        path_prefixes=("src/apps/operational_documents/",),
        route_namespaces=("operational_documents",),
        evidence_note="Explicit owner: apps.operational_documents.",
    ),
    "operational_journal": DomainOwnership(
        display="Оперативный журнал",
        app_labels=("operational_log",),
        path_prefixes=("src/apps/operational_log/",),
        route_namespaces=("operational_log",),
        evidence_note="Explicit owner: apps.operational_log.",
    ),
    "equipment_dispatching": DomainOwnership(
        display="Оборудование и объекты диспетчеризации",
        app_labels=("equipment", "dispatching"),
        model_label_prefixes=("imports.powersystem",),
        path_prefixes=("src/apps/equipment/", "src/apps/dispatching/"),
        exact_paths=("src/apps/imports/services.py",),
        route_namespaces=("equipment", "dispatching"),
        evidence_note=(
            "Explicit owners: apps.equipment, apps.dispatching and power-system "
            "import models."
        ),
    ),
    "personnel_rights": DomainOwnership(
        display="Персонал, рабочие места и оперативные права",
        app_labels=("organizations",),
        model_label_prefixes=("imports.personnel",),
        path_prefixes=("src/apps/organizations/",),
        exact_paths=("src/apps/imports/services.py",),
        route_namespaces=("organizations",),
        evidence_note=(
            "Explicit owner: apps.organizations plus personnel import models."
        ),
    ),
    "workplace_documents": DomainOwnership(
        display="Документация рабочего места",
        app_labels=("workplace_docs",),
        model_label_prefixes=("imports.workplacedocument",),
        path_prefixes=("src/apps/workplace_docs/",),
        exact_paths=("src/apps/imports/services.py",),
        route_namespaces=("workplace_docs",),
        evidence_note=(
            "Explicit owner: apps.workplace_docs plus workplace-document import models."
        ),
    ),
    "defect_journal": DomainOwnership(
        display="Журнал дефектов оборудования",
        source_bound_codes=("journal-equipment-defects",),
        not_applicable_components=(
            "models",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
        ),
        evidence_note=(
            "Source-bound profile on the shared apps.operational_documents core."
        ),
    ),
    "application_journal": DomainOwnership(
        display="Журнал заявок на вывод из работы",
        source_bound_codes=("journal-outage-requests",),
        not_applicable_components=(
            "models",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
        ),
        evidence_note=(
            "Source-bound profile on the shared apps.operational_documents core."
        ),
    ),
    "disposition_journal": DomainOwnership(
        display="Журнал распоряжений",
        source_bound_codes=("journal-orders",),
        not_applicable_components=(
            "models",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
        ),
        evidence_note=(
            "Source-bound profile on the shared apps.operational_documents core."
        ),
    ),
    "equipment_commissioning": DomainOwnership(
        display="Журнал ввода оборудования в работу",
        source_bound_codes=("journal-equipment-commissioning",),
        not_applicable_components=(
            "models",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
        ),
        evidence_note=(
            "Source-bound profile on the shared apps.operational_documents core."
        ),
    ),
    "relay_automation": DomainOwnership(
        display="Журнал РЗА и телемеханики",
        source_bound_codes=("journal-rza-telemechanics",),
        not_applicable_components=(
            "models",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
        ),
        evidence_note=(
            "Source-bound profile on the shared apps.operational_documents core."
        ),
    ),
    "work_permit": DomainOwnership(
        display="Наряды, распоряжения и допуски",
        absence_is_conclusive=True,
        evidence_note=(
            "No explicit application owner or accepted source-bound profile is "
            "registered for this vertical slice."
        ),
    ),
    "keys_journal": DomainOwnership(
        display="Журнал выдачи и возврата ключей",
        not_applicable_components=COMPONENTS,
        evidence_note=(
            "Paper-first decision: a mandatory full electronic lifecycle is not "
            "applicable at this stage."
        ),
    ),
    "switching_documents": DomainOwnership(
        display="Документы переключений",
        absence_is_conclusive=True,
        evidence_note=(
            "No explicit application owner or accepted source-bound profile is "
            "registered for this vertical slice."
        ),
    ),
    "repeatable_presentation_dataset": DomainOwnership(
        display="Повторяемый presentation dataset",
        not_applicable_components=(
            "models",
            "services",
            "forms",
            "views",
            "routes",
            "templates",
            "tests",
        ),
        evidence_note=(
            "Measured through fixture/seed/reset evidence, not through domain model "
            "ownership."
        ),
    ),
}

DISCOVERY_TOKENS: dict[str, tuple[str, ...]] = {
    "structured_journal_core": ("operational_documents", "source-bound"),
    "operational_journal": ("operational_log", "оперативный журнал"),
    "defect_journal": ("journal-equipment-defects", "дефект"),
    "application_journal": ("journal-outage-requests", "журнал заявок"),
    "disposition_journal": ("journal-orders", "журнал распоряжений"),
    "equipment_commissioning": (
        "journal-equipment-commissioning",
        "ввод оборудования в работу",
    ),
    "relay_automation": ("journal-rza-telemechanics", "рза", "телемехан"),
    "work_permit": ("work_permit", "наряд-допуск"),
    "keys_journal": ("журнал ключей", "возврат ключ"),
    "switching_documents": ("switching_documents", "документы переключений"),
    "equipment_dispatching": ("apps.equipment", "apps.dispatching", "щпт", "шот"),
    "personnel_rights": ("apps.organizations", "оперативные права"),
    "workplace_documents": ("apps.workplace_docs", "документация рабочего места"),
    "repeatable_presentation_dataset": ("seed_demo_", "presentation reset"),
}
DISCOVERY_EXCLUDED_PREFIXES = (
    ".github/",
    "deploy/automation/",
    "docs/automation/",
    "scripts/automation/",
    "tests/automation/",
    "src/apps/system/plan_001_audit/",
)


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
    presentation_tokens = (
        "fixture",
        "presentation",
        "demo",
        "seed",
        "sample",
        "reset",
    )
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
            files.append(
                {
                    "path": row["path"],
                    "error": f"{exc.__class__.__name__}: {exc}",
                }
            )
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


def documentation_inventory(
    root: Path,
    main_head: str,
    baseline: str,
) -> dict[str, Any]:
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
                        for token in (
                            "auto-001 implementation отсутств",
                            "auto-001 — следующий",
                            "after auto-001",
                            "после auto-001",
                        )
                    )
                ),
                "mentions_plan001_acceptance": (
                    "plan-001 evidence" in lowered
                    and "accepted" in lowered
                ),
                "mentions_defect_selection": (
                    "defect journal" in lowered
                    or "журнал дефектов" in lowered
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
        "plan001_acceptance_files": [
            row["path"] for row in rows if row["mentions_plan001_acceptance"]
        ],
        "defect_selection_files": [
            row["path"] for row in rows if row["mentions_defect_selection"]
        ],
    }


def domain_hits(root: Path, limit: int = 120) -> dict[str, list[dict[str, Any]]]:
    """Return discovery-only text references.

    These references are never used to establish implementation ownership or
    readiness. Broad words such as application/order/work/switch/permit are not
    accepted as ownership evidence.
    """

    result = {area: [] for area in DOMAIN_OWNERSHIP}
    for path in repo_files(root, TEXT_SUFFIXES):
        if path.stat().st_size > 2_000_000:
            continue
        rel = relative(path, root)
        if rel.startswith(DISCOVERY_EXCLUDED_PREFIXES):
            continue
        for number, line in enumerate(read_text(path).splitlines(), start=1):
            lowered = line.lower()
            for area, tokens in DISCOVERY_TOKENS.items():
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
                        "evidence_role": "discovery_only",
                    }
                )
    return result


def source_bound_code_references(
    root: Path,
    codes: Iterable[str],
) -> dict[str, list[dict[str, Any]]]:
    result = {code: [] for code in codes}
    allowed_prefix = "src/apps/operational_documents/"
    for path in repo_files(root, {".py", ".html", ".js"}):
        rel = relative(path, root)
        if not rel.startswith(allowed_prefix):
            continue
        lines = read_text(path).splitlines()
        for code in result:
            for number, line in enumerate(lines, start=1):
                if code not in line:
                    continue
                result[code].append(
                    {
                        "path": rel,
                        "line": number,
                        "excerpt": sanitize_text(line.strip()[:240]),
                        "is_test": "/tests/" in f"/{rel}/"
                        or Path(rel).name.startswith("test"),
                    }
                )
    return result


def _owned_model(row: Mapping[str, Any], ownership: DomainOwnership) -> bool:
    app_label = str(row.get("app_label") or "")
    label = str(row.get("label") or "")
    return app_label in ownership.app_labels or any(
        label.startswith(prefix) for prefix in ownership.model_label_prefixes
    )


def _owned_path(path: str, ownership: DomainOwnership) -> bool:
    return path in ownership.exact_paths or path.startswith(ownership.path_prefixes)


def _owned_route(row: Mapping[str, Any], ownership: DomainOwnership) -> bool:
    namespace = str(row.get("namespace") or "")
    callback = str(row.get("callback") or "")
    if any(
        namespace == item or namespace.startswith(f"{item}:")
        for item in ownership.route_namespaces
    ):
        return True
    return any(callback.startswith(f"apps.{label}.") for label in ownership.app_labels)


def _component(
    *,
    items: Sequence[Any],
    applicable: bool,
    conclusive: bool,
    reason: str,
) -> dict[str, Any]:
    if not applicable:
        status = NOT_APPLICABLE
    elif items:
        status = PRESENT
    elif conclusive:
        status = ABSENT
    else:
        status = UNKNOWN
    return {
        "status": status,
        "count": len(items) if status != UNKNOWN else None,
        "items": list(items),
        "reason": reason,
    }


def _journal_runtime(
    runtime_rows: Sequence[Mapping[str, Any]],
    code: str,
) -> dict[str, Any]:
    row = next((dict(item) for item in runtime_rows if item.get("code") == code), None)
    if row is None:
        return {
            "code": code,
            "catalog_state": UNKNOWN,
            "published_type_state": UNKNOWN,
            "records_state": UNKNOWN,
            "catalog_present": None,
            "published_type_count": None,
            "record_count": None,
            "reason": "runtime source-bound inventory did not return this code",
        }
    catalog_present = bool(row.get("catalog_present"))
    published_count = int(row.get("published_type_count") or 0)
    record_count = int(row.get("record_count") or 0)
    return {
        **row,
        "catalog_state": PRESENT if catalog_present else ABSENT,
        "published_type_state": PRESENT if published_count else ABSENT,
        "records_state": PRESENT if record_count else ABSENT,
    }


def classify_runtime_data(
    model_rows: Sequence[Mapping[str, Any]],
    assets: Mapping[str, Sequence[Mapping[str, Any]]],
    source_bound_runtime: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Classify runtime counts by provenance confidence.

    Model identity alone cannot prove that ordinary domain rows are canonical or
    presentation data. Unmarked rows therefore remain ``unknown`` rather than
    being promoted to canonical/presentation.
    """

    system_apps = {
        "admin",
        "auth",
        "contenttypes",
        "sessions",
        "system",
    }
    system_model_tokens = (
        "audit",
        "revision",
        "sequence",
        "event",
        "permission",
        "contenttype",
        "interfacepreference",
        "signedsnapshot",
    )
    canonical_publication_labels = {
        "imports.importpublication",
        "imports.importpublicationrow",
        "imports.personnelpublication",
        "imports.powersystempublication",
        "imports.workplacedocumentpublication",
    }
    classified = []
    totals: Counter[str] = Counter()
    for original in model_rows:
        row = dict(original)
        label = str(row.get("label") or "")
        app_label = str(row.get("app_label") or "")
        count = int(row.get("row_count") or 0)
        if label in canonical_publication_labels:
            data_class = "canonical"
            reason = "explicit publication model"
        elif app_label == "imports":
            data_class = "staging/import"
            reason = "explicit import/staging application"
        elif app_label in system_apps or any(
            token in label for token in system_model_tokens
        ):
            data_class = "system/internal"
            reason = "framework, audit, revision, sequence or internal metadata"
        else:
            data_class = "unknown"
            reason = "row provenance is not encoded; model identity is insufficient"
        classified.append(
            {
                "model": label,
                "app_label": app_label,
                "row_count": row.get("row_count"),
                "data_class": data_class,
                "classification_reason": reason,
            }
        )
        totals[data_class] += count

    canonical_source_bound_types = sum(
        int(row.get("published_type_count") or 0) for row in source_bound_runtime
    )
    canonical_source_bound_records = sum(
        int(row.get("record_count") or 0) for row in source_bound_runtime
    )
    if canonical_source_bound_types:
        totals["canonical"] += canonical_source_bound_types

    presentation_candidates = [
        str(row.get("path") or "")
        for row in assets.get("presentation_candidates", ())
        if "seed_demo_" in str(row.get("path") or "")
        or "presentation" in str(row.get("path") or "").lower()
    ]
    categories = {
        "canonical": {
            "status": PRESENT if totals["canonical"] else ABSENT,
            "row_count": totals["canonical"],
            "note": (
                "Only explicit publication rows and published source-bound type "
                "configuration are counted as canonical."
            ),
            "published_source_bound_type_count": canonical_source_bound_types,
            "source_bound_record_count_not_promoted": canonical_source_bound_records,
        },
        "staging/import": {
            "status": PRESENT if totals["staging/import"] else ABSENT,
            "row_count": totals["staging/import"],
            "note": "Import/staging rows do not prove a published canonical dataset.",
        },
        "presentation/demo": {
            "status": UNKNOWN,
            "row_count": None,
            "note": (
                "Seed/fixture code exists, but runtime rows do not carry reliable "
                "presentation provenance."
            ),
            "candidate_files": sorted(presentation_candidates),
        },
        "system/internal": {
            "status": PRESENT if totals["system/internal"] else ABSENT,
            "row_count": totals["system/internal"],
            "note": "Framework, audit, revision, sequence and internal metadata.",
        },
        "unknown": {
            "status": PRESENT if totals["unknown"] else ABSENT,
            "row_count": totals["unknown"],
            "note": "Ordinary runtime rows whose provenance cannot be proven.",
        },
    }
    return {
        "categories": categories,
        "models": sorted(classified, key=lambda item: item["model"]),
    }


def _owned_rows(
    ownership: DomainOwnership,
    model_rows: Sequence[Mapping[str, Any]],
    route_rows: Sequence[Mapping[str, Any]],
    python_rows: Mapping[str, Sequence[Mapping[str, Any]]],
    assets: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, list[Any]]:
    return {
        "models": [
            dict(row) for row in model_rows if _owned_model(row, ownership)
        ],
        "services": [
            dict(row)
            for row in python_rows["services"]
            if _owned_path(str(row.get("path") or ""), ownership)
        ],
        "forms": [
            dict(row)
            for row in python_rows["forms"]
            if _owned_path(str(row.get("path") or ""), ownership)
        ],
        "views": [
            dict(row)
            for row in python_rows["views"]
            if _owned_path(str(row.get("path") or ""), ownership)
        ],
        "routes": [
            dict(row) for row in route_rows if _owned_route(row, ownership)
        ],
        "templates": [
            dict(row)
            for row in assets["templates"]
            if _owned_path(str(row.get("path") or ""), ownership)
        ],
        "tests": [
            dict(row)
            for row in python_rows["tests"]
            if _owned_path(str(row.get("path") or ""), ownership)
        ],
        "presentation": [
            dict(row)
            for row in assets["presentation_candidates"]
            if _owned_path(str(row.get("path") or ""), ownership)
        ],
    }


def _paths(rows: Sequence[Mapping[str, Any]]) -> list[str]:
    return sorted({str(row.get("path") or "") for row in rows if row.get("path")})


def build_evidence_matrix(
    model_rows: list[dict[str, Any]],
    migration_rows: dict[str, Any],
    route_rows: list[dict[str, Any]],
    python_rows: dict[str, list[dict[str, Any]]],
    assets: dict[str, list[dict[str, Any]]],
    commands: dict[str, dict[str, Any]],
    smoke: list[dict[str, Any]],
    hits: dict[str, list[dict[str, Any]]],
    source_bound_runtime: list[dict[str, Any]] | None = None,
    source_bound_references: dict[str, list[dict[str, Any]]] | None = None,
) -> list[dict[str, Any]]:
    runtime_rows = source_bound_runtime or []
    references = source_bound_references or {}
    gates_passed = all(
        not result["timed_out"] and result["returncode"] == 0
        for result in commands.values()
    )
    rows = []
    for area, ownership in DOMAIN_OWNERSHIP.items():
        owned = _owned_rows(
            ownership,
            model_rows,
            route_rows,
            python_rows,
            assets,
        )
        source_profiles = [
            _journal_runtime(runtime_rows, code)
            for code in ownership.source_bound_codes
        ]
        exact_references = [
            reference
            for code in ownership.source_bound_codes
            for reference in references.get(code, ())
        ]
        exact_test_references = [
            item for item in exact_references if item.get("is_test")
        ]

        if ownership.source_bound_codes:
            owned["tests"] = exact_test_references
            owned["presentation"] = []
        elif area == "repeatable_presentation_dataset":
            seed_paths = [
                dict(row)
                for row in python_rows["management_commands"]
                if "seed_demo_" in str(row.get("path") or "")
            ]
            reset_paths = [
                dict(row)
                for row in python_rows["management_commands"]
                if "reset" in str(row.get("path") or "").lower()
                or "presentation" in str(row.get("path") or "").lower()
            ]
            owned["presentation"] = [*seed_paths, *reset_paths]

        component_states = {}
        for component in COMPONENTS:
            applicable = component not in ownership.not_applicable_components
            if ownership.source_bound_codes and component == "tests":
                conclusive = True
                reason = "exact approved form code references in profile tests"
            elif (
                area == "repeatable_presentation_dataset"
                and component == "presentation"
            ):
                conclusive = True
                reason = "explicit seed/reset management-command paths"
            else:
                conclusive = bool(
                    ownership.app_labels
                    or ownership.model_label_prefixes
                    or ownership.path_prefixes
                    or ownership.exact_paths
                    or ownership.route_namespaces
                    or ownership.absence_is_conclusive
                )
                reason = ownership.evidence_note
            if (
                area == "repeatable_presentation_dataset"
                and component == "presentation"
            ):
                seed_items = [
                    item
                    for item in owned[component]
                    if "seed_demo_" in str(item.get("path") or "")
                ]
                reset_items = [
                    item
                    for item in owned[component]
                    if "reset" in str(item.get("path") or "").lower()
                    or "presentation" in str(item.get("path") or "").lower()
                ]
                if seed_items and reset_items:
                    component_states[component] = _component(
                        items=owned[component],
                        applicable=True,
                        conclusive=True,
                        reason="explicit seed and reset commands",
                    )
                elif seed_items:
                    component_states[component] = {
                        "status": UNKNOWN,
                        "count": None,
                        "items": list(owned[component]),
                        "reason": (
                            "seed commands exist, but no unified repeatable reset "
                            "contract was classified"
                        ),
                    }
                else:
                    component_states[component] = _component(
                        items=(),
                        applicable=True,
                        conclusive=True,
                        reason="no explicit presentation seed/reset command",
                    )
            else:
                component_states[component] = _component(
                    items=owned[component],
                    applicable=applicable,
                    conclusive=conclusive,
                    reason=reason,
                )

        if ownership.source_bound_codes:
            catalog_states = [row["catalog_state"] for row in source_profiles]
            published_states = [row["published_type_state"] for row in source_profiles]
            record_states = [row["records_state"] for row in source_profiles]
            source_catalog_state = (
                PRESENT
                if PRESENT in catalog_states
                else ABSENT
                if catalog_states
                and all(item == ABSENT for item in catalog_states)
                else UNKNOWN
            )
            published_type_state = (
                PRESENT
                if PRESENT in published_states
                else ABSENT
                if published_states
                and all(item == ABSENT for item in published_states)
                else UNKNOWN
            )
            records_state = (
                PRESENT
                if PRESENT in record_states
                else ABSENT
                if record_states
                and all(item == ABSENT for item in record_states)
                else UNKNOWN
            )
        else:
            source_catalog_state = NOT_APPLICABLE
            published_type_state = NOT_APPLICABLE
            records_state = NOT_APPLICABLE

        deficits = []
        for component, payload in component_states.items():
            if payload["status"] == ABSENT:
                deficits.append(f"{component}: absent")
            elif payload["status"] == UNKNOWN:
                deficits.append(f"{component}: unknown")
        if ownership.source_bound_codes:
            if published_type_state != PRESENT:
                deficits.append(
                    "published source-bound type: "
                    f"{published_type_state}; catalog presence is not implementation"
                )
            if records_state != PRESENT:
                deficits.append(f"runtime records: {records_state}")
        deficits.append("subject acceptance is not established by automatic audit")

        rows.append(
            {
                "area": area,
                "requirement": ownership.display,
                "ownership": {
                    "app_labels": list(ownership.app_labels),
                    "model_label_prefixes": list(ownership.model_label_prefixes),
                    "path_prefixes": list(ownership.path_prefixes),
                    "exact_paths": list(ownership.exact_paths),
                    "route_namespaces": list(ownership.route_namespaces),
                    "source_bound_codes": list(ownership.source_bound_codes),
                    "note": ownership.evidence_note,
                },
                "component_states": component_states,
                "models": [row["label"] for row in owned["models"]],
                "services": _paths(owned["services"]),
                "forms": _paths(owned["forms"]),
                "views": _paths(owned["views"]),
                "routes": sorted(
                    {
                        str(row.get("qualified_name") or row.get("route") or "")
                        for row in owned["routes"]
                    }
                ),
                "templates": _paths(owned["templates"]),
                "test_files": _paths(owned["tests"]),
                "static_test_method_count": sum(
                    int(row.get("test_method_count") or 0)
                    for row in owned["tests"]
                ),
                "global_executed_test_count": commands["django_tests"][
                    "executed_test_count"
                ],
                "presentation_files": _paths(owned["presentation"]),
                "migration_disk_total": len(migration_rows["disk"]),
                "pending_migrations_total": len(migration_rows["pending"]),
                "source_bound_profiles": source_profiles,
                "source_catalog_state": source_catalog_state,
                "published_type_state": published_type_state,
                "records_state": records_state,
                "runtime_evidence": (
                    "global executable gates passed"
                    if gates_passed
                    else "global executable gates failed"
                ),
                "runtime_smoke": smoke,
                "subject_acceptance": "not established by automatic audit",
                "discovery_text_hit_count": len(hits.get(area, ())),
                "remaining_deficit": deficits,
            }
        )
    return rows
