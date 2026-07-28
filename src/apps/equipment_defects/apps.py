from django.apps import AppConfig


class EquipmentDefectsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.equipment_defects"
    verbose_name = "Журнал дефектов оборудования"

    def ready(self) -> None:
        from . import signals  # noqa: F401
