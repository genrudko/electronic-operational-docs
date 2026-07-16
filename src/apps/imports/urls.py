from django.urls import path

from . import views

app_name = "imports"

urlpatterns = [
    path("imports/", views.import_list, name="list"),
    path("imports/upload/", views.import_upload, name="upload"),
    path("imports/<uuid:public_id>/", views.import_detail, name="detail"),
    path(
        "imports/<uuid:public_id>/discard/",
        views.import_discard,
        name="discard",
    ),
]
