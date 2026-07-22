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
    PowerSystemAliasProposal,
    PowerSystemAssetOccurrence,
    PowerSystemAuthorityOccurrence,
    PowerSystemImportIssue,
    PowerSystemPublication,
    PowerSystemSourceRevision,
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


@admin.register(PowerSystemSourceRevision)
class PowerSystemSourceRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "original_filename",
        "organization",
        "data_profile",
        "source_approval_status",
        "status",
        "total_occurrences",
        "ready_count",
        "review_count",
        "blocked_count",
        "published_count",
        "created_at",
    )
    list_filter = ("status", "source_approval_status", "data_profile")
    search_fields = ("original_filename", "source_reference", "file_sha256")
    readonly_fields = (
        "public_id",
        "file_sha256",
        "source_document_sha256",
        "manifest",
        "type_dictionary",
        "diff_counts",
        "total_occurrences",
        "hierarchy_nodes",
        "authority_rows",
        "alias_rows",
        "issue_rows",
        "ready_count",
        "review_count",
        "blocked_count",
        "excluded_count",
        "published_count",
        "publication_digest",
        "published_at",
        "published_by",
        "created_at",
        "updated_at",
        "discarded_at",
    )

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PowerSystemAssetOccurrence)
class PowerSystemAssetOccurrenceAdmin(admin.ModelAdmin):
    list_display = (
        "occurrence_id",
        "source_revision",
        "source_sheet",
        "source_row",
        "asset_type_code",
        "dispatcher_name_raw",
        "review_status",
        "diff_state",
    )
    list_filter = ("review_status", "diff_state", "record_role", "asset_type_code")
    search_fields = (
        "occurrence_id",
        "dispatcher_name_raw",
        "display_name_normalized",
        "logical_key",
        "external_key",
    )
    readonly_fields = [field.name for field in PowerSystemAssetOccurrence._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PowerSystemAuthorityOccurrence)
class PowerSystemAuthorityOccurrenceAdmin(admin.ModelAdmin):
    list_display = (
        "asset_occurrence",
        "authority_kind",
        "assignment_status",
        "authority_subject_raw",
        "conduct_mode",
        "publication_status",
    )
    list_filter = (
        "authority_kind",
        "assignment_status",
        "conduct_mode",
        "publication_status",
    )
    search_fields = (
        "asset_occurrence__occurrence_id",
        "authority_subject_raw",
        "source_cell_raw",
    )
    readonly_fields = [field.name for field in PowerSystemAuthorityOccurrence._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PowerSystemAliasProposal)
class PowerSystemAliasProposalAdmin(admin.ModelAdmin):
    list_display = (
        "alias_raw",
        "target_name_raw",
        "alias_scope",
        "review_status",
        "publication_status",
    )
    list_filter = ("alias_scope", "review_status", "publication_status")
    search_fields = ("alias_raw", "target_name_raw", "occurrence_id_raw")
    readonly_fields = [field.name for field in PowerSystemAliasProposal._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PowerSystemImportIssue)
class PowerSystemImportIssueAdmin(admin.ModelAdmin):
    list_display = (
        "issue_code",
        "source_revision",
        "severity",
        "category",
        "blocks_automatic_import",
        "status",
    )
    list_filter = ("severity", "category", "blocks_automatic_import", "status")
    search_fields = ("issue_code", "evidence", "recommended_handling")
    readonly_fields = [field.name for field in PowerSystemImportIssue._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(PowerSystemPublication)
class PowerSystemPublicationAdmin(admin.ModelAdmin):
    list_display = ("source_revision", "actor", "digest", "created_at")
    search_fields = ("source_revision__original_filename", "digest")
    readonly_fields = [field.name for field in PowerSystemPublication._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
