from django.apps import AppConfig


class OrganizationsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.organizations"
    verbose_name = "Организация и персонал"

    def ready(self) -> None:
        from . import (  # noqa: F401
            authority_models,
            personnel_management_models,
            signals,
        )
        from .personnel_management_models import PersonnelChangeRecord

        # Empty before/after snapshots are valid at the creation and batch
        # boundaries. The migration records the same validation state.
        PersonnelChangeRecord._meta.get_field("before_snapshot").blank = True
        PersonnelChangeRecord._meta.get_field("after_snapshot").blank = True
