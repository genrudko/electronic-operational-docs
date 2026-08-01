from django.apps import AppConfig


class NormativesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.normatives"
    verbose_name = "Нормативный реестр"

    def ready(self) -> None:
        # Evidence models live in a bounded module but must be registered in the
        # normatives app registry before checks, migrations, admin and services run.
        from . import evidence_admin, evidence_models, evidence_signals  # noqa: F401
