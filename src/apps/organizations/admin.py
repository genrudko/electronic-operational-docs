from django.contrib import admin

from .models import (
    AuthenticationEvent,
    Division,
    DivisionEnergySiteService,
    DivisionServiceProfile,
    Employee,
    EmployeeEnergySiteAuthorization,
    EmployeeOperationalRight,
    EmployeeQualification,
    InterfacePreference,
    OperationalArea,
    OperationalReportingLine,
    OperationalRightDefinition,
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

@admin.register(DivisionServiceProfile)
class DivisionServiceProfileAdmin(admin.ModelAdmin):
    list_display = (
        "division",
        "territorial_base",
        "is_cross_territory",
    )
    list_filter = ("is_cross_territory",)
    search_fields = ("division__name", "territorial_base", "service_scope")


@admin.register(DivisionEnergySiteService)
class DivisionEnergySiteServiceAdmin(admin.ModelAdmin):
    list_display = (
        "division",
        "energy_site",
        "service_kind",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("service_kind", "is_active", "energy_site")
    search_fields = ("division__name", "energy_site__name", "note")


@admin.register(EmployeeEnergySiteAuthorization)
class EmployeeEnergySiteAuthorizationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "energy_site",
        "operational_role",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("operational_role", "is_active", "energy_site")
    search_fields = (
        "employee__last_name",
        "employee__first_name",
        "energy_site__name",
    )


@admin.register(OperationalReportingLine)
class OperationalReportingLineAdmin(admin.ModelAdmin):
    list_display = (
        "subordinate_division",
        "supervisor",
        "relation_type",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("relation_type", "is_active")
    search_fields = (
        "subordinate_division__name",
        "supervisor__last_name",
        "supervisor__first_name",
    )

@admin.register(InterfacePreference)
class InterfacePreferenceAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "theme",
        "density",
        "font_scale",
        "content_width",
        "show_technical_details",
        "updated_at",
    )
    list_filter = (
        "theme",
        "density",
        "font_scale",
        "content_width",
        "show_technical_details",
    )
    search_fields = ("user__username",)


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


@admin.register(OperationalRightDefinition)
class OperationalRightDefinitionAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "category", "value_kind", "display_order", "is_active")
    list_filter = ("category", "value_kind", "is_active")
    search_fields = ("code", "name", "description")


@admin.register(EmployeeQualification)
class EmployeeQualificationAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "personnel_category",
        "electrical_safety_group",
        "voltage_scope",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("personnel_category", "electrical_safety_group", "is_active")
    search_fields = ("employee__last_name", "employee__first_name", "source_reference")
    readonly_fields = ("public_id", "source_file_sha256", "source_row_number", "created_at")


@admin.register(EmployeeOperationalRight)
class EmployeeOperationalRightAdmin(admin.ModelAdmin):
    list_display = (
        "employee",
        "right_definition",
        "qualifier",
        "valid_from",
        "valid_until",
        "is_active",
    )
    list_filter = ("right_definition__category", "right_definition", "is_active")
    search_fields = (
        "employee__last_name",
        "employee__first_name",
        "right_definition__name",
        "qualifier",
        "scope_text",
    )
    readonly_fields = (
        "public_id",
        "source_marker",
        "source_file_sha256",
        "source_row_number",
        "created_at",
    )
