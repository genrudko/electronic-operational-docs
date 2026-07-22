import uuid

import django.db.models.deletion
from django.db import migrations, models
from django.db.models import F, Q


RIGHT_DEFINITIONS = (
    ("dispatch_application_submit", "Подача диспетчерской заявки", "APPLICATIONS", "BOOLEAN"),
    ("dispatch_application_approve", "Согласование диспетчерской заявки", "APPLICATIONS", "BOOLEAN"),
    ("operational_application_submit", "Подача оперативной заявки", "APPLICATIONS", "BOOLEAN"),
    ("operational_application_approve", "Согласование оперативной заявки", "APPLICATIONS", "BOOLEAN"),
    ("interlock_bypass_authorization", "Выдача разрешения на деблокирование при неисправной блокировке", "WORK_SAFETY", "BOOLEAN"),
    ("worksite_preparation_and_admission_authorization", "Выдача разрешения на подготовку рабочего места и допуск", "WORK_SAFETY", "BOOLEAN"),
    ("permit_and_order_issue", "Выдача наряда-допуска и распоряжения", "WORK_SAFETY", "QUALIFIED"),
    ("responsible_work_manager", "Ответственный руководитель работ", "WORK_SAFETY", "QUALIFIED"),
    ("admitting_person", "Допускающий", "WORK_SAFETY", "QUALIFIED"),
    ("work_supervisor", "Производитель работ", "WORK_SAFETY", "QUALIFIED"),
    ("observer", "Наблюдающий", "WORK_SAFETY", "QUALIFIED"),
    ("team_member", "Член бригады", "WORK_SAFETY", "BOOLEAN"),
    ("sole_inspection", "Единоличный осмотр", "WORK_SAFETY", "QUALIFIED"),
    ("operational_communications", "Ведение оперативных переговоров", "COMMUNICATIONS", "BOOLEAN"),
    ("switching_operation", "Производство переключений", "SWITCHING", "QUALIFIED"),
    ("switching_supervision", "Контроль переключений", "SWITCHING", "QUALIFIED"),
    ("work_at_height", "Работы на высоте", "SPECIAL_WORK", "QUALIFIED"),
    ("live_work", "Работы под напряжением на токоведущих частях", "SPECIAL_WORK", "QUALIFIED"),
    ("induced_voltage_work", "Работы под наведённым напряжением", "SPECIAL_WORK", "QUALIFIED"),
    ("high_voltage_testing", "Испытания оборудования повышенным напряжением", "SPECIAL_WORK", "QUALIFIED"),
    ("rza_maintenance_category", "Категория допуска к техническому обслуживанию устройств РЗА", "RZA", "ENUM"),
)


def seed_right_definitions(apps, schema_editor):
    Right = apps.get_model("organizations", "OperationalRightDefinition")
    for order, (code, name, category, value_kind) in enumerate(RIGHT_DEFINITIONS, start=10):
        Right.objects.update_or_create(
            code=code,
            defaults={
                "name": name,
                "category": category,
                "value_kind": value_kind,
                "display_order": order,
                "is_active": True,
            },
        )



def populate_employee_public_ids(apps, schema_editor):
    Employee = apps.get_model("organizations", "Employee")
    for employee in Employee.objects.filter(public_id__isnull=True).iterator():
        employee.public_id = uuid.uuid4()
        employee.save(update_fields=("public_id",))

def noop_reverse(apps, schema_editor):
    return None


class Migration(migrations.Migration):
    dependencies = [
        ("organizations", "0006_journal_simplified_time_input"),
    ]

    operations = [
        migrations.AddField(
            model_name="employee",
            name="public_id",
            field=models.UUIDField(editable=False, null=True, verbose_name="Публичный идентификатор"),
        ),
        migrations.RunPython(populate_employee_public_ids, noop_reverse),
        migrations.AlterField(
            model_name="employee",
            name="public_id",
            field=models.UUIDField(
                default=uuid.uuid4,
                editable=False,
                unique=True,
                verbose_name="Публичный идентификатор",
            ),
        ),
        migrations.CreateModel(
            name="OperationalRightDefinition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("code", models.SlugField(max_length=96, unique=True, verbose_name="Код права")),
                ("name", models.CharField(max_length=500, verbose_name="Наименование права")),
                ("category", models.CharField(choices=[("APPLICATIONS", "Заявки"), ("WORK_SAFETY", "Безопасное производство работ"), ("SWITCHING", "Переключения"), ("COMMUNICATIONS", "Оперативные переговоры"), ("SPECIAL_WORK", "Специальные работы"), ("RZA", "Релейная защита и автоматика")], max_length=24, verbose_name="Категория")),
                ("value_kind", models.CharField(choices=[("BOOLEAN", "Право предоставлено или не предоставлено"), ("QUALIFIED", "Право с квалификатором или областью действия"), ("ENUM", "Перечислимое квалификационное значение")], default="BOOLEAN", max_length=16, verbose_name="Тип значения")),
                ("description", models.TextField(blank=True, verbose_name="Пояснение")),
                ("display_order", models.PositiveSmallIntegerField(default=0, verbose_name="Порядок отображения")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующее право")),
            ],
            options={"verbose_name": "вид оперативного права", "verbose_name_plural": "виды оперативных прав", "ordering": ("display_order", "name")},
        ),
        migrations.CreateModel(
            name="EmployeeQualification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("personnel_category", models.CharField(max_length=128, verbose_name="Категория персонала")),
                ("electrical_safety_group", models.CharField(blank=True, max_length=16, verbose_name="Группа по электробезопасности")),
                ("voltage_scope", models.CharField(blank=True, max_length=255, verbose_name="Класс напряжения")),
                ("electrical_installation_scope", models.TextField(blank=True, verbose_name="Область электроустановок")),
                ("valid_from", models.DateField(verbose_name="Действует с")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Действует по")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующая квалификация")),
                ("source_reference", models.CharField(max_length=1000, verbose_name="Источник или основание")),
                ("source_file_sha256", models.CharField(max_length=64, verbose_name="SHA-256 исходного файла")),
                ("source_row_number", models.PositiveIntegerField(verbose_name="Строка исходного файла")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="qualifications", to="organizations.employee", verbose_name="Сотрудник")),
            ],
            options={"verbose_name": "квалификация сотрудника", "verbose_name_plural": "квалификации сотрудников", "ordering": ("employee__last_name", "-valid_from", "-id")},
        ),
        migrations.CreateModel(
            name="EmployeeOperationalRight",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("qualifier", models.CharField(blank=True, max_length=500, verbose_name="Квалификатор")),
                ("scope_text", models.TextField(blank=True, verbose_name="Область действия")),
                ("source_marker", models.CharField(max_length=500, verbose_name="Исходная отметка")),
                ("source_reference", models.CharField(max_length=1000, verbose_name="Источник или основание")),
                ("source_file_sha256", models.CharField(max_length=64, verbose_name="SHA-256 исходного файла")),
                ("source_row_number", models.PositiveIntegerField(verbose_name="Строка исходного файла")),
                ("valid_from", models.DateField(verbose_name="Действует с")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Действует по")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующее назначение")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="operational_rights", to="organizations.employee", verbose_name="Сотрудник")),
                ("right_definition", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="employee_grants", to="organizations.operationalrightdefinition", verbose_name="Вид права")),
            ],
            options={"verbose_name": "оперативное право сотрудника", "verbose_name_plural": "оперативные права сотрудников", "ordering": ("employee__last_name", "right_definition__display_order", "right_definition__name")},
        ),
        migrations.AddConstraint(model_name="employeequalification", constraint=models.CheckConstraint(condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")), name="employee_qualification_valid_window")),
        migrations.AddConstraint(model_name="employeequalification", constraint=models.UniqueConstraint(fields=("employee", "source_file_sha256", "source_row_number"), name="uniq_employee_qualification_source_row")),
        migrations.AddConstraint(model_name="employeeoperationalright", constraint=models.CheckConstraint(condition=Q(valid_until__isnull=True) | Q(valid_until__gte=F("valid_from")), name="employee_operational_right_valid_window")),
        migrations.AddConstraint(model_name="employeeoperationalright", constraint=models.UniqueConstraint(fields=("employee", "right_definition", "source_file_sha256", "source_row_number"), name="uniq_employee_right_source_row")),
        migrations.RunPython(seed_right_definitions, noop_reverse),
    ]
