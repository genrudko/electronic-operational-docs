from django.apps import AppConfig


class ImportsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.imports"
    verbose_name = "Импорт справочников"

    def ready(self) -> None:
        from .master_data_runtime import install_master_data_contracts

        install_master_data_contracts()
