from __future__ import annotations

from django.conf import settings
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


def _development_authentication_ready() -> bool:
    if settings.EOD_DEPLOYMENT_MODE != "development":
        return True
    try:
        from apps.organizations.development_auth_smoke import (
            verify_development_demo_authentication_state,
        )

        return verify_development_demo_authentication_state()
    except Exception:  # noqa: BLE001 - never disclose credential/auth details via health.
        return False


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
    """Trusted deployment health including Development demo auth state."""

    try:
        ready = _deployment_dependencies_ready()
    except Exception:  # noqa: BLE001 - health response must not disclose backend details.
        ready = False
    if not ready:
        return JsonResponse({"status": "unavailable"}, status=503)
    if not _development_authentication_ready():
        return JsonResponse(
            {"status": "unavailable", "development_authentication": "failed"},
            status=503,
        )
    payload = {"status": "ok"}
    if settings.EOD_DEPLOYMENT_MODE == "development":
        payload["development_authentication"] = "verified"
    return JsonResponse(payload)
