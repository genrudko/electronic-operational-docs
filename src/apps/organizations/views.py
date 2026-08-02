from __future__ import annotations

from collections import defaultdict

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Q
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import InterfacePreferenceForm, PersonalAuthenticationForm
from .models import (
    Division,
    DivisionEnergySiteService,
    Employee,
    InterfacePreference,
    OperationalReportingLine,
    Organization,
    RoleAssignment,
)
from .personnel_management_models import (
    ExternalOperationalContact,
    OrganizationOperationalProfile,
    OrganizationRelationKind,
    PersonnelChangeRecord,
    PersonnelImportBatch,
)
from .services import get_effective_roles


class PersonalLoginView(LoginView):
    template_name = "organizations/login.html"
    authentication_form = PersonalAuthenticationForm
    redirect_authenticated_user = True


def _organization_kind(organization: Organization) -> str:
    try:
        return organization.operational_profile.relation_kind
    except OrganizationOperationalProfile.DoesNotExist:
        return OrganizationRelationKind.OWN


def _organization_groups(
    organizations: list[Organization],
) -> dict[str, list[Organization]]:
    groups: dict[str, list[Organization]] = defaultdict(list)
    for organization in organizations:
        groups[_organization_kind(organization)].append(organization)
    return groups


def _division_tree(divisions: list[Division]) -> list[dict[str, object]]:
    children: dict[int | None, list[Division]] = defaultdict(list)
    for division in divisions:
        children[division.parent_id].append(division)
    for items in children.values():
        items.sort(key=lambda item: item.name)

    result: list[dict[str, object]] = []

    def add(parent_id: int | None, depth: int) -> None:
        for division in children.get(parent_id, ()):
            result.append(
                {
                    "division": division,
                    "depth": depth,
                    "is_separate": division.code == "BLADE_SERVICE",
                    "is_center": division.code == "CENTER",
                }
            )
            add(division.id, depth + 1)

    add(None, 0)
    return result


def _site_service_rows(
    organization: Organization | None,
) -> list[dict[str, object]]:
    if organization is None:
        return []
    services = list(
        DivisionEnergySiteService.objects.filter(
            division__organization=organization,
            is_active=True,
        )
        .select_related("division", "energy_site")
        .order_by("energy_site__name", "division__name", "service_kind")
    )
    grouped: dict[int, dict[str, object]] = {}
    for service in services:
        row = grouped.setdefault(
            service.energy_site_id,
            {"site": service.energy_site, "services": []},
        )
        row["services"].append(service)
    return list(grouped.values())


@login_required
def directory(request):
    organizations = list(
        Organization.objects.filter(is_active=True)
        .select_related("operational_profile")
        .annotate(
            employee_count=Count(
                "employees",
                filter=Q(employees__is_active=True),
                distinct=True,
            ),
            division_count=Count(
                "divisions",
                filter=Q(divisions__is_active=True),
                distinct=True,
            ),
        )
        .order_by("name")
    )
    groups = _organization_groups(organizations)
    selected_code = request.GET.get("organization", "").strip()
    selected = next(
        (item for item in organizations if item.code == selected_code),
        None,
    )
    if selected is None:
        selected = next(
            (item for item in organizations if item.code == "DEMO"),
            organizations[0] if organizations else None,
        )

    divisions = []
    employees = []
    if selected is not None:
        divisions = list(
            Division.objects.filter(
                organization=selected,
                is_active=True,
            )
            .select_related("parent", "service_profile")
            .annotate(
                active_employee_count=Count(
                    "employees",
                    filter=Q(employees__is_active=True),
                    distinct=True,
                )
            )
            .order_by("name")
        )
        employees = list(
            Employee.objects.filter(
                organization=selected,
                is_active=True,
            )
            .select_related(
                "division",
                "position",
                "workplace",
                "contact_profile",
            )
            .prefetch_related(
                "qualifications",
                "special_qualifications",
                "operational_rights",
            )
            .order_by("division__name", "position__name", "last_name")
        )

    external_contacts = (
        list(
            ExternalOperationalContact.objects.filter(
                host_organization=selected,
                is_active=True,
            )
            .select_related(
                "employee__organization",
                "employee__division",
                "employee__position",
                "employee__contact_profile",
            )
            .order_by(
                "employee__organization__name",
                "relation_kind",
                "employee__last_name",
            )[:100]
        )
        if selected
        else []
    )
    reporting_lines = (
        list(
            OperationalReportingLine.objects.filter(
                subordinate_division__organization=selected,
                is_active=True,
            )
            .select_related(
                "supervisor__position",
                "subordinate_division",
            )
            .order_by("subordinate_division__name")
        )
        if selected
        else []
    )
    center_leadership = [
        employee for employee in employees if employee.division.code == "CENTER"
    ]

    return render(
        request,
        "organizations/directory.html",
        {
            "organizations": organizations,
            "selected_organization": selected,
            "division_tree": _division_tree(divisions),
            "employees": employees,
            "external_contacts": external_contacts,
            "reporting_lines": reporting_lines,
            "site_service_rows": _site_service_rows(selected),
            "center_leadership": center_leadership,
            "own_organizations": groups.get(OrganizationRelationKind.OWN, []),
            "dispatch_organizations": groups.get(
                OrganizationRelationKind.DISPATCH_CENTER,
                [],
            ),
            "related_grid_organizations": groups.get(
                OrganizationRelationKind.RELATED_GRID,
                [],
            ),
            "related_site_organizations": groups.get(
                OrganizationRelationKind.RELATED_SITE,
                [],
            ),
            "commercial_organizations": groups.get(
                OrganizationRelationKind.COMMERCIAL_DISPATCH,
                [],
            ),
            "contractor_organizations": groups.get(
                OrganizationRelationKind.CONTRACTOR,
                [],
            ),
            "recent_imports": list(
                PersonnelImportBatch.objects.select_related(
                    "target_organization",
                    "source_organization",
                    "uploaded_by",
                )[:8]
            ),
            "recent_changes": list(
                PersonnelChangeRecord.objects.select_related(
                    "employee",
                    "changed_by",
                    "batch",
                )[:12]
            ),
            "total_active_employees": sum(
                item.employee_count for item in organizations
            ),
            "external_contact_count": len(external_contacts),
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
