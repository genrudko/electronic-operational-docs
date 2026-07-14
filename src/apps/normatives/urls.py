from django.urls import path

from . import views

app_name = "normatives"

urlpatterns = [
    path("normatives/", views.registry, name="registry"),
    path("normatives/<slug:code>/", views.document_detail, name="document_detail"),
    path(
        "normatives/<slug:code>/revisions/<int:revision_number>/",
        views.revision_detail,
        name="revision_detail",
    ),
]
