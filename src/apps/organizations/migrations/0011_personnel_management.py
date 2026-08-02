from __future__ import annotations

import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("organizations", "0010_publish_demo_personnel_authority_matrix"),
    ]

    operations = [
        migrations.CreateModel(
            name="OrganizationOperationalProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("relation_kind", models.CharField(choices=[("OWN", "Собственная организация"), ("DISPATCH_CENTER", "Диспетчерский центр"), ("RELATED_GRID", "Смежная сетевая организация"), ("RELATED_SITE", "Смежный энергообъект"), ("COMMERCIAL_DISPATCH", "Коммерческий диспетчерский центр"), ("CONTRACTOR", "Подрядная организация"), ("OTHER", "Иная внешняя организация")], default="OWN", max_length=32, verbose_name="Вид отношения")),
                ("directory_scope", models.TextField(blank=True, verbose_name="Область включения в справочник")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующий профиль")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменён")),
                ("organization", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="operational_profile", to="organizations.organization", verbose_name="Организация")),
            ],
            options={
                "verbose_name": "операционный профиль организации",
                "verbose_name_plural": "операционные профили организаций",
            },
        ),
        migrations.CreateModel(
            name="EmployeeContactProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("primary_phone", models.CharField(blank=True, max_length=100, verbose_name="Основной телефон")),
                ("operational_phone", models.CharField(blank=True, max_length=100, verbose_name="Оперативный телефон")),
                ("email", models.EmailField(blank=True, max_length=254, verbose_name="Электронная почта")),
                ("availability_schedule", models.CharField(blank=True, max_length=255, verbose_name="Часы работы")),
                ("is_round_the_clock", models.BooleanField(default=False, verbose_name="Круглосуточный контакт")),
                ("note", models.TextField(blank=True, verbose_name="Примечание")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создан")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменён")),
                ("employee", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="contact_profile", to="organizations.employee", verbose_name="Сотрудник")),
            ],
            options={
                "verbose_name": "контактный профиль сотрудника",
                "verbose_name_plural": "контактные профили сотрудников",
            },
        ),
        migrations.CreateModel(
            name="EmployeeSpecialQualification",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("kind", models.CharField(choices=[("HEIGHT", "Группа допуска к работам на высоте"), ("RZA", "Категория допуска по РЗА"), ("LIVE_WORK", "Допуск к работам под напряжением"), ("OTHER", "Иная специальная квалификация")], max_length=24, verbose_name="Вид квалификации")),
                ("level", models.CharField(max_length=64, verbose_name="Уровень или категория")),
                ("scope_text", models.TextField(blank=True, verbose_name="Область действия")),
                ("valid_from", models.DateField(verbose_name="Действует с")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Действует по")),
                ("basis_reference", models.CharField(max_length=1000, verbose_name="Документ-основание")),
                ("source_file_sha256", models.CharField(blank=True, max_length=64, verbose_name="SHA-256 исходного файла")),
                ("source_row_number", models.PositiveIntegerField(blank=True, null=True, verbose_name="Строка исходного файла")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующая квалификация")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="special_qualifications", to="organizations.employee", verbose_name="Сотрудник")),
            ],
            options={
                "verbose_name": "специальная квалификация сотрудника",
                "verbose_name_plural": "специальные квалификации сотрудников",
                "ordering": ("employee__last_name", "kind", "-valid_from", "-id"),
            },
        ),
        migrations.CreateModel(
            name="ExternalOperationalContact",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("relation_kind", models.CharField(choices=[("DISPATCH", "Диспетчерский персонал"), ("OPERATIONAL", "Оперативный персонал"), ("MANAGEMENT", "Руководство"), ("CONTROL_CENTER", "Персонал центра управления сетями"), ("COMMERCIAL_DISPATCH", "Коммерческий диспетчер"), ("RELATED_SITE", "Персонал смежного энергообъекта")], max_length=32, verbose_name="Роль во взаимодействии")),
                ("operational_scope", models.TextField(blank=True, verbose_name="Область взаимодействия")),
                ("authority_summary", models.TextField(blank=True, verbose_name="Полномочия во взаимодействии")),
                ("valid_from", models.DateField(verbose_name="Действует с")),
                ("valid_until", models.DateField(blank=True, null=True, verbose_name="Действует по")),
                ("basis_reference", models.CharField(max_length=1000, verbose_name="Документ-основание")),
                ("is_active", models.BooleanField(default=True, verbose_name="Действующая запись")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создана")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Изменена")),
                ("employee", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="external_operational_contacts", to="organizations.employee", verbose_name="Сотрудник внешней организации")),
                ("host_organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="external_operational_directory", to="organizations.organization", verbose_name="Организация, ведущая справочник")),
            ],
            options={
                "verbose_name": "внешний оперативный контакт",
                "verbose_name_plural": "внешние оперативные контакты",
                "ordering": ("employee__organization__name", "relation_kind", "employee__last_name"),
            },
        ),
        migrations.CreateModel(
            name="PersonnelImportBatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("import_kind", models.CharField(choices=[("INTERNAL_MATRIX", "Матрица штатного персонала"), ("EXTERNAL_DIRECTORY", "Внешний оперативный справочник")], max_length=32, verbose_name="Вид импорта")),
                ("status", models.CharField(choices=[("PREVIEW", "Предварительный просмотр"), ("PUBLISHED", "Опубликовано"), ("REJECTED", "Отклонено")], default="PREVIEW", max_length=16, verbose_name="Состояние")),
                ("uploaded_name", models.CharField(max_length=255, verbose_name="Имя файла")),
                ("file_sha256", models.CharField(max_length=64, unique=True, verbose_name="SHA-256 файла")),
                ("sheet_name", models.CharField(blank=True, max_length=255, verbose_name="Лист")),
                ("source_reference", models.CharField(max_length=1000, verbose_name="Документ-основание")),
                ("effective_from", models.DateField(verbose_name="Действует с")),
                ("preview", models.JSONField(default=dict, verbose_name="Результат предварительного просмотра")),
                ("validation_errors", models.JSONField(default=list, verbose_name="Ошибки проверки")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Загружен")),
                ("published_at", models.DateTimeField(blank=True, null=True, verbose_name="Опубликован")),
                ("published_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="published_personnel_import_batches", to=settings.AUTH_USER_MODEL, verbose_name="Опубликовал")),
                ("source_organization", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="outgoing_personnel_import_batches", to="organizations.organization", verbose_name="Организация-источник")),
                ("target_organization", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="personnel_import_batches", to="organizations.organization", verbose_name="Организация-держатель справочника")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="uploaded_personnel_import_batches", to=settings.AUTH_USER_MODEL, verbose_name="Загрузил")),
            ],
            options={
                "verbose_name": "пакет импорта персонала",
                "verbose_name_plural": "пакеты импорта персонала",
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="PersonnelChangeRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("public_id", models.UUIDField(default=uuid.uuid4, editable=False, unique=True, verbose_name="Публичный идентификатор")),
                ("action", models.CharField(choices=[("CREATE", "Создание карточки"), ("UPDATE", "Изменение карточки"), ("DEACTIVATE", "Деактивация карточки"), ("QUALIFICATION", "Изменение квалификации"), ("RIGHT", "Изменение права"), ("IMPORT_PREVIEW", "Предварительный просмотр импорта"), ("IMPORT_PUBLISH", "Публикация импорта")], max_length=24, verbose_name="Действие")),
                ("reason", models.CharField(max_length=1000, verbose_name="Основание изменения")),
                ("before_snapshot", models.JSONField(default=dict, verbose_name="Состояние до изменения")),
                ("after_snapshot", models.JSONField(default=dict, verbose_name="Состояние после изменения")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Зафиксировано")),
                ("batch", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="change_records", to="organizations.personnelimportbatch", verbose_name="Пакет импорта")),
                ("changed_by", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="personnel_change_records", to=settings.AUTH_USER_MODEL, verbose_name="Изменил")),
                ("employee", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name="change_records", to="organizations.employee", verbose_name="Сотрудник")),
            ],
            options={
                "verbose_name": "запись изменения персонала",
                "verbose_name_plural": "записи изменений персонала",
                "ordering": ("-created_at", "-id"),
            },
        ),
        migrations.AddConstraint(
            model_name="employeespecialqualification",
            constraint=models.CheckConstraint(condition=models.Q(("valid_until__isnull", True), ("valid_until__gte", models.F("valid_from")), _connector="OR"), name="employee_special_qualification_valid_window"),
        ),
        migrations.AddConstraint(
            model_name="employeespecialqualification",
            constraint=models.UniqueConstraint(fields=("employee", "kind", "level", "valid_from", "basis_reference"), name="uniq_employee_special_qualification_start_basis"),
        ),
        migrations.AddConstraint(
            model_name="externaloperationalcontact",
            constraint=models.CheckConstraint(condition=models.Q(("valid_until__isnull", True), ("valid_until__gte", models.F("valid_from")), _connector="OR"), name="external_operational_contact_valid_window"),
        ),
        migrations.AddConstraint(
            model_name="externaloperationalcontact",
            constraint=models.UniqueConstraint(fields=("employee", "host_organization", "relation_kind", "valid_from"), name="uniq_external_operational_contact_start"),
        ),
    ]
