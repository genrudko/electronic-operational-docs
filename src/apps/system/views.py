from __future__ import annotations

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.documents.models import Document
from apps.organizations.models import Employee, Organization


def home(request):
    system_stats = None
    if request.user.is_authenticated:
        system_stats = {
            "organizations": Organization.objects.filter(is_active=True).count(),
            "employees": Employee.objects.filter(is_active=True).count(),
            "drafts": Document.objects.filter(status=Document.Status.DRAFT).count(),
            "registered": Document.objects.filter(status=Document.Status.REGISTERED).count(),
        }
    return render(
        request,
        "system/home.html",
        {
            "server_time": timezone.localtime(),
            "project_version": "0.3.0-dev",
            "database_vendor": connection.vendor,
            "system_stats": system_stats,
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
            "database_vendor": connection.vendor,
            "server_time": timezone.now().isoformat(),
            "local_server_time": timezone.localtime().isoformat(),
            "time_zone": str(timezone.get_current_timezone()),
            "profile": "development" if connection.vendor == "sqlite" else "postgresql",
        },
        status=200 if database_ok else 503,
    )
