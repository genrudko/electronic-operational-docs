from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Count, Prefetch
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .forms import InterfacePreferenceForm, PersonalAuthenticationForm
from .models import Division, Employee, InterfacePreference, Organization, RoleAssignment
from .services import get_effective_roles


class PersonalLoginView(LoginView):
    template_name = "organizations/login.html"
    authentication_form = PersonalAuthenticationForm
    redirect_authenticated_user = True


@login_required
def directory(request):
    organizations = Organization.objects.prefetch_related(
        Prefetch("divisions", queryset=Division.objects.order_by("name")),
        "workplaces",
        "operational_areas",
        "positions",
        Prefetch(
            "employees",
            queryset=Employee.objects.select_related(
                "division",
                "position",
                "workplace",
                "user",
            ).order_by("last_name", "first_name"),
        ),
    ).annotate(employee_count=Count("employees", distinct=True))
    return render(
        request,
        "organizations/directory.html",
        {"organizations": organizations},
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
