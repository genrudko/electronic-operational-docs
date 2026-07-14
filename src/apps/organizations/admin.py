from django.contrib import admin

from .models import (
    AuthenticationEvent,
    Division,
    Employee,
    OperationalArea,
    Organization,
    Position,
    ResponsibilityScope,
    Role,
    RoleAssignment,
    Substitution,
    Workplace,
)


@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "short_name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("code", "name", "short_name")


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "parent", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("code", "name")


@admin.register(Workplace)
class WorkplaceAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "division", "is_active")
    list_filter = ("organization", "division", "is_active")
    search_fields = ("code", "name")


@admin.register(OperationalArea)
class OperationalAreaAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "division", "is_active")
    list_filter = ("organization", "division", "is_active")
    search_fields = ("code", "name")
    filter_horizontal = ("workplaces",)


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "is_operational", "is_active")
    list_filter = ("organization", "is_operational", "is_active")
    search_fields = ("code", "name")


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = (
        "personnel_number",
        "full_name",
        "organization",
        "division",
        "position",
        "user",
        "is_active",
    )
    list_filter = ("organization", "division", "position", "is_active")
    search_fields = (
        "personnel_number",
        "last_name",
        "first_name",
        "middle_name",
        "user__username",
    )
    autocomplete_fields = ("user",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "is_system", "is_active")
    list_filter = ("is_system", "is_active")
    search_fields = ("code", "name")


@admin.register(ResponsibilityScope)
class ResponsibilityScopeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "operational_area", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("code", "name")


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ("employee", "role", "scope", "valid_from", "valid_until", "is_active")
    list_filter = ("role", "scope", "is_active")
    search_fields = ("employee__last_name", "employee__first_name", "role__name")


@admin.register(Substitution)
class SubstitutionAdmin(admin.ModelAdmin):
    list_display = (
        "replaced_employee",
        "substitute_employee",
        "scope",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("is_active", "scope")
    search_fields = (
        "replaced_employee__last_name",
        "substitute_employee__last_name",
        "reason",
    )


@admin.register(AuthenticationEvent)
class AuthenticationEventAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_at",
        "event_type",
        "username_snapshot",
        "employee",
        "ip_address",
    )
    list_filter = ("event_type", "occurred_at")
    search_fields = ("username_snapshot", "employee__last_name", "ip_address")
    readonly_fields = (
        "event_type",
        "occurred_at",
        "user",
        "employee",
        "username_snapshot",
        "ip_address",
        "user_agent",
        "session_key",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
