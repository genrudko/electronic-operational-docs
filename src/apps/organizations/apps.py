from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.organizations"
    verbose_name = "Организация и персонал"

    def ready(self) -> None:
        from . import authority_models, signals  # noqa: F401
