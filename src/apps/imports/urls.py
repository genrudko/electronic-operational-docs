from django.urls import path

from . import views

app_name = "imports"

urlpatterns = [
    path("imports/", views.import_list, name="list"),
    path("imports/upload/", views.import_upload, name="upload"),
    path("imports/<uuid:public_id>/", views.import_detail, name="detail"),
    path(
        "imports/<uuid:public_id>/mapping/",
        views.import_mapping,
        name="mapping",
    ),
    path(
        "imports/<uuid:public_id>/rows/<int:row_id>/edit/",
        views.import_row_edit,
        name="row_edit",
    ),
    path(
        "imports/<uuid:public_id>/rows/<int:row_id>/decision/",
        views.import_row_decide,
        name="row_decide",
    ),
    path(
        "imports/<uuid:public_id>/bulk-decision/",
        views.import_bulk_decide,
        name="bulk_decide",
    ),
    path(
        "imports/<uuid:public_id>/discard/",
        views.import_discard,
        name="discard",
    ),
]
