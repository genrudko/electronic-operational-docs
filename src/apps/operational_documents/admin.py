from django.contrib import admin

from .models import (
    OperationalDocumentAuditEvent,
    OperationalDocumentRecord,
    OperationalDocumentRecordRevision,
    OperationalDocumentType,
    OperationalDocumentTypeRevision,
)


@admin.register(OperationalDocumentType)
class OperationalDocumentTypeAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "organization", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("code", "name", "short_name")


@admin.register(OperationalDocumentTypeRevision)
class OperationalDocumentTypeRevisionAdmin(admin.ModelAdmin):
    list_display = ("document_type", "revision_number", "status", "published_at")
    list_filter = ("status", "document_type__organization")
    readonly_fields = ("canonical_snapshot", "sha256", "published_at")


@admin.register(OperationalDocumentRecord)
class OperationalDocumentRecordAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "document_type",
        "title",
        "status_name_snapshot",
        "event_at",
    )
    list_filter = ("organization", "document_type", "status_code", "status_is_terminal")
    search_fields = ("registration_number", "title", "summary", "search_text")
    readonly_fields = (
        "public_id",
        "registration_number",
        "sequence_year",
        "sequence_value",
        "created_by_full_name_snapshot",
        "created_by_position_snapshot",
        "created_by_division_snapshot",
        "search_text",
    )


@admin.register(OperationalDocumentRecordRevision)
class OperationalDocumentRecordRevisionAdmin(admin.ModelAdmin):
    list_display = ("record", "revision_number", "action", "actor", "created_at")
    readonly_fields = [field.name for field in OperationalDocumentRecordRevision._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(OperationalDocumentAuditEvent)
class OperationalDocumentAuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "entity_type", "entity_id", "actor", "occurred_at")
    list_filter = ("organization", "event_type")
    readonly_fields = [field.name for field in OperationalDocumentAuditEvent._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
