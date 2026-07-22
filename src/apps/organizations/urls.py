from django.urls import path

from . import views

app_name = "organizations"

urlpatterns = [
    path("accounts/login/", views.PersonalLoginView.as_view(), name="login"),
    path("accounts/logout/", views.personal_logout, name="logout"),
    path("accounts/me/", views.account, name="account"),
    path("organization/", views.directory, name="directory"),
    path(
        "organization/employees/<uuid:public_id>/",
        views.employee_detail,
        name="employee_detail",
    ),
]
