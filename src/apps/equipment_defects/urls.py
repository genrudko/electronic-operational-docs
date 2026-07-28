from django.urls import path

from . import views

app_name = "equipment_defects"

urlpatterns = [
    path("operations/defects/", views.registry, name="registry"),
    path("operations/defects/new/", views.create, name="create"),
    path(
        "operations/defects/new/from-operational-log/<int:entry_id>/",
        views.create_from_operational_log,
        name="create_from_operational_log",
    ),
    path("operations/defects/print/", views.print_view, name="print"),
    path(
        "operations/defects/<uuid:public_id>/",
        views.detail,
        name="detail",
    ),
    path(
        "operations/defects/<uuid:public_id>/deadline/",
        views.confirm_deadline_view,
        name="confirm_deadline",
    ),
    path(
        "operations/defects/<uuid:public_id>/deadline/extend/",
        views.extend_deadline_view,
        name="extend_deadline",
    ),
    path(
        "operations/defects/<uuid:public_id>/resolution/",
        views.confirm_resolution_view,
        name="confirm_resolution",
    ),
    path(
        "operations/defects/<uuid:public_id>/acknowledge/",
        views.acknowledge_view,
        name="acknowledge",
    ),
    path(
        "operations/defects/<uuid:public_id>/close/",
        views.close_view,
        name="close",
    ),
]
