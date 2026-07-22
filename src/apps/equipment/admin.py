from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import (
    DocumentEquipmentLink,
    DocumentEquipmentSnapshot,
    EnergySite,
    EquipmentAlias,
    EquipmentAsset,
    EquipmentAuditEvent,
    EquipmentNameRevision,
    EquipmentRelation,
    EquipmentType,
)
from .services import dispatcher_name_on, publish_equipment_name_revision


def employee_for_request(request):
    return getattr(request.user, "employee_profile", None)


@admin.register(EnergySite)
class EnergySiteAdmin(admin.ModelAdmin):
    list_display = ("name", "site_type", "organization", "is_external", "is_active")
    list_filter = ("site_type", "is_external", "is_active", "organization")
    search_fields = ("code", "name", "short_name")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "category", "is_active")
    list_filter = ("category", "is_active")
    search_fields = ("code", "name", "description")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EquipmentAsset)
class EquipmentAssetAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "dispatcher_name",
        "equipment_type",
        "site",
        "status",
        "is_external",
    )
    list_filter = (
        "equipment_type__category",
        "status",
        "site",
        "is_external",
    )
    search_fields = (
        "code",
        "technical_name",
        "dispatcher_name_revisions__dispatcher_name",
        "aliases__alias",
    )
    readonly_fields = ("public_id", "created_at")

    @admin.display(description="Диспетчерское наименование")
    def dispatcher_name(self, obj):
        return dispatcher_name_on(obj)

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EquipmentNameRevision)
class EquipmentNameRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "equipment",
        "revision_number",
        "dispatcher_name",
        "effective_from",
        "status",
        "published_at",
    )
    list_filter = ("status", "equipment__site", "equipment__equipment_type")
    search_fields = (
        "equipment__code",
        "dispatcher_name",
        "basis_reference",
    )
    readonly_fields = ("published_at", "digest")
    actions = ("publish_selected",)

    @admin.action(description="Опубликовать выбранные диспетчерские наименования")
    def publish_selected(self, request, queryset) -> None:
        actor = employee_for_request(request)
        if actor is None:
            self.message_user(
                request,
                "Учётная запись администратора не связана с сотрудником.",
                level=messages.ERROR,
            )
            return
        count = 0
        for revision in queryset:
            try:
                publish_equipment_name_revision(
                    revision=revision,
                    actor=actor,
                )
            except ValidationError as error:
                self.message_user(
                    request,
                    f"{revision}: {error}",
                    level=messages.ERROR,
                )
            else:
                count += 1
        if count:
            self.message_user(request, f"Опубликовано наименований: {count}.")

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EquipmentAlias)
class EquipmentAliasAdmin(admin.ModelAdmin):
    list_display = (
        "alias",
        "equipment",
        "scope_site",
        "scope_parent",
        "alias_type",
        "valid_from",
        "valid_until",
    )
    list_filter = ("alias_type", "organization", "scope_site")
    search_fields = ("alias", "equipment__code", "equipment__technical_name")

    def has_change_permission(self, request, obj=None) -> bool:
        return obj is None

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EquipmentRelation)
class EquipmentRelationAdmin(admin.ModelAdmin):
    list_display = (
        "source_equipment",
        "relation_type",
        "target_equipment",
        "valid_from",
        "valid_until",
    )
    list_filter = ("relation_type", "source_equipment__site")
    search_fields = (
        "source_equipment__code",
        "target_equipment__code",
        "description",
        "basis_reference",
    )

    def has_change_permission(self, request, obj=None) -> bool:
        return obj is None

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(DocumentEquipmentLink)
class DocumentEquipmentLinkAdmin(admin.ModelAdmin):
    list_display = ("document_version", "equipment", "created_by", "created_at")
    list_filter = ("equipment__site", "equipment__equipment_type")
    search_fields = (
        "document__registration_number",
        "document__title",
        "equipment__code",
        "equipment__technical_name",
    )

    def has_delete_permission(self, request, obj=None) -> bool:
        return bool(obj and obj.document_version.status == "DRAFT")


@admin.register(DocumentEquipmentSnapshot)
class DocumentEquipmentSnapshotAdmin(admin.ModelAdmin):
    list_display = (
        "document_version",
        "equipment_code_snapshot",
        "dispatcher_name_snapshot",
        "captured_at",
    )
    search_fields = (
        "document__registration_number",
        "equipment_code_snapshot",
        "dispatcher_name_snapshot",
    )
    readonly_fields = (
        "link",
        "document",
        "document_version",
        "equipment",
        "equipment_public_id_snapshot",
        "equipment_code_snapshot",
        "dispatcher_name_snapshot",
        "technical_name_snapshot",
        "equipment_type_code_snapshot",
        "equipment_type_name_snapshot",
        "site_code_snapshot",
        "site_name_snapshot",
        "hierarchy_path_snapshot",
        "name_revision_number_snapshot",
        "captured_at",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(EquipmentAuditEvent)
class EquipmentAuditEventAdmin(admin.ModelAdmin):
    list_display = (
        "occurred_at",
        "event_type",
        "actor_employee",
        "equipment",
        "document_version",
    )
    list_filter = ("event_type", "organization")
    search_fields = (
        "equipment__code",
        "actor_employee__last_name",
        "document_version__document__registration_number",
    )
    readonly_fields = (
        "organization",
        "event_type",
        "occurred_at",
        "actor_employee",
        "equipment",
        "document_version",
        "payload",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
