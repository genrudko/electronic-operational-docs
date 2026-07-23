from django.urls import path

from . import views

app_name = "operational_documents"

urlpatterns = [
    path("operational-documents/", views.registry, name="registry"),
    path("operational-documents/types/", views.type_registry, name="type_registry"),
    path("operational-documents/types/new/", views.type_create, name="type_create"),
    path(
        "operational-documents/types/<uuid:public_id>/",
        views.type_detail,
        name="type_detail",
    ),
    path("operational-documents/new/", views.record_choose_type, name="record_choose_type"),
    path(
        "operational-documents/new/<uuid:type_public_id>/",
        views.record_create,
        name="record_create",
    ),
    path(
        "operational-documents/<uuid:public_id>/",
        views.record_detail,
        name="record_detail",
    ),
    path(
        "operational-documents/<uuid:public_id>/edit/",
        views.record_edit,
        name="record_edit",
    ),
    path(
        "operational-documents/<uuid:public_id>/transition/",
        views.record_transition,
        name="record_transition",
    ),
]
