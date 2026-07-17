from django.apps import AppConfig


class OperationalLogConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.operational_log"
    verbose_name = "Оперативный журнал"
