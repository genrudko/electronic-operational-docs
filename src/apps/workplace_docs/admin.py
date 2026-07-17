from django.contrib import admin

from .models import (
    WorkplaceDocumentAuditEvent,
    WorkplaceDocumentEntry,
    WorkplaceDocumentList,
    WorkplaceDocumentRevision,
)


class WorkplaceDocumentEntryInline(admin.TabularInline):
    model = WorkplaceDocumentEntry
    extra = 0
    fields = (
        "display_order",
        "code",
        "title",
        "source_kind",
        "requirement_kind",
        "storage_form",
    )


@admin.register(WorkplaceDocumentList)
class WorkplaceDocumentListAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "workplace", "organization", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("code", "title", "workplace__name")


@admin.register(WorkplaceDocumentRevision)
class WorkplaceDocumentRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "document_list",
        "revision_number",
        "status",
        "effective_from",
        "next_review_date",
        "approved_by",
    )
    list_filter = ("status", "effective_from", "next_review_date")
    readonly_fields = ("approved_at", "next_review_date", "digest", "created_at")
    inlines = (WorkplaceDocumentEntryInline,)


@admin.register(WorkplaceDocumentEntry)
class WorkplaceDocumentEntryAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "title",
        "revision",
        "source_kind",
        "requirement_kind",
        "storage_form",
    )
    list_filter = ("source_kind", "requirement_kind", "storage_form")
    search_fields = ("code", "title", "basis_text")


@admin.register(WorkplaceDocumentAuditEvent)
class WorkplaceDocumentAuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "document_list", "revision", "actor", "event_at")
    readonly_fields = (
        "document_list",
        "revision",
        "event_type",
        "actor",
        "event_at",
        "snapshot",
        "digest",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
