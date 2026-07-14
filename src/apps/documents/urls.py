from django.urls import path

from . import views

app_name = "documents"

urlpatterns = [
    path("documents/", views.document_list, name="list"),
    path("documents/new/", views.document_create, name="create"),
    path("documents/<uuid:public_id>/", views.document_detail, name="detail"),
    path("documents/<uuid:public_id>/edit/", views.document_edit, name="edit"),
    path("documents/<uuid:public_id>/register/", views.document_register, name="register"),
    path("documents/<uuid:public_id>/links/", views.document_link_create, name="link_create"),
]
