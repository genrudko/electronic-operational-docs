from __future__ import annotations

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.organizations.models import Employee, Organization, Role, Substitution


def home(request):
    organization_stats = None
    if request.user.is_authenticated:
        today = timezone.localdate()
        organization_stats = {
            "organizations": Organization.objects.filter(is_active=True).count(),
            "employees": Employee.objects.filter(is_active=True).count(),
            "roles": Role.objects.filter(is_active=True).count(),
            "substitutions": Substitution.objects.filter(
                is_active=True,
                valid_from__lte=today,
                valid_until__gte=today,
            ).count(),
        }
    return render(
        request,
        "system/home.html",
        {
            "server_time": timezone.localtime(),
            "project_version": "0.2.0-dev",
            "database_vendor": connection.vendor,
            "organization_stats": organization_stats,
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
