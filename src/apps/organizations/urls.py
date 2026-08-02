from django.urls import path

from . import authority_views, views

app_name = "organizations"

urlpatterns = [
    path("accounts/login/", views.PersonalLoginView.as_view(), name="login"),
    path("accounts/logout/", views.personal_logout, name="logout"),
    path("accounts/me/", views.account, name="account"),
    path("organization/", views.directory, name="directory"),
    path(
        "organization/authorities/",
        authority_views.authority_registry,
        name="authority_registry",
    ),
    path(
        "organization/authority-evaluations/<uuid:public_id>/",
        authority_views.authority_evaluation_detail,
        name="authority_evaluation_detail",
    ),
    path(
        "organization/employees/<uuid:public_id>/",
        authority_views.employee_detail,
        name="employee_detail",
    ),
]
