from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.dispatching.models import ManagementRevision, PublicationStatus
from apps.documents.models import Document
from apps.equipment.models import EquipmentAsset
from apps.organizations.models import Employee, Organization


def _database_context() -> dict[str, str]:
    database_name = connection.settings_dict.get("NAME", "")
    database_file = Path(str(database_name)).name if database_name else "не определён"
    legacy_profile = "postgresql" if connection.vendor == "postgresql" else "development"
    return {
        # Keep the historical API field for existing health checks and integrations.
        "profile": legacy_profile,
        # The explicit database profile distinguishes presentation, gate and override modes.
        "database_profile": getattr(settings, "EOD_DATABASE_PROFILE", "unknown"),
        "database_file": database_file,
        "database_vendor": connection.vendor,
    }


def home(request):
    system_stats = None
    if request.user.is_authenticated:
        system_stats = {
            "organizations": Organization.objects.filter(is_active=True).count(),
            "employees": Employee.objects.filter(is_active=True).count(),
            "drafts": Document.objects.filter(status=Document.Status.DRAFT).count(),
            "registered": Document.objects.filter(status=Document.Status.REGISTERED).count(),
            "equipment": EquipmentAsset.objects.filter(status=EquipmentAsset.Status.ACTIVE).count(),
            "management": ManagementRevision.objects.filter(
                status=PublicationStatus.PUBLISHED
            ).count(),
        }
    return render(
        request,
        "system/home.html",
        {
            "server_time": timezone.localtime(),
            "project_version": "0.3.2-dev",
            "system_stats": system_stats,
            **_database_context(),
        },
    )


def health(request):
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        database_ok = cursor.fetchone() == (1,)
    return JsonResponse(
        {
            "status": "ok" if database_ok else "degraded",
            "database": database_ok,
            **_database_context(),
            "server_time": timezone.now().isoformat(),
            "local_server_time": timezone.localtime().isoformat(),
            "time_zone": str(timezone.get_current_timezone()),
        },
        status=200 if database_ok else 503,
    )
