from django.contrib import admin

from .models import ImportBatch, ImportColumn, ImportEvent, ImportRow


class ImportColumnInline(admin.TabularInline):
    model = ImportColumn
    extra = 0
    readonly_fields = (
        "position",
        "source_name",
        "normalized_name",
        "recognized_key",
        "needs_review",
        "issues",
    )
    can_delete = False


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "organization",
        "target_registry",
        "status",
        "data_rows",
        "warning_count",
        "created_at",
    )
    list_filter = ("status", "target_registry", "source_format")
    search_fields = ("original_filename", "file_sha256")
    readonly_fields = (
        "public_id",
        "file_sha256",
        "file_size",
        "status_counts",
        "created_at",
        "updated_at",
        "discarded_at",
    )
    inlines = (ImportColumnInline,)


@admin.register(ImportRow)
class ImportRowAdmin(admin.ModelAdmin):
    list_display = ("batch", "row_number", "status", "fingerprint")
    list_filter = ("status",)
    search_fields = ("batch__original_filename", "fingerprint")
    readonly_fields = (
        "batch",
        "row_number",
        "source_values",
        "normalized_values",
        "status",
        "issues",
        "fingerprint",
        "created_at",
    )


@admin.register(ImportEvent)
class ImportEventAdmin(admin.ModelAdmin):
    list_display = ("batch", "event_type", "actor", "created_at")
    list_filter = ("event_type",)
    readonly_fields = ("batch", "event_type", "actor", "details", "created_at")
