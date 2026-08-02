from django.db import migrations, models
import django.db.models.deletion


SOURCE_903N = (
    "Правила по охране труда при эксплуатации электроустановок, "
    "утверждённые приказом Минтруда России от 15.12.2020 № 903н"
)


def populate_condition_details(apps, schema_editor):
    EmployeeOperationalRight = apps.get_model(
        "organizations",
        "EmployeeOperationalRight",
    )
    OperationalRightConditionDetail = apps.get_model(
        "organizations",
        "OperationalRightConditionDetail",
    )
    catalog = {
        "+1": {
            "title": "Условие по пункту 5.4 Правил по охране труда",
            "description": (
                "Право применяется в соответствии с пунктом 5.4 Правил по "
                "охране труда при эксплуатации электроустановок."
            ),
            "source_clause": "пункт 5.4",
            "source_reference": SOURCE_903N,
            "is_resolved": True,
        },
        "+2": {
            "title": "Условие по пункту 5.13 Правил по охране труда",
            "description": (
                "Право применяется в соответствии с пунктом 5.13 Правил по "
                "охране труда при эксплуатации электроустановок."
            ),
            "source_clause": "пункт 5.13",
            "source_reference": SOURCE_903N,
            "is_resolved": True,
        },
    }
    for right in EmployeeOperationalRight.objects.exclude(source_marker="+"):
        marker = (right.source_marker or "").strip()
        if not marker:
            continue
        defaults = catalog.get(marker)
        if defaults is None:
            qualifier = (right.qualifier or "").strip()
            defaults = {
                "title": f"Дополнительное условие {marker}",
                "description": (
                    qualifier
                    or "Текст условия в опубликованной редакции не расшифрован."
                ),
                "source_clause": "",
                "source_reference": right.source_reference,
                "is_resolved": bool(qualifier),
            }
        OperationalRightConditionDetail.objects.update_or_create(
            right=right,
            defaults={"marker": marker, **defaults},
        )


def reverse_condition_details(apps, schema_editor):
    apps.get_model(
        "organizations",
        "OperationalRightConditionDetail",
    ).objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0012_personnel_change_snapshot_blank"),
    ]

    operations = [
        migrations.CreateModel(
            name="OperationalRightConditionDetail",
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
                ("marker", models.CharField(max_length=16, verbose_name="Индекс условия")),
                (
                    "title",
                    models.CharField(
                        max_length=500,
                        verbose_name="Краткое наименование условия",
                    ),
                ),
                ("description", models.TextField(verbose_name="Точное содержание условия")),
                (
                    "source_clause",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Пункт документа",
                    ),
                ),
                (
                    "source_reference",
                    models.CharField(
                        max_length=1000,
                        verbose_name="Источник условия",
                    ),
                ),
                (
                    "is_resolved",
                    models.BooleanField(
                        default=True,
                        verbose_name="Условие расшифровано",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменено")),
                (
                    "right",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="condition_detail",
                        to="organizations.employeeoperationalright",
                        verbose_name="Предоставленное право",
                    ),
                ),
            ],
            options={
                "verbose_name": "условие предоставленного права",
                "verbose_name_plural": "условия предоставленных прав",
                "ordering": ("marker", "right__right_definition__display_order"),
            },
        ),
        migrations.RunPython(
            populate_condition_details,
            reverse_condition_details,
        ),
    ]
