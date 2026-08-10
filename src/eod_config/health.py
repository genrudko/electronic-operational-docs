from __future__ import annotations

from django.db import connection as django_connection
from django.db.migrations.executor import MigrationExecutor
from django.http import JsonResponse


class _DatabaseHealthConnection:
    """Narrow database seam for deployment health probes."""

    def cursor(self):
        return django_connection.cursor()


# Keep health-probe patching isolated from Django's global connection wrapper.
connection = _DatabaseHealthConnection()


def liveness(_request):
    """Process-only liveness: never depends on database or external services."""

    return JsonResponse({"status": "alive"})


def _deployment_dependencies_ready() -> bool:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        cursor.fetchone()

    executor = MigrationExecutor(django_connection)
    targets = executor.loader.graph.leaf_nodes()
    return not executor.migration_plan(targets)


def readiness(_request):
    """Bounded readiness for mandatory repository-owned deployment dependencies."""

    try:
        ready = _deployment_dependencies_ready()
    except Exception:  # noqa: BLE001 - health response must not disclose backend details.
        ready = False
    if not ready:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ready"})


def health(_request):
    """Backward-compatible DB-backed health endpoint with the historic success payload."""

    try:
        ready = _deployment_dependencies_ready()
    except Exception:  # noqa: BLE001 - health response must not disclose backend details.
        ready = False
    if not ready:
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
