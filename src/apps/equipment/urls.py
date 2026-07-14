from django.urls import path

from . import views

app_name = "equipment"

urlpatterns = [
    path("equipment/", views.registry, name="registry"),
    path("equipment/sites/<slug:code>/", views.site_detail, name="site_detail"),
    path("equipment/items/<uuid:public_id>/", views.equipment_detail, name="detail"),
]
