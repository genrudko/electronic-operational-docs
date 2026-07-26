from django.contrib import admin
from django.urls import include, path

from eod_config.health import health

urlpatterns = [
    path("_health/", health, name="health"),
    path("admin/", admin.site.urls),
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
