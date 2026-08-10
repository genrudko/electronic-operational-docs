from django.conf import settings
from django.contrib import admin
from django.urls import include, path

from eod_config.health import health, liveness, readiness


def build_urlpatterns(*, django_admin_enabled: bool):
    patterns = [
        path("_health/", health, name="health"),
        path("_health/live/", liveness, name="liveness"),
        path("_health/ready/", readiness, name="readiness"),
        path("", include("apps.organizations.urls")),
        path("", include("apps.documents.urls")),
        path("", include("apps.normatives.urls")),
        path("", include("apps.equipment.urls")),
        path("", include("apps.dispatching.urls")),
        path("", include("apps.imports.urls")),
        path("", include("apps.workplace_docs.urls")),
        path("", include("apps.operational_documents.urls")),
        path("", include("apps.equipment_defects.urls")),
        path("", include("apps.operational_log.urls")),
        path("", include("apps.system.urls")),
    ]
    if django_admin_enabled:
        patterns.insert(3, path("admin/", admin.site.urls))
    return patterns


urlpatterns = build_urlpatterns(
    django_admin_enabled=settings.EOD_DJANGO_ADMIN_ENABLED,
)
