from django.contrib import admin

from .models import (
    AuditEvent,
    Document,
    DocumentLink,
    DocumentNumberSequence,
    DocumentType,
    DocumentVersion,
)


@admin.register(DocumentType)
class DocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "number_prefix", "number_width", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("code", "name", "number_prefix")


class DocumentVersionInline(admin.TabularInline):
    model = DocumentVersion
    extra = 0
    can_delete = False
    readonly_fields = (
        "version_number",
        "status",
        "title",
        "content",
        "created_by",
        "created_at",
        "updated_at",
        "registered_at",
        "registered_by",
    )

    def has_add_permission(self, request, obj=None) -> bool:
        return False


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "title",
        "document_type",
        "organization",
        "status",
        "created_by",
        "created_at",
        "registered_at",
    )
    list_filter = ("organization", "document_type", "status")
    search_fields = ("registration_number", "title", "public_id")
    readonly_fields = (
        "public_id",
        "status",
        "current_version",
        "created_at",
        "updated_at",
        "registration_year",
        "sequence_number",
        "registration_number",
        "registered_at",
        "registered_by",
    )
    inlines = (DocumentVersionInline,)

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(DocumentVersion)
class DocumentVersionAdmin(admin.ModelAdmin):
    list_display = ("document", "version_number", "status", "created_by", "created_at", "registered_at")
    list_filter = ("status",)
    search_fields = ("document__registration_number", "document__title", "title")
    readonly_fields = (
        "document",
        "version_number",
        "status",
        "title",
        "content",
        "created_by",
        "created_at",
        "updated_at",
        "registered_at",
        "registered_by",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(DocumentLink)
class DocumentLinkAdmin(admin.ModelAdmin):
    list_display = ("source_document", "link_type", "target_document", "created_by", "created_at")
    list_filter = ("link_type",)
    readonly_fields = ("created_at",)

    def has_change_permission(self, request, obj=None) -> bool:
        return obj is None

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "event_type", "organization", "actor_employee", "document")
    list_filter = ("organization", "event_type")
    search_fields = ("entity_id", "document__registration_number", "document__title")
    readonly_fields = (
        "organization",
        "event_type",
        "occurred_at",
        "actor_user",
        "actor_employee",
        "document",
        "document_version",
        "entity_type",
        "entity_id",
        "payload",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(DocumentNumberSequence)
class DocumentNumberSequenceAdmin(admin.ModelAdmin):
    list_display = ("organization", "document_type", "year", "last_value", "updated_at")
    list_filter = ("organization", "year")
    readonly_fields = ("organization", "document_type", "year", "last_value", "updated_at")

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
