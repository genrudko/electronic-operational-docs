from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    NormativeDocument,
    NormativeRequirement,
    NormativeRevision,
    OrganizationConfigurationRevision,
    OrganizationNameRevision,
    RequirementTrace,
)
from .services import (
    publish_configuration_revision,
    publish_normative_revision,
    publish_organization_name_revision,
)


def _employee_for_request(request):
    return getattr(request.user, "employee_profile", None)


@admin.register(NormativeDocument)
class NormativeDocumentAdmin(admin.ModelAdmin):
    list_display = ("short_title", "scope", "issuer", "organization", "is_active")
    list_filter = ("scope", "is_active")
    search_fields = ("code", "title", "short_title", "issuer", "document_number")


@admin.register(NormativeRevision)
class NormativeRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "document",
        "revision_number",
        "status",
        "effective_from",
        "effective_until",
        "published_at",
    )
    list_filter = ("status", "document__scope")
    search_fields = ("document__title", "document__short_title", "source_reference")
    readonly_fields = ("published_at", "digest")
    actions = ("publish_selected",)

    @admin.action(description="Опубликовать выбранные редакции")
    def publish_selected(self, request, queryset) -> None:
        actor = _employee_for_request(request)
        if actor is None:
            self.message_user(
                request,
                "Учётная запись администратора не связана с сотрудником.",
                level=messages.ERROR,
            )
            return
        published = 0
        for revision in queryset:
            try:
                publish_normative_revision(revision=revision, actor=actor)
            except ValidationError as error:
                self.message_user(request, f"{revision}: {error}", level=messages.ERROR)
            else:
                published += 1
        if published:
            self.message_user(request, f"Опубликовано редакций: {published}.")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(NormativeRequirement)
class NormativeRequirementAdmin(admin.ModelAdmin):
    list_display = ("code", "clause", "title", "revision", "is_mandatory")
    list_filter = ("is_mandatory", "revision__status")
    search_fields = ("code", "clause", "title", "requirement_text")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(RequirementTrace)
class RequirementTraceAdmin(admin.ModelAdmin):
    list_display = (
        "requirement",
        "function_code",
        "function_name",
        "implementation_status",
        "created_at",
    )
    list_filter = ("implementation_status",)
    search_fields = ("requirement__code", "function_code", "function_name", "test_reference")

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return ("created_at",)
        return tuple(field.name for field in self.model._meta.fields)

    def has_change_permission(self, request, obj=None) -> bool:
        return obj is None

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(OrganizationNameRevision)
class OrganizationNameRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "full_name",
        "valid_from",
        "valid_until",
        "status",
    )
    list_filter = ("status", "organization")
    search_fields = ("full_name", "short_name", "basis_reference")
    readonly_fields = ("published_at",)
    actions = ("publish_selected",)

    @admin.action(description="Опубликовать выбранные наименования")
    def publish_selected(self, request, queryset) -> None:
        actor = _employee_for_request(request)
        if actor is None:
            self.message_user(
                request,
                "Учётная запись администратора не связана с сотрудником.",
                level=messages.ERROR,
            )
            return
        published = 0
        for revision in queryset:
            try:
                publish_organization_name_revision(revision=revision, actor=actor)
            except ValidationError as error:
                self.message_user(request, f"{revision}: {error}", level=messages.ERROR)
            else:
                published += 1
        if published:
            self.message_user(request, f"Опубликовано наименований: {published}.")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(OrganizationConfigurationRevision)
class OrganizationConfigurationRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "organization",
        "revision_number",
        "effective_from",
        "effective_until",
        "status",
    )
    list_filter = ("status", "organization")
    readonly_fields = ("published_at", "digest")
    actions = ("publish_selected",)

    @admin.action(description="Опубликовать выбранные конфигурации")
    def publish_selected(self, request, queryset) -> None:
        actor = _employee_for_request(request)
        if actor is None:
            self.message_user(
                request,
                "Учётная запись администратора не связана с сотрудником.",
                level=messages.ERROR,
            )
            return
        published = 0
        for revision in queryset:
            try:
                publish_configuration_revision(revision=revision, actor=actor)
            except ValidationError as error:
                self.message_user(request, f"{revision}: {error}", level=messages.ERROR)
            else:
                published += 1
        if published:
            self.message_user(request, f"Опубликовано конфигураций: {published}.")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
