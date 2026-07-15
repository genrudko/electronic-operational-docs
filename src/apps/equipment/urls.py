from django.urls import path

from . import views

app_name = "equipment"

urlpatterns = [
    path("equipment/", views.registry, name="registry"),
    path(
        "equipment/selector/options/",
        views.selector_options,
        name="selector_options",
    ),
    path("equipment/sites/<slug:code>/", views.site_detail, name="site_detail"),
    path("equipment/items/<uuid:public_id>/", views.equipment_detail, name="detail"),
]
