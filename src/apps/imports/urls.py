from django.urls import path

from . import views

app_name = "imports"

urlpatterns = [
    path("imports/power-system/", views.power_system_list, name="power_system_list"),
    path(
        "imports/power-system/upload/",
        views.power_system_upload,
        name="power_system_upload",
    ),
    path(
        "imports/power-system/<uuid:public_id>/",
        views.power_system_detail,
        name="power_system_detail",
    ),
    path(
        "imports/power-system/<uuid:public_id>/rows/<int:occurrence_id>/decision/",
        views.power_system_occurrence_decide,
        name="power_system_occurrence_decide",
    ),
    path(
        "imports/power-system/<uuid:public_id>/publication/",
        views.power_system_publication,
        name="power_system_publication",
    ),
    path(
        "imports/power-system/<uuid:public_id>/publication/<uuid:publication_id>/",
        views.power_system_publication_result,
        name="power_system_publication_result",
    ),
    path(
        "imports/power-system/<uuid:public_id>/discard/",
        views.power_system_discard,
        name="power_system_discard",
    ),
    path("imports/", views.import_list, name="list"),
    path("imports/data-profiles/", views.data_profile_list, name="data_profiles"),
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
        "imports/<uuid:public_id>/publication/",
        views.import_publication,
        name="publication",
    ),
    path(
        "imports/<uuid:public_id>/publication/result/",
        views.import_publication_result,
        name="publication_result",
    ),
    path(
        "imports/<uuid:public_id>/discard/",
        views.import_discard,
        name="discard",
    ),
]
