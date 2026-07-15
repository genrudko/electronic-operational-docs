from django.contrib import admin

from .models import (
    AdjacentSubjectRelation,
    AdjacentSubjectRelationRevision,
    DispatchingAuditEvent,
    DispatchLevel,
    DispatchSubject,
    ManagementObject,
    ManagementRevision,
    SupervisionObject,
    SupervisionRevision,
)


@admin.register(DispatchLevel)
class DispatchLevelAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "level_type", "rank", "organization", "is_active")
    list_filter = ("level_type", "is_active", "organization")
    search_fields = ("code", "name")


@admin.register(DispatchSubject)
class DispatchSubjectAdmin(admin.ModelAdmin):
    list_display = ("code", "short_name", "subject_type", "is_external", "organization")
    list_filter = ("subject_type", "is_external", "is_active", "organization")
    search_fields = ("code", "name", "short_name")


@admin.register(ManagementObject)
class ManagementObjectAdmin(admin.ModelAdmin):
    list_display = ("equipment", "organization", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("equipment__code", "equipment__technical_name")


@admin.register(SupervisionObject)
class SupervisionObjectAdmin(admin.ModelAdmin):
    list_display = ("equipment", "organization", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("equipment__code", "equipment__technical_name")


@admin.register(ManagementRevision)
class ManagementRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "management_object",
        "revision_number",
        "level",
        "subject",
        "effective_from",
        "effective_until",
        "status",
    )
    list_filter = ("status", "level", "subject")
    readonly_fields = ("published_at", "published_by", "digest", "created_at")


@admin.register(SupervisionRevision)
class SupervisionRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "supervision_object",
        "revision_number",
        "level",
        "subject",
        "is_information_only",
        "effective_from",
        "effective_until",
        "status",
    )
    list_filter = ("status", "is_information_only", "level", "subject")
    readonly_fields = ("published_at", "published_by", "digest", "created_at")


@admin.register(AdjacentSubjectRelation)
class AdjacentSubjectRelationAdmin(admin.ModelAdmin):
    list_display = ("code", "source_subject", "target_subject", "organization", "is_active")
    list_filter = ("is_active", "organization")
    search_fields = ("code", "source_subject__name", "target_subject__name")


@admin.register(AdjacentSubjectRelationRevision)
class AdjacentSubjectRelationRevisionAdmin(admin.ModelAdmin):
    list_display = (
        "relation",
        "revision_number",
        "effective_from",
        "effective_until",
        "status",
    )
    list_filter = ("status",)
    readonly_fields = ("published_at", "published_by", "digest", "created_at")


@admin.register(DispatchingAuditEvent)
class DispatchingAuditEventAdmin(admin.ModelAdmin):
    list_display = ("event_type", "actor_employee", "organization", "created_at")
    list_filter = ("event_type", "organization")
    readonly_fields = (
        "organization",
        "event_type",
        "actor_employee",
        "management_revision",
        "supervision_revision",
        "adjacent_revision",
        "payload",
        "created_at",
    )
