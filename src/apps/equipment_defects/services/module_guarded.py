from __future__ import annotations

from datetime import datetime

from apps.equipment.models import EquipmentAsset
from apps.operational_documents.models import OperationalDocumentRecord
from apps.operational_log.models import OperationalLogEntry
from apps.organizations.models import Employee, Workplace
from apps.system.module_registry import (
    EntryPointClass,
    ModuleAccessDecision,
    ModuleOperation,
    decide_module_access,
    normalize_context,
    require_module_access,
)

from .actions import register_defect as _register_defect


def defect_opj_link_access_decision(
    *,
    organization_id: int,
    workplace_id: int,
    entry_point_class: EntryPointClass,
) -> ModuleAccessDecision:
    context = normalize_context(
        organization=organization_id,
        workplace=workplace_id,
    )
    return decide_module_access(
        context=context,
        module_id="DEFECT",
        capability_id="CAP-DEFECT-OPJ-LINK",
        operation=ModuleOperation.CREATE,
        entry_point_class=entry_point_class,
    )


def require_defect_opj_link_access(
    *,
    organization_id: int,
    workplace_id: int,
    entry_point_class: EntryPointClass,
) -> ModuleAccessDecision:
    context = normalize_context(
        organization=organization_id,
        workplace=workplace_id,
    )
    return require_module_access(
        context=context,
        module_id="DEFECT",
        capability_id="CAP-DEFECT-OPJ-LINK",
        operation=ModuleOperation.CREATE,
        entry_point_class=entry_point_class,
    )


def register_defect(
    *,
    actor: Employee,
    workplace: Workplace,
    equipment: EquipmentAsset,
    discovered_by: Employee,
    detected_at: datetime,
    defect_description: str,
    operational_log_entry: OperationalLogEntry | None = None,
    presentation_key: str | None = None,
) -> OperationalDocumentRecord:
    """Public defect-registration service with the migrated OPJ-link guard."""

    if operational_log_entry is not None:
        require_defect_opj_link_access(
            organization_id=actor.organization_id,
            workplace_id=workplace.pk,
            entry_point_class=EntryPointClass.SERVICE,
        )
    return _register_defect(
        actor=actor,
        workplace=workplace,
        equipment=equipment,
        discovered_by=discovered_by,
        detected_at=detected_at,
        defect_description=defect_description,
        operational_log_entry=operational_log_entry,
        presentation_key=presentation_key,
    )
