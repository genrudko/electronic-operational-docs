from __future__ import annotations

import inspect
import os
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from .core import relative


def setup_django(app_root: Path) -> Any:
    sys.path.insert(0, str(app_root / "src"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "eod_config.settings")
    import django

    django.setup()
    return django


def _default_repr(field: Any) -> str | None:
    try:
        if not field.has_default():
            return None
        value = field.default
        if callable(value):
            name = getattr(value, "__qualname__", value.__class__.__name__)
            return f"{value.__module__}.{name}"
        return repr(value)[:200]
    except (AttributeError, TypeError, ValueError) as exc:
        return f"<unavailable:{exc.__class__.__name__}>"


def app_and_model_inventory(
    app_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    from django.apps import apps
    from django.db import connection

    tables = set(connection.introspection.table_names())
    app_rows: list[dict[str, Any]] = []
    model_rows: list[dict[str, Any]] = []
    for config in sorted(apps.get_app_configs(), key=lambda item: item.label):
        models = sorted(config.get_models(), key=lambda item: item._meta.label_lower)
        migration_dir = Path(config.path) / "migrations"
        app_rows.append(
            {
                "label": config.label,
                "name": config.name,
                "verbose_name": str(config.verbose_name),
                "path": relative(Path(config.path), app_root),
                "model_count": len(models),
                "migration_files": sorted(
                    path.name
                    for path in migration_dir.glob("[0-9][0-9][0-9][0-9]_*.py")
                ),
            }
        )
        for model in models:
            meta = model._meta
            fields = []
            for field in meta.get_fields(include_parents=True, include_hidden=False):
                related_model = getattr(field, "related_model", None)
                fields.append(
                    {
                        "name": field.name,
                        "type": field.__class__.__name__,
                        "related_model": (
                            related_model._meta.label_lower if related_model else None
                        ),
                        "many_to_many": bool(getattr(field, "many_to_many", False)),
                        "one_to_many": bool(getattr(field, "one_to_many", False)),
                        "many_to_one": bool(getattr(field, "many_to_one", False)),
                        "one_to_one": bool(getattr(field, "one_to_one", False)),
                        "null": bool(getattr(field, "null", False)),
                        "blank": bool(getattr(field, "blank", False)),
                        "primary_key": bool(getattr(field, "primary_key", False)),
                        "unique": bool(getattr(field, "unique", False)),
                        "db_index": bool(getattr(field, "db_index", False)),
                        "editable": bool(getattr(field, "editable", False)),
                        "default": _default_repr(field),
                    }
                )
            constraints = [
                {
                    "name": getattr(item, "name", ""),
                    "type": item.__class__.__name__,
                    "fields": list(getattr(item, "fields", ()) or ()),
                    "condition": str(getattr(item, "condition", "") or ""),
                }
                for item in meta.constraints
            ]
            indexes = [
                {
                    "name": getattr(item, "name", ""),
                    "type": item.__class__.__name__,
                    "fields": list(getattr(item, "fields", ()) or ()),
                    "condition": str(getattr(item, "condition", "") or ""),
                }
                for item in meta.indexes
            ]
            row_count = None
            count_error = None
            if meta.managed and not meta.proxy and meta.db_table in tables:
                try:
                    row_count = int(model._default_manager.count())
                except Exception as exc:  # noqa: BLE001
                    count_error = f"{exc.__class__.__name__}: {exc}"
            source = inspect.getsourcefile(model)
            model_rows.append(
                {
                    "label": meta.label_lower,
                    "app_label": meta.app_label,
                    "verbose_name": str(meta.verbose_name),
                    "verbose_name_plural": str(meta.verbose_name_plural),
                    "db_table": meta.db_table,
                    "db_table_exists": meta.db_table in tables,
                    "managed": bool(meta.managed),
                    "proxy": bool(meta.proxy),
                    "source_file": relative(Path(source), app_root) if source else None,
                    "fields": fields,
                    "constraints": constraints,
                    "indexes": indexes,
                    "row_count": row_count,
                    "count_error": count_error,
                }
            )
    return app_rows, model_rows


def migration_inventory() -> dict[str, Any]:
    from django.db import connection
    from django.db.migrations.executor import MigrationExecutor
    from django.db.migrations.loader import MigrationLoader
    from django.db.migrations.recorder import MigrationRecorder

    loader = MigrationLoader(connection, ignore_no_migrations=True)
    executor = MigrationExecutor(connection)
    return {
        "applied": sorted(
            [list(item) for item in MigrationRecorder(connection).applied_migrations()]
        ),
        "disk": sorted([list(item) for item in loader.disk_migrations]),
        "leaf_nodes": sorted([list(item) for item in loader.graph.leaf_nodes()]),
        "pending": [
            [migration.app_label, migration.name, bool(backwards)]
            for migration, backwards in executor.migration_plan(
                executor.loader.graph.leaf_nodes()
            )
        ],
    }


def route_inventory() -> list[dict[str, Any]]:
    from django.urls import URLPattern, URLResolver, get_resolver

    rows: list[dict[str, Any]] = []

    def walk(
        patterns: Iterable[Any],
        prefix: str = "",
        namespaces: tuple[str, ...] = (),
    ) -> None:
        for entry in patterns:
            route = prefix + str(entry.pattern)
            if isinstance(entry, URLPattern):
                callback = entry.callback
                callback_name = getattr(
                    callback,
                    "__qualname__",
                    getattr(callback, "__name__", repr(callback)),
                )
                module = getattr(callback, "__module__", "")
                rows.append(
                    {
                        "route": route,
                        "name": entry.name,
                        "namespace": ":".join(namespaces),
                        "qualified_name": (
                            ":".join((*namespaces, entry.name)) if entry.name else None
                        ),
                        "callback": f"{module}.{callback_name}".strip("."),
                        "lookup_str": getattr(entry, "lookup_str", ""),
                    }
                )
            elif isinstance(entry, URLResolver):
                nested = (*namespaces, entry.namespace) if entry.namespace else namespaces
                walk(entry.url_patterns, route, nested)

    walk(get_resolver().url_patterns)
    return sorted(rows, key=lambda item: (item["route"], item["qualified_name"] or ""))


def database_inventory() -> dict[str, Any]:
    from django.conf import settings
    from django.db import connection

    with connection.cursor() as cursor:
        cursor.execute("SELECT current_database()")
        database = cursor.fetchone()[0]
        cursor.execute("SHOW server_version")
        version = cursor.fetchone()[0]
    return {
        "engine": settings.DATABASES["default"].get("ENGINE"),
        "current_database": database,
        "vendor": connection.vendor,
        "server_version": version,
        "timezone": str(settings.TIME_ZONE),
        "deployment_mode": os.environ.get("EOD_DEPLOYMENT_MODE"),
        "database_profile": os.environ.get("EOD_DATABASE_PROFILE"),
        "tables": sorted(connection.introspection.table_names()),
    }


def runtime_smoke() -> list[dict[str, Any]]:
    from django.test import Client

    client = Client(HTTP_HOST="localhost")
    rows = []
    for path in ("/_health/", "/accounts/login/", "/"):
        try:
            response = client.get(path, follow=False)
            rows.append(
                {
                    "path": path,
                    "status_code": response.status_code,
                    "location": response.headers.get("Location", ""),
                }
            )
        except Exception as exc:  # noqa: BLE001
            rows.append({"path": path, "error": f"{exc.__class__.__name__}: {exc}"})
    return rows
