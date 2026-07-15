from django.urls import path

from . import views

app_name = "dispatching"

urlpatterns = [
    path("dispatching/", views.registry, name="registry"),
    path("dispatching/subjects/", views.subjects, name="subjects"),
    path(
        "dispatching/equipment/<uuid:public_id>/",
        views.equipment_detail,
        name="equipment_detail",
    ),
]
