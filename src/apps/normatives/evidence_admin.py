from django.contrib import admin

from .evidence_models import EvidenceEvent, LegalModeDecision
from .evidence_services import (
    verify_evidence_event_integrity,
    verify_legal_mode_decision_integrity,
)


class _ReadOnlyEvidenceAdmin(admin.ModelAdmin):
    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(LegalModeDecision)
class LegalModeDecisionAdmin(_ReadOnlyEvidenceAdmin):
    list_display = (
        "decided_at",
        "code",
        "module_id",
        "product_target_mode",
        "proven_legal_mode",
        "integrity_label",
    )
    list_filter = (
        "product_target_mode",
        "proven_legal_mode",
        "normative_evidence_status",
        "local_act_status",
    )
    search_fields = ("code", "module_id", "subject_label", "digest")
    readonly_fields = tuple(
        field.name for field in LegalModeDecision._meta.fields
    )

    @admin.display(description="Целостность")
    def integrity_label(self, obj: LegalModeDecision) -> str:
        return verify_legal_mode_decision_integrity(obj).status.label


@admin.register(EvidenceEvent)
class EvidenceEventAdmin(_ReadOnlyEvidenceAdmin):
    list_display = (
        "occurred_at",
        "event_type",
        "subject_type",
        "subject_id",
        "actor",
        "confirmation_method",
        "integrity_label",
    )
    list_filter = ("event_type", "confirmation_method", "requires_reauthentication")
    search_fields = (
        "subject_type",
        "subject_id",
        "actor__last_name",
        "actor__personnel_number",
        "digest",
        "correlation_id",
    )
    readonly_fields = tuple(field.name for field in EvidenceEvent._meta.fields)

    @admin.display(description="Целостность")
    def integrity_label(self, obj: EvidenceEvent) -> str:
        return verify_evidence_event_integrity(obj).status.label
