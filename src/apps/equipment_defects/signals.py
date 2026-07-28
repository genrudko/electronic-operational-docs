from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.db.models.signals import post_migrate, pre_save
from django.dispatch import receiver

from apps.operational_documents.services import canonical_json, sha256_text

from .models import (
    EquipmentDefectActionEvidence,
    EquipmentDefectContext,
    EquipmentDefectOperationalLogLink,
)


@receiver(
    pre_save,
    sender=EquipmentDefectContext,
    dispatch_uid="equipment_defects_require_equipment_link",
)
def require_equipment_link(sender, instance, **kwargs) -> None:
    del sender, kwargs
    if instance.record_id and not instance.record.equipment_links.exists():
        raise ValidationError(
            "Запись журнала дефектов должна иметь обязательную структурированную связь "
            "с оборудованием."
        )


@receiver(
    pre_save,
    sender=EquipmentDefectActionEvidence,
    dispatch_uid="equipment_defects_verify_action_digest",
)
def verify_action_digest(sender, instance, **kwargs) -> None:
    del sender, kwargs
    expected = sha256_text(canonical_json(instance.canonical_snapshot))
    if instance.sha256 != expected:
        raise ValidationError("SHA-256 подтверждаемого действия не соответствует снимку.")


@receiver(
    pre_save,
    sender=EquipmentDefectOperationalLogLink,
    dispatch_uid="equipment_defects_verify_operational_log_digest",
)
def verify_operational_log_digest(sender, instance, **kwargs) -> None:
    del sender, kwargs
    if (
        instance.operational_log_entry_id
        and instance.entry_digest_snapshot != instance.operational_log_entry.digest
    ):
        raise ValidationError(
            "SHA-256 связи не соответствует исходной записи оперативного журнала."
        )


@receiver(post_migrate, dispatch_uid="equipment_defects_seed_presentation")
def seed_equipment_defect_presentation(sender, **kwargs) -> None:
    del kwargs
    if sender.name != "apps.equipment_defects":
        return
    call_command("seed_equipment_defects", verbosity=0)
