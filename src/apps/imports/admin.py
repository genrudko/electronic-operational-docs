from django.contrib import admin

from .models import (
    DataProfile,
    ImportBatch,
    ImportColumn,
    ImportEvent,
    ImportMappingTemplate,
    ImportPublication,
    ImportPublicationRow,
    ImportRow,
)


@admin.register(DataProfile)
class DataProfileAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "kind",
        "sensitivity_level",
        "export_policy",
        "is_default",
        "is_active",
    )
    list_filter = ("kind", "sensitivity_level", "export_policy", "is_active")
    search_fields = ("name", "code", "organization__name")


@admin.register(ImportMappingTemplate)
class ImportMappingTemplateAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "organization",
        "target_registry",
        "usage_count",
        "last_used_at",
        "is_active",
    )
    list_filter = ("target_registry", "is_active")
    search_fields = ("name", "header_signature", "organization__name")
    readonly_fields = (
        "header_signature",
        "mapping",
        "created_by",
        "updated_by",
        "usage_count",
        "last_used_at",
        "created_at",
        "updated_at",
    )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ImportColumnInline(admin.TabularInline):
    model = ImportColumn
    extra = 0
    readonly_fields = (
        "position",
        "source_name",
        "normalized_name",
        "recognized_key",
        "mapped_key",
        "mapping_origin",
        "needs_review",
        "issues",
    )
    can_delete = False


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "organization",
        "data_profile",
        "target_registry",
        "status",
        "data_rows",
        "mapping_revision",
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
        "mapping_revision",
        "mapping_completed_at",
        "review_recalculated_at",
        "review_counts",
        "published_at",
        "published_by",
        "publication_digest",
        "publication_counts",
        "created_at",
        "updated_at",
        "discarded_at",
    )
    inlines = (ImportColumnInline,)


@admin.register(ImportRow)
class ImportRowAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "row_number",
        "status",
        "review_status",
        "decision",
        "decided_by",
    )
    list_filter = ("status", "review_status", "decision")
    search_fields = ("batch__original_filename", "fingerprint")
    readonly_fields = (
        "batch",
        "row_number",
        "source_values",
        "normalized_values",
        "status",
        "issues",
        "fingerprint",
        "mapped_values",
        "review_status",
        "validation_issues",
        "registry_conflicts",
        "decision",
        "decision_values",
        "decision_note",
        "decided_by",
        "decided_at",
        "created_at",
    )


@admin.register(ImportEvent)
class ImportEventAdmin(admin.ModelAdmin):
    list_display = ("batch", "event_type", "actor", "created_at")
    list_filter = ("event_type",)
    readonly_fields = ("batch", "event_type", "actor", "details", "created_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



@admin.register(ImportPublication)
class ImportPublicationAdmin(admin.ModelAdmin):
    list_display = (
        "batch",
        "target_registry",
        "actor",
        "digest",
        "created_at",
    )
    list_filter = ("target_registry",)
    search_fields = ("batch__original_filename", "digest")
    readonly_fields = (
        "public_id",
        "batch",
        "actor",
        "schema_version",
        "target_registry",
        "mapping_revision",
        "canonical_json",
        "digest",
        "result_summary",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ImportPublicationRow)
class ImportPublicationRowAdmin(admin.ModelAdmin):
    list_display = (
        "publication",
        "row",
        "target_model",
        "target_object_id",
        "created_at",
    )
    list_filter = ("target_model",)
    search_fields = (
        "publication__batch__original_filename",
        "target_object_id",
        "digest",
    )
    readonly_fields = (
        "publication",
        "row",
        "target_model",
        "target_object_id",
        "result",
        "digest",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
