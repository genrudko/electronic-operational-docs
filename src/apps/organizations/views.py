from __future__ import annotations

import unicodedata
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.equipment.models import EnergySite

from .forms import InterfacePreferenceForm, PersonalAuthenticationForm
from .models import (
    Division,
    DivisionEnergySiteService,
    Employee,
    EmployeeEnergySiteAuthorization,
    InterfacePreference,
    OperationalReportingLine,
    OperationalRightDefinition,
    Organization,
    RoleAssignment,
)
from .services import get_effective_roles


def _search_token(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKC", value or "")
        .casefold()
        .replace("ё", "е")
        .split()
    )


def _employee_search_haystack(employee: Employee) -> str:
    parts = [
        employee.full_name,
        employee.personnel_number,
        employee.division.name,
        employee.position.name,
        employee.workplace.name if employee.workplace_id else "",
    ]
    parts.extend(
        f"{qualification.personnel_category} {qualification.electrical_safety_group} "
        f"{qualification.voltage_scope} {qualification.electrical_installation_scope}"
        for qualification in employee.qualifications.all()
    )
    parts.extend(
        f"{grant.right_definition.name} {grant.qualifier} {grant.scope_text}"
        for grant in employee.operational_rights.all()
    )
    return _search_token(" ".join(parts))


class PersonalLoginView(LoginView):
    template_name = "organizations/login.html"
    authentication_form = PersonalAuthenticationForm
    redirect_authenticated_user = True


def _division_tree(
    divisions: list[Division],
    employees: list[Employee],
) -> list[dict[str, object]]:
    children: dict[int | None, list[Division]] = defaultdict(list)
    for division in divisions:
        children[division.parent_id].append(division)
    for items in children.values():
        items.sort(key=lambda item: item.name)

    direct_employees: dict[int, list[Employee]] = defaultdict(list)
    for employee in employees:
        direct_employees[employee.division_id].append(employee)

    result: list[dict[str, object]] = []

    def add_branch(parent_id: int | None, depth: int) -> None:
        for division in children.get(parent_id, []):
            try:
                service_profile = division.service_profile
            except ObjectDoesNotExist:
                service_profile = None
            result.append(
                {
                    "division": division,
                    "depth": depth,
                    "service_profile": service_profile,
                    "is_blade_service": division.code == "BLADE_SERVICE",
                    "is_center": division.code == "CENTER",
                    "direct_employees": direct_employees.get(division.pk, []),
                }
            )
            add_branch(division.pk, depth + 1)

    add_branch(None, 0)
    return result


@login_required
def directory(request):
    organizations = list(Organization.objects.filter(is_active=True).order_by("name"))
    organization_cards: list[dict[str, object]] = []

    for organization in organizations:
        divisions = list(
            Division.objects.filter(organization=organization, is_active=True)
            .select_related("parent", "service_profile")
            .order_by("name")
        )
        employees = list(
            Employee.objects.filter(organization=organization, is_active=True)
            .select_related("division", "position", "workplace", "user")
            .prefetch_related(
                "qualifications",
                "operational_rights__right_definition",
            )
            .order_by("division__name", "last_name", "first_name")
        )
        sites = list(
            EnergySite.objects.filter(organization=organization, is_active=True)
            .prefetch_related(
                Prefetch(
                    "servicing_divisions",
                    queryset=DivisionEnergySiteService.objects.filter(is_active=True)
                    .select_related("division")
                    .order_by("service_kind", "division__name"),
                )
            )
            .order_by("site_type", "name")
        )
        reporting_lines = list(
            OperationalReportingLine.objects.filter(
                subordinate_division__organization=organization,
                is_active=True,
            )
            .select_related("supervisor__position", "subordinate_division")
            .order_by("subordinate_division__name")
        )
        authorizations = list(
            EmployeeEnergySiteAuthorization.objects.filter(
                employee__organization=organization,
                is_active=True,
            )
            .select_related("employee__position", "energy_site")
            .order_by("employee__last_name", "energy_site__name")
        )
        authorization_rows: dict[int, dict[str, object]] = {}
        for authorization in authorizations:
            row = authorization_rows.setdefault(
                authorization.employee_id,
                {
                    "employee": authorization.employee,
                    "role": authorization.get_operational_role_display(),
                    "sites": [],
                },
            )
            row["sites"].append(authorization.energy_site.short_name or authorization.energy_site.name)

        organization_cards.append(
            {
                "organization": organization,
                "division_tree": _division_tree(divisions, employees),
                "employees": employees,
                "employee_count": len(employees),
                "sites": sites,
                "reporting_lines": reporting_lines,
                "authorization_rows": list(authorization_rows.values()),
            }
        )

    query = " ".join(request.GET.get("q", "").split())
    query_token = _search_token(query)
    search_results: list[Employee] = []
    if query_token:
        for card in organization_cards:
            for employee in card["employees"]:
                if query_token in _employee_search_haystack(employee):
                    search_results.append(employee)

    return render(
        request,
        "organizations/directory.html",
        {
            "organization_cards": organization_cards,
            "query": query,
            "search_results": search_results,
        },
    )


@login_required
def employee_detail(request, public_id):
    employee = get_object_or_404(
        Employee.objects.select_related(
            "organization",
            "division",
            "position",
            "workplace",
            "user",
        ).prefetch_related(
            "qualifications",
            "operational_rights__right_definition",
        ),
        public_id=public_id,
        is_active=True,
    )
    qualifications = list(
        employee.qualifications.filter(is_active=True).order_by("-valid_from", "-id")
    )
    grants = list(
        employee.operational_rights.filter(is_active=True)
        .select_related("right_definition")
        .order_by("right_definition__display_order", "right_definition__name")
    )
    grouped_rights: list[dict[str, object]] = []
    current_category = None
    current_group = None
    category_labels = dict(OperationalRightDefinition.Category.choices)
    for grant in grants:
        category = grant.right_definition.category
        if category != current_category:
            current_group = {
                "code": category,
                "name": category_labels.get(category, category),
                "rights": [],
            }
            grouped_rights.append(current_group)
            current_category = category
        current_group["rights"].append(grant)
    return render(
        request,
        "organizations/employee_detail.html",
        {
            "employee": employee,
            "qualifications": qualifications,
            "grouped_rights": grouped_rights,
        },
    )


@login_required
def account(request):
    employee = (
        Employee.objects.select_related(
            "organization",
            "division",
            "position",
            "workplace",
            "user",
        )
        .filter(user=request.user)
        .first()
    )
    preferences, _ = InterfacePreference.objects.get_or_create(user=request.user)
    if request.method == "POST":
        preference_form = InterfacePreferenceForm(request.POST, instance=preferences)
        if preference_form.is_valid():
            preference_form.save()
            messages.success(request, "Настройки интерфейса сохранены.")
            return redirect("organizations:account")
    else:
        preference_form = InterfacePreferenceForm(instance=preferences)

    effective_roles = get_effective_roles(employee) if employee else []
    direct_assignments = (
        RoleAssignment.objects.select_related("role", "scope")
        .filter(employee=employee)
        .order_by("role__name")
        if employee
        else []
    )
    return render(
        request,
        "organizations/account.html",
        {
            "employee": employee,
            "effective_roles": effective_roles,
            "direct_assignments": direct_assignments,
            "preference_form": preference_form,
        },
    )


@require_POST
@login_required
def personal_logout(request):
    logout(request)
    return redirect("system:home")
