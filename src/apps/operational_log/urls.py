from django.urls import path

from . import views

app_name = "operational_log"

urlpatterns = [
    path("operations/journal/", views.registry, name="registry"),
    path(
        "operations/journal/<int:journal_id>/display/",
        views.update_display,
        name="update_display",
    ),
    path("operations/journal/<int:journal_id>/", views.detail, name="detail"),
]
