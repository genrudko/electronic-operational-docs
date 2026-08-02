from __future__ import annotations

from django import forms as django_forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import (
    DeactivationForm,
    EmployeeCardForm,
    EmployeeContactForm,
    EmployeeOperationalRightForm,
    EmployeeQualificationForm,
    EmployeeSpecialQualificationForm,
    ExternalOperationalContactForm,
    OrganizationOperationalProfileForm,
    PersonnelImportUploadForm,
)
from .models import (
    Employee,
    EmployeeOperationalRight,
    EmployeeQualification,
    Organization,
)
from .personnel_edit_services import (
    deactivate_employee,
    replace_electrical_qualification,
    replace_external_contact,
    replace_operational_right,
    replace_special_qualification,
)
from .personnel_management_models import (
    EmployeeContactProfile,
    EmployeeSpecialQualification,
    ExternalOperationalContact,
    OrganizationOperationalProfile,
    PersonnelChangeAction,
    PersonnelImportBatch,
    PersonnelImportKind,
    PersonnelImportStatus,
)
from .personnel_management_services import (
    build_personnel_template,
    create_import_batch,
    employee_snapshot,
    publish_import_batch,
    record_personnel_change,
)


OrganizationForm = django_forms.modelform_factory(
    Organization,
    fields=("code", "name", "short_name", "is_active"),
)


def _employee_context(employee: Employee | None) -> dict:
    if employee is None:
        return {
            "qualifications": [],
            "special_qualifications": [],
            "rights": [],
            "external_contacts": [],
            "change_records": [],
        }
    return {
        "qualifications": list(
            employee.qualifications.order_by("-is_active", "-valid_from", "-id")
        ),
        "special_qualifications": list(
            employee.special_qualifications.order_by("-is_active", "kind", "-valid_from")
        ),
        "rights": list(
            employee.operational_rights.select_related("right_definition").order_by(
                "-is_active",
                "right_definition__display_order",
                "-valid_from",
            )
        ),
        "external_contacts": list(
            employee.external_operational_contacts.select_related(
                "host_organization"
            ).order_by("-is_active", "relation_kind", "-valid_from")
        ),
        "change_records": list(
            employee.change_records.select_related("changed_by", "batch").order_by(
                "-created_at"
            )[:50]
        ),
    }


@login_required
def employee_create(request):
    employee = None
    contact = EmployeeContactProfile()
    if request.method == "POST":
        employee_form = EmployeeCardForm(request.POST, prefix="employee")
        contact_form = EmployeeContactForm(request.POST, prefix="contact", instance=contact)
        if employee_form.is_valid() and contact_form.is_valid():
            with transaction.atomic():
                employee = employee_form.save()
                contact = contact_form.save(commit=False)
                contact.employee = employee
                contact.save()
                record_personnel_change(
                    user=request.user,
                    employee=employee,
                    action=PersonnelChangeAction.CREATE,
                    reason=employee_form.cleaned_data["change_reason"],
                    after=employee_snapshot(employee),
                )
            messages.success(request, "Карточка сотрудника создана. Права и квалификации добавляются отдельно.")
            return redirect("organizations:employee_edit", public_id=employee.public_id)
    else:
        employee_form = EmployeeCardForm(prefix="employee")
        contact_form = EmployeeContactForm(prefix="contact", instance=contact)
    return render(
        request,
        "organizations/employee_editor.html",
        {
            "employee": employee,
            "employee_form": employee_form,
            "contact_form": contact_form,
            "is_create": True,
            **_employee_context(None),
        },
    )


@login_required
def employee_edit(request, public_id):
    employee = get_object_or_404(
        Employee.objects.select_related(
            "organization",
            "division",
            "position",
            "workplace",
        ),
        public_id=public_id,
    )
    contact, _ = EmployeeContactProfile.objects.get_or_create(employee=employee)
    if request.method == "POST":
        employee_form = EmployeeCardForm(
            request.POST,
            prefix="employee",
            instance=employee,
        )
        contact_form = EmployeeContactForm(
            request.POST,
            prefix="contact",
            instance=contact,
        )
        if employee_form.is_valid() and contact_form.is_valid():
            before = employee_snapshot(employee)
            with transaction.atomic():
                employee = employee_form.save()
                contact_form.save()
                record_personnel_change(
                    user=request.user,
                    employee=employee,
                    action=PersonnelChangeAction.UPDATE,
                    reason=employee_form.cleaned_data["change_reason"],
                    before=before,
                    after=employee_snapshot(employee),
                )
            messages.success(request, "Карточка сотрудника обновлена, изменение зафиксировано в истории.")
            return redirect("organizations:employee_edit", public_id=employee.public_id)
    else:
        employee_form = EmployeeCardForm(prefix="employee", instance=employee)
        contact_form = EmployeeContactForm(prefix="contact", instance=contact)
    return render(
        request,
        "organizations/employee_editor.html",
        {
            "employee": employee,
            "employee_form": employee_form,
            "contact_form": contact_form,
            "deactivation_form": DeactivationForm(),
            "is_create": False,
            **_employee_context(employee),
        },
    )


@login_required
@require_POST
def employee_deactivate(request, public_id):
    employee = get_object_or_404(Employee, public_id=public_id)
    form = DeactivationForm(request.POST)
    if form.is_valid():
        deactivate_employee(
            employee=employee,
            user=request.user,
            reason=form.cleaned_data["reason"],
        )
        messages.success(request, "Карточка деактивирована без физического удаления истории.")
        return redirect("organizations:directory")
    messages.error(request, "Укажите основание деактивации.")
    return redirect("organizations:employee_edit", public_id=employee.public_id)


def _initial_from_model(instance, field_names: tuple[str, ...]) -> dict:
    return {name: getattr(instance, name) for name in field_names}


@login_required
def electrical_qualification_edit(request, employee_public_id, record_public_id=None):
    employee = get_object_or_404(Employee, public_id=employee_public_id)
    existing = (
        get_object_or_404(
            EmployeeQualification,
            employee=employee,
            public_id=record_public_id,
        )
        if record_public_id
        else None
    )
    fields = (
        "personnel_category",
        "electrical_safety_group",
        "voltage_scope",
        "electrical_installation_scope",
        "valid_from",
        "valid_until",
        "is_active",
        "source_reference",
    )
    initial = _initial_from_model(existing, fields) if existing else None
    form = EmployeeQualificationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        replace_electrical_qualification(
            employee=employee,
            cleaned_data=form.cleaned_data,
            user=request.user,
            existing=existing,
        )
        messages.success(request, "Новая редакция квалификации опубликована.")
        return redirect("organizations:employee_edit", public_id=employee.public_id)
    return render(
        request,
        "organizations/personnel_record_form.html",
        {
            "employee": employee,
            "form": form,
            "title": "Группа по электробезопасности и категория персонала",
            "subtitle": "Старая редакция будет закрыта, новая сохранится отдельной записью.",
        },
    )


@login_required
def special_qualification_edit(request, employee_public_id, record_public_id=None):
    employee = get_object_or_404(Employee, public_id=employee_public_id)
    existing = (
        get_object_or_404(
            EmployeeSpecialQualification,
            employee=employee,
            public_id=record_public_id,
        )
        if record_public_id
        else None
    )
    fields = (
        "kind",
        "level",
        "scope_text",
        "valid_from",
        "valid_until",
        "basis_reference",
        "is_active",
    )
    initial = _initial_from_model(existing, fields) if existing else None
    form = EmployeeSpecialQualificationForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        replace_special_qualification(
            employee=employee,
            cleaned_data=form.cleaned_data,
            user=request.user,
            existing=existing,
        )
        messages.success(request, "Новая редакция специальной квалификации опубликована.")
        return redirect("organizations:employee_edit", public_id=employee.public_id)
    return render(
        request,
        "organizations/personnel_record_form.html",
        {
            "employee": employee,
            "form": form,
            "title": "Специальная квалификация",
            "subtitle": "Категория РЗА, группа работ на высоте или иной специальный допуск.",
        },
    )


@login_required
def operational_right_edit(request, employee_public_id, record_public_id=None):
    employee = get_object_or_404(Employee, public_id=employee_public_id)
    existing = (
        get_object_or_404(
            EmployeeOperationalRight.objects.select_related("right_definition"),
            employee=employee,
            public_id=record_public_id,
        )
        if record_public_id
        else None
    )
    fields = (
        "right_definition",
        "source_marker",
        "qualifier",
        "scope_text",
        "valid_from",
        "valid_until",
        "source_reference",
        "is_active",
    )
    initial = _initial_from_model(existing, fields) if existing else None
    form = EmployeeOperationalRightForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        replace_operational_right(
            employee=employee,
            cleaned_data=form.cleaned_data,
            user=request.user,
            existing=existing,
        )
        messages.success(request, "Новая редакция права опубликована и связана с проверкой полномочий.")
        return redirect("organizations:employee_edit", public_id=employee.public_id)
    return render(
        request,
        "organizations/personnel_record_form.html",
        {
            "employee": employee,
            "form": form,
            "title": "Предоставленное оперативное право",
            "subtitle": "Изменение создаёт новую редакцию, а предыдущая остаётся в истории.",
        },
    )


@login_required
def external_contact_edit(request, employee_public_id, record_public_id=None):
    employee = get_object_or_404(Employee, public_id=employee_public_id)
    existing = (
        get_object_or_404(
            ExternalOperationalContact,
            employee=employee,
            public_id=record_public_id,
        )
        if record_public_id
        else None
    )
    fields = (
        "host_organization",
        "relation_kind",
        "operational_scope",
        "authority_summary",
        "valid_from",
        "valid_until",
        "basis_reference",
        "is_active",
    )
    initial = _initial_from_model(existing, fields) if existing else None
    form = ExternalOperationalContactForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        replace_external_contact(
            employee=employee,
            cleaned_data=form.cleaned_data,
            user=request.user,
            existing=existing,
        )
        messages.success(request, "Связь с внешним оперативным справочником обновлена.")
        return redirect("organizations:employee_edit", public_id=employee.public_id)
    return render(
        request,
        "organizations/personnel_record_form.html",
        {
            "employee": employee,
            "form": form,
            "title": "Внешнее оперативное взаимодействие",
            "subtitle": "Диспетчерский центр, ЦУС, смежная организация или энергообъект.",
        },
    )


@login_required
def organization_create(request):
    organization = Organization()
    profile = OrganizationOperationalProfile(organization=organization)
    if request.method == "POST":
        organization_form = OrganizationForm(request.POST, prefix="organization")
        profile_form = OrganizationOperationalProfileForm(
            request.POST,
            prefix="profile",
            instance=profile,
        )
        if organization_form.is_valid() and profile_form.is_valid():
            with transaction.atomic():
                organization = organization_form.save()
                profile = profile_form.save(commit=False)
                profile.organization = organization
                profile.save()
            messages.success(request, "Организация добавлена в справочник.")
            return redirect("organizations:directory")
    else:
        organization_form = OrganizationForm(prefix="organization")
        profile_form = OrganizationOperationalProfileForm(
            prefix="profile",
            instance=profile,
        )
    return render(
        request,
        "organizations/organization_form.html",
        {
            "organization": None,
            "organization_form": organization_form,
            "profile_form": profile_form,
        },
    )


@login_required
def organization_edit(request, organization_id):
    organization = get_object_or_404(Organization, pk=organization_id)
    profile, _ = OrganizationOperationalProfile.objects.get_or_create(
        organization=organization,
    )
    if request.method == "POST":
        organization_form = OrganizationForm(
            request.POST,
            prefix="organization",
            instance=organization,
        )
        profile_form = OrganizationOperationalProfileForm(
            request.POST,
            prefix="profile",
            instance=profile,
        )
        if organization_form.is_valid() and profile_form.is_valid():
            organization_form.save()
            profile_form.save()
            messages.success(request, "Организация обновлена.")
            return redirect("organizations:directory")
    else:
        organization_form = OrganizationForm(
            prefix="organization",
            instance=organization,
        )
        profile_form = OrganizationOperationalProfileForm(
            prefix="profile",
            instance=profile,
        )
    return render(
        request,
        "organizations/organization_form.html",
        {
            "organization": organization,
            "organization_form": organization_form,
            "profile_form": profile_form,
        },
    )


@login_required
def personnel_import_upload(request):
    if request.method == "POST":
        form = PersonnelImportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                batch = create_import_batch(form=form, user=request.user)
            except ValidationError as exc:
                form.add_error("workbook", exc)
            else:
                messages.success(request, "Файл разобран. Проверьте изменения перед публикацией.")
                return redirect("organizations:personnel_import_detail", public_id=batch.public_id)
    else:
        form = PersonnelImportUploadForm()
    batches = PersonnelImportBatch.objects.select_related(
        "target_organization",
        "source_organization",
        "uploaded_by",
    )[:30]
    return render(
        request,
        "organizations/personnel_import_upload.html",
        {"form": form, "batches": batches},
    )


@login_required
def personnel_import_detail(request, public_id):
    batch = get_object_or_404(
        PersonnelImportBatch.objects.select_related(
            "target_organization",
            "source_organization",
            "uploaded_by",
            "published_by",
        ),
        public_id=public_id,
    )
    return render(
        request,
        "organizations/personnel_import_detail.html",
        {"batch": batch, "preview": batch.preview},
    )


@login_required
@require_POST
def personnel_import_publish(request, public_id):
    batch = get_object_or_404(
        PersonnelImportBatch,
        public_id=public_id,
        status=PersonnelImportStatus.PREVIEW,
    )
    selected_rows = {
        int(value)
        for value in request.POST.getlist("selected_rows")
        if value.isdigit()
    }
    if not selected_rows:
        messages.error(request, "Не выбрана ни одна строка для публикации.")
        return redirect("organizations:personnel_import_detail", public_id=batch.public_id)
    try:
        result = publish_import_batch(
            batch=batch,
            selected_rows=selected_rows,
            user=request.user,
        )
    except ValidationError as exc:
        messages.error(request, "; ".join(exc.messages))
        return redirect("organizations:personnel_import_detail", public_id=batch.public_id)
    messages.success(
        request,
        "Пакет опубликован: "
        f"создано {result['created']}, обновлено {result['updated']}, "
        f"пропущено {result['skipped']}.",
    )
    return redirect("organizations:personnel_import_detail", public_id=batch.public_id)


@login_required
def personnel_import_template(request, import_kind):
    if import_kind not in PersonnelImportKind.values:
        return HttpResponse(status=404)
    payload = build_personnel_template(import_kind)
    filename = (
        "personnel-rights-matrix.xlsx"
        if import_kind == PersonnelImportKind.INTERNAL_MATRIX
        else "external-operational-directory.xlsx"
    )
    response = HttpResponse(
        payload,
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
