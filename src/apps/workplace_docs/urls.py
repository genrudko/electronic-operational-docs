from django.urls import path

from . import views

app_name = "workplace_docs"

urlpatterns = [
    path("workplace-documentation/", views.registry, name="registry"),
    path("workplace-documentation/<int:list_id>/", views.detail, name="detail"),
    path(
        "workplace-documentation/<int:list_id>/revisions/<int:revision_number>/",
        views.detail,
        name="revision_detail",
    ),
]
