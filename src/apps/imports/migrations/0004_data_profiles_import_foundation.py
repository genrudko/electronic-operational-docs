# Generated for Patch 011.4.

import django.db.models.deletion
from django.db import migrations, models


PROFILE_SPECS = (
    {
        "code": "presentation-safe",
        "name": "Безопасная презентационная база",
        "kind": "PRESENTATION_SAFE",
        "sensitivity_level": "SAFE_DEMO",
        "export_policy": "ALLOWED",
        "allows_real_personal_data": False,
        "is_default": True,
        "description": (
            "Предметная демонстрационная база: реальные диспетчерские наименования "
            "допустимы, персональные данные и реальные оперативные события запрещены."
        ),
    },
    {
        "code": "local-validation",
        "name": "Локальная проверочная база",
        "kind": "LOCAL_VALIDATION",
        "sensitivity_level": "PERSONAL_INTERNAL",
        "export_policy": "PROHIBITED",
        "allows_real_personal_data": True,
        "is_default": False,
        "description": (
            "Локальная база углублённой проверки. Может содержать реальные ФИО и "
            "внутреннюю номенклатуру; обычный экспорт запрещён."
        ),
    },
    {
        "code": "automated-tests",
        "name": "Автоматизированные тесты",
        "kind": "AUTOMATED_TEST",
        "sensitivity_level": "SYNTHETIC",
        "export_policy": "PROHIBITED",
        "allows_real_personal_data": False,
        "is_default": False,
        "description": (
            "Полностью синтетические данные для изолированных автоматизированных проверок."
        ),
    },
)


def create_profiles_and_assign_batches(apps, schema_editor):
    Organization = apps.get_model("organizations", "Organization")
    DataProfile = apps.get_model("imports", "DataProfile")
    ImportBatch = apps.get_model("imports", "ImportBatch")

    for organization in Organization.objects.all().iterator():
        profiles = {}
        for spec in PROFILE_SPECS:
            defaults = {key: value for key, value in spec.items() if key != "code"}
            profile, _created = DataProfile.objects.get_or_create(
                organization_id=organization.pk,
                code=spec["code"],
                defaults=defaults,
            )
            profiles[spec["code"]] = profile
        ImportBatch.objects.filter(
            organization_id=organization.pk,
            data_profile__isnull=True,
        ).update(data_profile_id=profiles["presentation-safe"].pk)


def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("imports", "0003_controlled_publication"),
    ]

    operations = [
        migrations.CreateModel(
            name="DataProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "code",
                    models.SlugField(max_length=64, verbose_name="Внутренний код"),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="Наименование"),
                ),
                (
                    "kind",
                    models.CharField(
                        choices=[
                            ("PRESENTATION_SAFE", "Безопасная презентационная база"),
                            ("LOCAL_VALIDATION", "Локальная проверочная база"),
                            ("AUTOMATED_TEST", "Автоматизированные тесты"),
                        ],
                        max_length=24,
                        verbose_name="Тип профиля",
                    ),
                ),
                (
                    "sensitivity_level",
                    models.CharField(
                        choices=[
                            ("SYNTHETIC", "Синтетические данные"),
                            ("SAFE_DEMO", "Безопасные демонстрационные данные"),
                            (
                                "INTERNAL_OPERATIONAL",
                                "Внутренняя оперативная номенклатура",
                            ),
                            (
                                "PERSONAL_INTERNAL",
                                "Внутренние данные с персональными сведениями",
                            ),
                        ],
                        max_length=24,
                        verbose_name="Уровень чувствительности",
                    ),
                ),
                (
                    "export_policy",
                    models.CharField(
                        choices=[
                            ("ALLOWED", "Разрешён безопасный экспорт"),
                            ("RESTRICTED", "Экспорт только после проверки"),
                            ("PROHIBITED", "Обычный экспорт запрещён"),
                        ],
                        max_length=16,
                        verbose_name="Политика экспорта",
                    ),
                ),
                (
                    "allows_real_personal_data",
                    models.BooleanField(
                        default=False,
                        verbose_name="Допускает реальные персональные данные",
                    ),
                ),
                (
                    "is_default",
                    models.BooleanField(
                        default=False,
                        verbose_name="Профиль по умолчанию",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Действующий"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Назначение и ограничения"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создан"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Изменён"),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="data_profiles",
                        to="organizations.organization",
                        verbose_name="Организация",
                    ),
                ),
            ],
            options={
                "verbose_name": "профиль данных",
                "verbose_name_plural": "профили данных",
                "ordering": ("organization__name", "name"),
            },
        ),
        migrations.AddConstraint(
            model_name="dataprofile",
            constraint=models.UniqueConstraint(
                fields=("organization", "code"),
                name="uniq_data_profile_code_per_org",
            ),
        ),
        migrations.AddConstraint(
            model_name="dataprofile",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_default", True)),
                fields=("organization",),
                name="uniq_default_data_profile_per_org",
            ),
        ),
        migrations.CreateModel(
            name="ImportMappingTemplate",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "target_registry",
                    models.CharField(
                        choices=[
                            ("ORGANIZATION", "Организация и персонал"),
                            ("EQUIPMENT", "Оборудование"),
                            ("DISPATCHING", "Управление и ведение"),
                            ("OTHER", "Другой справочник"),
                        ],
                        max_length=24,
                        verbose_name="Назначение импорта",
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=255, verbose_name="Наименование схемы"),
                ),
                (
                    "header_signature",
                    models.CharField(
                        max_length=64,
                        verbose_name="SHA-256 структуры заголовков",
                    ),
                ),
                (
                    "mapping",
                    models.JSONField(default=dict, verbose_name="Сопоставление колонок"),
                ),
                (
                    "usage_count",
                    models.PositiveIntegerField(
                        default=0,
                        verbose_name="Количество применений",
                    ),
                ),
                (
                    "last_used_at",
                    models.DateTimeField(
                        blank=True,
                        null=True,
                        verbose_name="Последнее применение",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        verbose_name="Действующая схема",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="Создана"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="Изменена"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_import_mapping_templates",
                        to="organizations.employee",
                        verbose_name="Создал",
                    ),
                ),
                (
                    "organization",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="import_mapping_templates",
                        to="organizations.organization",
                        verbose_name="Организация",
                    ),
                ),
                (
                    "updated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="updated_import_mapping_templates",
                        to="organizations.employee",
                        verbose_name="Изменил",
                    ),
                ),
            ],
            options={
                "verbose_name": "схема сопоставления импорта",
                "verbose_name_plural": "схемы сопоставления импорта",
                "ordering": ("organization__name", "target_registry", "name"),
            },
        ),
        migrations.AddConstraint(
            model_name="importmappingtemplate",
            constraint=models.UniqueConstraint(
                fields=("organization", "target_registry", "header_signature"),
                name="uniq_mapping_template_headers",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="applied_mapping_template",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="applied_batches",
                to="imports.importmappingtemplate",
                verbose_name="Применённая схема сопоставления",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="data_profile",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name="import_batches",
                to="imports.dataprofile",
                verbose_name="Профиль данных",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="header_signature",
            field=models.CharField(
                blank=True,
                editable=False,
                max_length=64,
                verbose_name="SHA-256 структуры заголовков",
            ),
        ),
        migrations.AddField(
            model_name="importbatch",
            name="source_reference",
            field=models.CharField(
                blank=True,
                max_length=1000,
                verbose_name="Источник или основание",
            ),
        ),
        migrations.RunPython(create_profiles_and_assign_batches, noop_reverse),
        migrations.AlterField(
            model_name="importbatch",
            name="data_profile",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="import_batches",
                to="imports.dataprofile",
                verbose_name="Профиль данных",
            ),
        ),
        migrations.AlterField(
            model_name="importpublication",
            name="schema_version",
            field=models.CharField(
                default="eod.import.publication.v2",
                max_length=64,
                verbose_name="Версия схемы снимка",
            ),
        ),
        migrations.AlterField(
            model_name="importcolumn",
            name="mapping_origin",
            field=models.CharField(
                choices=[
                    ("AUTO", "Предложено автоматически"),
                    ("TEMPLATE", "Из сохранённой схемы"),
                    ("MANUAL", "Назначено пользователем"),
                    ("IGNORED", "Не используется"),
                ],
                default="AUTO",
                max_length=12,
                verbose_name="Источник сопоставления",
            ),
        ),
        migrations.AlterField(
            model_name="importevent",
            name="event_type",
            field=models.CharField(
                choices=[
                    ("UPLOADED", "Файл загружен"),
                    ("PARSED", "Предварительный просмотр сформирован"),
                    ("FAILED", "Разбор завершился ошибкой"),
                    ("DISCARDED", "Загрузка убрана из рабочего списка"),
                    ("MAPPING_UPDATED", "Сопоставление колонок подтверждено"),
                    (
                        "MAPPING_TEMPLATE_APPLIED",
                        "Применена сохранённая схема сопоставления",
                    ),
                    (
                        "MAPPING_TEMPLATE_SAVED",
                        "Схема сопоставления сохранена",
                    ),
                    ("REVIEW_RECALCULATED", "Проверка строк пересчитана"),
                    ("ROW_DECISION", "Принято решение по строке"),
                    ("BULK_DECISION", "Выполнено массовое решение"),
                    ("PUBLISHED", "Принятые строки опубликованы"),
                ],
                max_length=24,
                verbose_name="Событие",
            ),
        ),
    ]
