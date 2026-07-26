from django.core.management import call_command
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate, dispatch_uid="equipment_defects_seed_presentation")
def seed_equipment_defect_presentation(sender, **kwargs) -> None:
    if sender.name != "apps.equipment_defects":
        return
    call_command("seed_equipment_defects", verbosity=0)
