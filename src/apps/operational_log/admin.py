from django.contrib import admin

from .models import (
    OperationalJournal,
    OperationalJournalSequence,
    OperationalLogAuditEvent,
    OperationalLogDocumentLink,
    OperationalLogEntry,
    OperationalLogEquipmentLink,
)


@admin.register(OperationalJournal)
class OperationalJournalAdmin(admin.ModelAdmin):
    list_display = ("code", "title", "workplace", "organization", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("code", "title", "workplace__name")


@admin.register(OperationalLogEntry)
class OperationalLogEntryAdmin(admin.ModelAdmin):
    list_display = (
        "journal",
        "sequence_number",
        "event_at",
        "registered_at",
        "entry_form",
        "author_full_name_snapshot",
    )
    list_filter = ("journal", "entry_form", "event_at")
    search_fields = ("content", "type_code", "type_title", "author_full_name_snapshot")
    readonly_fields = (
        "journal",
        "sequence_number",
        "event_at",
        "registered_at",
        "entry_form",
        "type_code",
        "type_title",
        "content",
        "typed_payload",
        "author",
        "author_full_name_snapshot",
        "author_position_snapshot",
        "author_workplace_snapshot",
        "digest",
    )

    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


class ReadOnlyOperationalAdmin(admin.ModelAdmin):
    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


for model in (
    OperationalJournalSequence,
    OperationalLogEquipmentLink,
    OperationalLogDocumentLink,
    OperationalLogAuditEvent,
):
    admin.site.register(model, ReadOnlyOperationalAdmin)
