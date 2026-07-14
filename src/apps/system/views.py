from __future__ import annotations

from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone


def home(request):
    return render(
        request,
        "system/home.html",
        {
            "server_time": timezone.localtime(),
            "project_version": "0.1.1-dev",
            "database_vendor": connection.vendor,
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
            "profile": "development" if connection.vendor == "sqlite" else "postgresql",
        },
        status=200 if database_ok else 503,
    )
