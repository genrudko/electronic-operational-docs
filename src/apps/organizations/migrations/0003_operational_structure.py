import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("equipment", "0001_equipment_registry"),
        ("organizations", "0002_interface_preferences"),
    ]

    operations = [
        migrations.CreateModel(
            name="DivisionServiceProfile",
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
                    "territorial_base",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="Территориальная база",
                    ),
                ),
                ("service_scope", models.TextField(blank=True, verbose_name="Область обслуживания")),
                (
                    "is_cross_territory",
                    models.BooleanField(
                        default=False,
                        verbose_name="Работает на нескольких территориях",
                    ),
                ),
                (
                    "division",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="service_profile",
                        to="organizations.division",
                        verbose_name="Подразделение",
                    ),
                ),
            ],
            options={
                "verbose_name": "профиль обслуживания подразделения",
                "verbose_name_plural": "профили обслуживания подразделений",
            },
        ),
        migrations.CreateModel(
            name="DivisionEnergySiteService",
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
                    "service_kind",
                    models.CharField(
                        choices=[
                            ("OPERATING_CENTER", "Эксплуатационный контур"),
                            ("OPERATIONAL", "Оперативное обслуживание"),
                            ("MAINTENANCE", "Техническое обслуживание и ремонт"),
                            ("ENGINEERING", "Инженерное сопровождение"),
                            ("SPECIALIZED", "Специализированное обслуживание"),
                        ],
                        max_length=24,
                        verbose_name="Вид обслуживания",
                    ),
                ),
                ("valid_from", models.DateField(verbose_name="Действует с")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Действует по")),
                ("note", models.CharField(blank=True, max_length=500, verbose_name="Примечание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующая связь")),
                (
                    "division",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="energy_site_services",
                        to="organizations.division",
                        verbose_name="Подразделение",
                    ),
                ),
                (
                    "energy_site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="servicing_divisions",
                        to="equipment.energysite",
                        verbose_name="Энергообъект",
                    ),
                ),
            ],
            options={
                "verbose_name": "обслуживание энергообъекта подразделением",
                "verbose_name_plural": "обслуживание энергообъектов подразделениями",
                "ordering": ("energy_site__name", "division__name", "service_kind"),
            },
        ),
        migrations.CreateModel(
            name="EmployeeEnergySiteAuthorization",
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
                    "operational_role",
                    models.CharField(
                        choices=[
                            ("SHIFT_SUPERVISOR", "Начальник смены"),
                            ("DUTY_ELECTRICIAN", "Дежурный электромонтёр"),
                            ("MAINTENANCE", "Персонал ТОиР"),
                            ("SPECIALIST", "Специалист"),
                        ],
                        max_length=24,
                        verbose_name="Роль на энергообъекте",
                    ),
                ),
                ("valid_from", models.DateField(verbose_name="Допущен с")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Допущен по")),
                ("note", models.CharField(blank=True, max_length=500, verbose_name="Примечание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующий допуск")),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="energy_site_authorizations",
                        to="organizations.employee",
                        verbose_name="Сотрудник",
                    ),
                ),
                (
                    "energy_site",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authorized_employees",
                        to="equipment.energysite",
                        verbose_name="Энергообъект",
                    ),
                ),
            ],
            options={
                "verbose_name": "допуск сотрудника к энергообъекту",
                "verbose_name_plural": "допуски сотрудников к энергообъектам",
                "ordering": ("employee__last_name", "energy_site__name", "operational_role"),
            },
        ),
        migrations.CreateModel(
            name="OperationalReportingLine",
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
                    "relation_type",
                    models.CharField(
                        choices=[
                            ("DIRECT", "Непосредственное оперативное руководство"),
                            ("FUNCTIONAL", "Функциональное оперативное руководство"),
                        ],
                        default="DIRECT",
                        max_length=16,
                        verbose_name="Вид подчинённости",
                    ),
                ),
                ("valid_from", models.DateField(verbose_name="Действует с")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Действует по")),
                ("note", models.CharField(blank=True, max_length=500, verbose_name="Примечание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующая связь")),
                (
                    "subordinate_division",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="operational_reporting_lines",
                        to="organizations.division",
                        verbose_name="Подчинённое подразделение",
                    ),
                ),
                (
                    "supervisor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="operationally_supervised_divisions",
                        to="organizations.employee",
                        verbose_name="Оперативный руководитель",
                    ),
                ),
            ],
            options={
                "verbose_name": "оперативная подчинённость",
                "verbose_name_plural": "оперативная подчинённость",
                "ordering": ("subordinate_division__name", "relation_type", "valid_from"),
            },
        ),
        migrations.AddConstraint(
            model_name="divisionenergysiteservice",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(valid_until__isnull=True)
                    | models.Q(valid_until__gte=models.F("valid_from"))
                ),
                name="division_site_service_valid_window",
            ),
        ),
        migrations.AddConstraint(
            model_name="divisionenergysiteservice",
            constraint=models.UniqueConstraint(
                fields=("division", "energy_site", "service_kind", "valid_from"),
                name="uniq_division_site_service_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="employeeenergysiteauthorization",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(valid_until__isnull=True)
                    | models.Q(valid_until__gte=models.F("valid_from"))
                ),
                name="employee_site_authorization_valid_window",
            ),
        ),
        migrations.AddConstraint(
            model_name="employeeenergysiteauthorization",
            constraint=models.UniqueConstraint(
                fields=("employee", "energy_site", "operational_role", "valid_from"),
                name="uniq_employee_site_authorization_start",
            ),
        ),
        migrations.AddConstraint(
            model_name="operationalreportingline",
            constraint=models.CheckConstraint(
                condition=(
                    models.Q(valid_until__isnull=True)
                    | models.Q(valid_until__gte=models.F("valid_from"))
                ),
                name="operational_reporting_valid_window",
            ),
        ),
        migrations.AddConstraint(
            model_name="operationalreportingline",
            constraint=models.UniqueConstraint(
                fields=("supervisor", "subordinate_division", "relation_type", "valid_from"),
                name="uniq_operational_reporting_start",
            ),
        ),
    ]
