from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="ModuleActivationRule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("module_id", models.CharField(max_length=64, verbose_name="Стабильный идентификатор модуля")),
                ("scope_type", models.CharField(choices=[("ORGANIZATION", "Организация"), ("ENERGY_SITE", "Энергообъект"), ("WORKPLACE", "Рабочее место")], max_length=24, verbose_name="Тип области")),
                ("scope_id", models.PositiveBigIntegerField(verbose_name="Идентификатор области")),
                ("organization_id", models.PositiveBigIntegerField(verbose_name="Идентификатор организации")),
                ("state", models.CharField(choices=[("AVAILABLE", "Доступен"), ("CONFIGURED", "Настроен"), ("ACTIVE", "Активен"), ("READ_ONLY", "Только чтение"), ("INACTIVE", "Неактивен"), ("RETIRED", "Выведен")], default="CONFIGURED", max_length=24, verbose_name="Явное состояние")),
                ("configuration_ready", models.BooleanField(default=False, verbose_name="Конфигурация проверена")),
                ("configuration", models.JSONField(blank=True, default=dict, verbose_name="Конфигурация")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменено")),
            ],
            options={
                "verbose_name": "правило активации модуля",
                "verbose_name_plural": "правила активации модулей",
                "ordering": ("module_id", "organization_id", "scope_type", "scope_id"),
                "indexes": [models.Index(fields=["organization_id", "module_id", "scope_type", "scope_id"], name="system_modact_lookup_idx")],
                "constraints": [models.UniqueConstraint(fields=("module_id", "scope_type", "scope_id"), name="uniq_module_activation_exact_scope")],
            },
        ),
        migrations.CreateModel(
            name="ModuleActivationAuditEvent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("module_id", models.CharField(max_length=64, verbose_name="Стабильный идентификатор модуля")),
                ("scope_type", models.CharField(choices=[("ORGANIZATION", "Организация"), ("ENERGY_SITE", "Энергообъект"), ("WORKPLACE", "Рабочее место")], max_length=24, verbose_name="Тип области")),
                ("scope_id", models.PositiveBigIntegerField(verbose_name="Идентификатор области")),
                ("organization_id", models.PositiveBigIntegerField(verbose_name="Идентификатор организации")),
                ("previous_explicit_state", models.CharField(blank=True, max_length=24, verbose_name="Предыдущее явное состояние")),
                ("previous_effective_state", models.CharField(max_length=24, verbose_name="Предыдущее эффективное состояние")),
                ("requested_new_state", models.CharField(max_length=24, verbose_name="Запрошенное состояние")),
                ("resulting_effective_state", models.CharField(max_length=24, verbose_name="Результирующее эффективное состояние")),
                ("actor_identity", models.CharField(max_length=255, verbose_name="Идентификатор инициатора")),
                ("occurred_at", models.DateTimeField(auto_now_add=True, verbose_name="Время события")),
                ("reason", models.CharField(max_length=1000, verbose_name="Причина")),
                ("configuration_validation", models.CharField(max_length=255, verbose_name="Проверка конфигурации")),
                ("dependency_validation", models.CharField(max_length=1000, verbose_name="Проверка зависимостей")),
                ("result", models.CharField(choices=[("ALLOWED", "Разрешено"), ("DENIED", "Отклонено")], max_length=16, verbose_name="Результат")),
                ("denial_reason_code", models.CharField(blank=True, max_length=128, verbose_name="Код отказа")),
                ("correlation_id", models.UUIDField(default=uuid.uuid4, editable=False, verbose_name="Корреляционный идентификатор")),
                ("manifest_contract_version", models.CharField(max_length=32, verbose_name="Версия manifest contract")),
            ],
            options={
                "verbose_name": "событие аудита активации модуля",
                "verbose_name_plural": "события аудита активации модулей",
                "ordering": ("occurred_at", "pk"),
                "indexes": [models.Index(fields=["module_id", "organization_id", "scope_type", "scope_id", "occurred_at"], name="system_modaudit_lookup_idx")],
            },
        ),
    ]
