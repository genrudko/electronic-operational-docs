from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.organizations.urls")),
    path("", include("apps.documents.urls")),
    path("", include("apps.normatives.urls")),
    path("", include("apps.equipment.urls")),
    path("", include("apps.dispatching.urls")),
    path("", include("apps.system.urls")),
]
