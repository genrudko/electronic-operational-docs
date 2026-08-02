from django.urls import path

from . import authority_views, personnel_management_views, views

app_name = "organizations"

urlpatterns = [
    path("accounts/login/", views.PersonalLoginView.as_view(), name="login"),
    path("accounts/logout/", views.personal_logout, name="logout"),
    path("accounts/me/", views.account, name="account"),
    path("organization/", views.directory, name="directory"),
    path(
        "organization/create/",
        personnel_management_views.organization_create,
        name="organization_create",
    ),
    path(
        "organization/<int:organization_id>/edit/",
        personnel_management_views.organization_edit,
        name="organization_edit",
    ),
    path(
        "organization/employees/create/",
        personnel_management_views.employee_create,
        name="employee_create",
    ),
    path(
        "organization/employees/<uuid:public_id>/edit/",
        personnel_management_views.employee_edit,
        name="employee_edit",
    ),
    path(
        "organization/employees/<uuid:public_id>/deactivate/",
        personnel_management_views.employee_deactivate,
        name="employee_deactivate",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/qualifications/electrical/create/",
        personnel_management_views.electrical_qualification_edit,
        name="electrical_qualification_create",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/qualifications/electrical/<uuid:record_public_id>/edit/",
        personnel_management_views.electrical_qualification_edit,
        name="electrical_qualification_edit",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/qualifications/special/create/",
        personnel_management_views.special_qualification_edit,
        name="special_qualification_create",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/qualifications/special/<uuid:record_public_id>/edit/",
        personnel_management_views.special_qualification_edit,
        name="special_qualification_edit",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/rights/create/",
        personnel_management_views.operational_right_edit,
        name="operational_right_create",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/rights/<uuid:record_public_id>/edit/",
        personnel_management_views.operational_right_edit,
        name="operational_right_edit",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/external-contacts/create/",
        personnel_management_views.external_contact_edit,
        name="external_contact_create",
    ),
    path(
        "organization/employees/<uuid:employee_public_id>/external-contacts/<uuid:record_public_id>/edit/",
        personnel_management_views.external_contact_edit,
        name="external_contact_edit",
    ),
    path(
        "organization/personnel-import/",
        personnel_management_views.personnel_import_upload,
        name="personnel_import_upload",
    ),
    path(
        "organization/personnel-import/template/<str:import_kind>/",
        personnel_management_views.personnel_import_template,
        name="personnel_import_template",
    ),
    path(
        "organization/personnel-import/<uuid:public_id>/",
        personnel_management_views.personnel_import_detail,
        name="personnel_import_detail",
    ),
    path(
        "organization/personnel-import/<uuid:public_id>/publish/",
        personnel_management_views.personnel_import_publish,
        name="personnel_import_publish",
    ),
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
